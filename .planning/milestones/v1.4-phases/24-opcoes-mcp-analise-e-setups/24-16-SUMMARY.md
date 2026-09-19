---
phase: 24-opcoes-mcp-analise-e-setups
plan: 16
subsystem: api
tags: [fastapi, byok, plano-comercial, metering, gate, adr-010, adr-013, achado-ao-vivo]

requires:
  - phase: 03 (C-32)
    provides: "`_gate_analise` como ponto ÚNICO de decisão de gate por requisição, com precedência explícita PLANO → METERING"
  - phase: 05 (C-33)
    provides: "`metering.month_used` como fonte única da contagem mensal (o ledger é escrito só por `metering.consume`)"
  - phase: 12 (ADR-010, D-01)
    provides: "`PLAN_FREE.max_analyses_per_month = 30` — o limite que passou a barrar de verdade"
provides:
  - "precedência nova em `_gate_analise`: BYOK (`llm.resolve_key`) ANTES do gate mensal do plano"
  - "`server/tests/test_plan_gate_byok.py` — 10 casos travando os DOIS lados (destrava com chave própria, continua barrando sem)"
affects:
  - "as três rotas que chamam `_gate_analise`: `/api/analyze/{ticker}`, `/api/technical/analyze/{ticker}` e a compilação de setups da aba Opções (`options_mcp_api`, via a lambda de fiação)"
  - "nenhum outro plano — `plan.py`, `metering.py` e o contrato de `/api/ai/quota` ficaram intactos"

tech-stack:
  added: []
  patterns:
    - "precedência de gates é decisão do CHAMADOR, não do módulo de política: `plan.can_analyze` continua sem saber que BYOK existe, e é por isso que a assinatura dela não precisou mudar"
    - "uma única definição de 'tem chave' (`llm.resolve_key(config)`), reusada literalmente do ramo que já a usava — duas definições do mesmo conceito divergem na primeira manutenção"
    - "teste que passa nos DOIS estados do código prova ausência de regressão, não a correção; os dois papéis ficam nomeados por escrito no arquivo de teste"

key-files:
  created:
    - server/tests/test_plan_gate_byok.py
  modified:
    - server/app/main.py

key-decisions:
  - "A correção mudou QUANDO o gate mensal é consultado, nunca O QUE ele mede. Nenhum contador novo, nenhuma seção de kv nova, `plan.py` byte a byte igual — o achado era de precedência, e tratá-lo mexendo na contagem teria criado um segundo contador paralelo, exatamente o que o contrato C-32/C-33 proíbe"
  - "BYOK = `llm.resolve_key(config)` truthy, a MESMA expressão que `_ai_apply_managed` já usava na primeira linha. Não se inventou um `tem_chave()` novo: duas definições do mesmo conceito divergem na primeira manutenção, e uma delas seria a que decide dinheiro"
  - "O desvio para `_ai_apply_managed` no ramo BYOK é chamada direta, não early-return com `(config, lambda: None)` copiado. Copiar o retorno duplicaria o contrato do ramo BYOK em dois lugares; a chamada reusa a única implementação dele (verificado: com chave própria, `_ai_apply_managed` retorna na PRIMEIRA linha, sem tocar em `metering`)"
  - "O guardião do cap comercial (caso 2) foi escrito junto com a correção, não depois. Sem ele, a mudança de precedência é indistinguível de um furo no teto que protege a chave paga do servidor"

metrics:
  duration: ~25min
  completed: 2026-09-12
  tasks: 2
  commits: 2
  files-created: 1
  files-modified: 1
---

# Fase 24 Plano 16: BYOK destrava o gate mensal do plano — Summary

Chave própria de LLM passa na frente do cap mensal do plano em `_gate_analise`,
porque o contador desse cap mede exclusivamente o consumo da chave do servidor.

## O que mudou

`server/app/main.py::_gate_analise` ganhou um degrau acima dos dois gates que
já coexistiam ali:

```
antes:  PLANO (mensal)  →  METERING (diário, dentro de _ai_apply_managed)
depois: BYOK  →  PLANO (mensal)  →  METERING (diário)
```

O ramo novo é uma linha (`if llm.resolve_key(config): return
_ai_apply_managed(...)`) mais o registro do porquê no corpo da função e uma
nota datada na docstring, preservando o texto do C-32/C-33 que já estava lá.

## Por que (o achado)

Achado em 2026-09-12 a partir de um bloqueio real: a conta bateu as 30
análises/mês do `PLAN_FREE` e, ao configurar a própria chave, continuou
barrada.

A cadeia do defeito, com os três elos:

1. `_gate_analise` chamava `plan.can_analyze(metering.month_used(_conn, scope))`
   **antes** de qualquer verificação de chave própria;
2. `plan.can_analyze(used_this_month, plan=None)` não recebe nada sobre chave —
   por contrato, é hook comercial puro;
3. `metering.month_used` lê um ledger cujo **único ponto de escrita** é
   `metering.consume`, e `consume` só roda no ramo gerenciado de
   `_ai_apply_managed` (com BYOK esse ramo devolve `lambda: None`).

Resultado: quem trazia a própria chave era barrado por consumo de um recurso
que não ia usar, pagando do bolso pelo que não conseguia rodar. E o código já
prometia o contrário em dois lugares — o comentário `# BYOK utilizável → sem
cota` em `_ai_apply_managed` e o texto do 402, que fala de "análises do seu
plano" para alguém que não está usando a chave do plano.

Isto é a correção de uma promessa não cumprida, não uma mudança de política
comercial.

## Tasks

| Task | Nome | Commit | Arquivos |
| ---- | ---- | ------ | -------- |
| 1 | BYOK passa na frente do gate mensal | `dafad5c` | `server/app/main.py` |
| 2 | O teste que prova os dois lados | `71dd4f4` | `server/tests/test_plan_gate_byok.py` |

## RED: quais falharam contra o código anterior, quais não

O arquivo de teste foi escrito e rodado **contra o código de antes** da Task 1.
Saída medida: `4 failed, 6 passed`.

**Falharam no RED (provam a correção):**

| Caso | O que trava |
| ---- | ----------- |
| `test_1_byok_com_ledger_acima_do_limite_nao_e_barrado` | ledger em 100, plano free (limite 30), config com chave → não levanta 402; a config do usuário volta intacta e o `consume` é no-op |
| `test_1b_byok_nao_toca_o_gate_da_chave_do_servidor` | com a IA gerenciada habilitada por env, `metering.check` não é chamado nenhuma vez |
| `test_1c_rota_analyze_com_byok_e_ledger_estourado_nao_diz_quota` | o achado como o usuário o vive: `POST /api/analyze/PETR4` com a chave no corpo (caminho do iPhone) não volta `iaIndisponivel.code == "quota"` |
| `test_5_byok_nao_conta_e_nao_desconta_no_ledger_mensal` | `month_used` continua em 100 depois da passagem, inclusive chamando o `consume` devolvido |

Nota honesta sobre o `test_5`: o plano previa que ele passasse nos dois
estados. Não passa — e não podia. Ele só consegue medir o ledger **depois** de
atravessar o gate com chave própria, e na ordem antiga morria no 402 antes de
chegar ao `assert`. É um sub-asserto do caminho novo, não uma prova
independente de não-regressão. A docstring do arquivo registra isso, em vez de
repetir a expectativa do plano.

**Passaram nos dois estados (provam ausência de regressão, não a correção):**

| Caso | O que trava |
| ---- | ----------- |
| `test_2_sem_byok_com_ledger_acima_do_limite_continua_barrando` | **o guardião do cap comercial.** Sem chave, 402 com a mensagem exata de hoje (`Voce atingiu o limite de 30 analises/mes do plano free.`) |
| `test_2b_config_vazia_tambem_continua_barrando` | config `{}` (o default de quem nunca abriu a tela de IA) não pode ser lida como "tem chave" |
| `test_3_sem_byok_abaixo_do_limite_segue_para_o_gerenciado` | `metering.check` roda exatamente 1 vez e a config efetiva vira a do servidor (`keySource == "managed"`) |
| `test_4_pro_nunca_e_barrado[sem_byok]` / `[com_byok]` | conta `pro` (limite `None`) passa nos dois casos |
| `test_5b_escopo_anonimo_continua_degradando_para_o_plano_menos_privilegiado` | fail-closed (T-03-13/T-03-14): `scope=None` recebe `used == 0` e o plano é `plan.ACTIVE_PLAN`, nunca um superior — a ordem nova não criou atalho aqui |

O `test_2` importa tanto quanto o `test_1`: sem ele, a mudança de precedência
é indistinguível de um furo no teto que protege a chave paga do servidor.

## Guardrails respeitados

- **`plan.py` não foi tocado.** `git diff` do plano inteiro cobre dois
  arquivos; `can_analyze` mantém assinatura e corpo.
- **Nenhum contador novo.** `metering.py` intacto; `month_used` continua
  contando só o gerenciado.
- **As três rotas.** `_gate_analise` é chamado por `/api/analyze/{ticker}`,
  `/api/technical/analyze/{ticker}` e pela compilação de setups da aba Opções
  (via a lambda de fiação de `options_mcp_api.configure`). Nenhuma delas
  dependia da ordem antiga: as duas primeiras capturam o 402 e caem no
  fallback determinístico (FIX-C01), e a da aba Opções traduz o motivo por
  texto (`_MARCA_DO_GATE_MENSAL`), não por ordem de avaliação. Os guardiões
  estáticos pré-existentes continuam verdes: `plan.can_analyze(` aparece
  exatamente 1 vez no `main.py` e `_gate_analise(` aparece ≥ 3.
- **Nada publicado.** `server/web_dist`, `server/admin_dist`,
  `web/src/version.js` e a linha `SERVER_BUILD_ID` não foram tocados. Nenhum
  `git push`, nenhum PR, nenhum `bump.sh`/`publicar-*.sh`. Nenhum mutador de
  estado do `gsd-sdk` foi chamado.
- **Nenhum `git add -A`/`git add .`.** Cada commit teve o índice conferido com
  `git diff --cached --stat` antes: 1 arquivo em cada.

## Testes executados

Suíte canônica, **fora do sandbox** (dentro dele `ssl.load_verify_locations`
estoura `PermissionError` e a saída mente com ~26 falhas falsas):

```
$ bash scripts/executar.sh --testes
2542 passed, 5 skipped, 719 warnings in 56.80s
130 arquivos web/tests/*.mjs [OK]
```

Baseline: `2532 passed, 5 skipped` + 130 `.mjs`. Delta `+10` no pytest — são
exatamente os 10 casos novos deste plano. Nenhum `.mjs` a mais (o plano não
toca no front). **Sem regressão.**

Verificação da Task 1 (subconjunto do plano):

```
$ .venv/bin/python -m pytest tests/ -q -k "plan or gate or metering or quota or analyze"
166 passed, 2381 deselected
```

Front não foi editado, então `npx vite build` não se aplica.

## Limitações conhecidas

- **Não está no ar.** A mudança é de backend e exige deploy; até lá, a conta do
  Alex continua barrada em produção. Deploy só-backend pede bump manual de
  `SERVER_BUILD_ID` (guardrail do `CLAUDE.md`), fora do escopo deste plano.
- **Nenhuma verificação ao vivo.** O `test_1c` exercita a rota real via
  `TestClient` com a chamada de LLM stubada — prova a ausência da negação por
  cota, não que a análise com a chave do Alex responde. Isso só o aparelho
  dele diz.
- **`/api/ai/quota` não mudou.** A UI continua exibindo `monthUsed`/`monthLimit`
  do plano mesmo para quem tem BYOK, e para essa pessoa os dois números agora
  não decidem mais nada. O contrato foi deixado intacto de propósito (mexer
  nele é mudança de front, com publicação), mas a tela pode ficar dizendo
  "29/30" para quem está ilimitado — vale um item de backlog.

## Como validar localmente

```bash
cd /Users/acamerini/dev/borisv2
bash scripts/executar.sh --testes          # canônica (fora do sandbox)

# o caso do achado, isolado:
cd server && .venv/bin/python -m pytest tests/test_plan_gate_byok.py -q

# o RED, se quiser reproduzir:
git stash && git checkout dafad5c~1 -- server/app/main.py
.venv/bin/python -m pytest tests/test_plan_gate_byok.py -q   # 4 failed, 6 passed
git checkout HEAD -- server/app/main.py
```

## Deviations from Plan

Nenhum desvio de implementação. Uma correção de expectativa, documentada acima
e na docstring do arquivo de teste: o plano previa que os casos 2-5 passassem
nos dois estados do código, e o caso 5 não passa — por construção, ele depende
de atravessar o gate com BYOK, o que só o código novo permite. Registrado como
está, em vez de reescrito para caber na previsão.

## Threat Flags

Nenhuma superfície nova. A mudança relaxa um gate existente por um caminho
(BYOK) em que o recurso protegido — a chave paga do servidor — comprovadamente
não é consumido, e o guardião do caso 2 trava o caminho em que ele é.

## Self-Check: PASSED

- `server/tests/test_plan_gate_byok.py` — FOUND
- `server/app/main.py` (modificado, `llm.resolve_key` presente em `_gate_analise`) — FOUND
- commit `dafad5c` — FOUND
- commit `71dd4f4` — FOUND
