---
phase: 24-opcoes-mcp-analise-e-setups
plan: 15
subsystem: api
tags: [fastapi, react, opcoes, mcp, cota, admin, rbac, auditoria, adr-013, adr-027]

requires:
  - phase: 24-opcoes-mcp-analise-e-setups (plano 01)
    provides: "`_cap_check`, as seções `mcpUsage*` e os três tetos como env (`B3_MCP_COTA_USUARIO_DIA`, `B3_MCP_RATE_MIN`, `B3_MCP_COTA_GLOBAL_DIA`)"
  - phase: ADR-008 / ADR-013
    provides: "`brapi_budget.spot_intervalo_s`/`set_spot_intervalo` (o padrão memória→kv→default) e `POST /api/obs/brapi/projecao` (prévia + `audit.record` + `fontes_dados.configurar`)"
provides:
  - "`cota_usuario_dia`/`rate_min`/`cota_global_dia` + `set_*` — precedência memória → kv → env → default"
  - "`limites()` com a ORIGEM de cada teto (`kv`/`env`/`default`), a env que o declara e `tetoServicoDia`"
  - "`consumo_global_hoje()` — o balde `mcpUsageGlobal` no dia de São Paulo"
  - "`reset_limites_cache()`, chamado por `configure()` e pelos testes"
  - "`GET`/`POST /api/obs/opcoes/cota` — prévia, aplicação tudo-ou-nada e um `audit.record` por campo alterado"
  - "`ENTIDADE_COTA = \"mcp_cota\"` em `rbac.ENTIDADES_POR_PERMISSAO[\"fontes_dados.configurar\"]`"
  - "card `CotaOpcoes` dentro da aba Fontes de dados do portal admin"
  - "`web/tests/test_admin_cota_opcoes.mjs` — guardião estático do card (26 asserções, 3 de sanidade)"
affects: [qualquer plano futuro que mexa no cap da aba Opções ou acrescente teto configurável; a publicação do portal (scripts/publicar-admin.sh) e o deploy do backend, os dois FORA deste plano]

tech-stack:
  added: []
  patterns:
    - "precedência em camadas com ORIGEM publicada: o número sozinho não diz se veio do painel ou do Railway, e sem isso as duas verdades convivem sem ninguém saber qual manda"
    - "cache em memória só da camada que muda por ação administrativa (kv); a camada que muda por fora do processo (env) segue lida a cada leitura"
    - "validação tudo-ou-nada ANTES de aplicar: validar enquanto aplica deixa metade da mudança de pé e o admin sem saber qual metade"
    - "aceitar com aviso em vez de recusar, quando o limite real é de terceiro: recusar fingiria controle que não se tem; calar deixaria o admin achar que subiu um teto que não subiu"

key-files:
  created:
    - web/tests/test_admin_cota_opcoes.mjs
  modified:
    - server/app/options_mcp_api.py
    - server/app/main.py
    - server/app/rbac.py
    - server/tests/test_mcp_cap.py
    - web-admin/src/App.jsx
    - web-admin/src/api.js

key-decisions:
  - "A env continua sendo camada, e continua lida A CADA leitura. O kv entra NA FRENTE dela, não no lugar dela: é como o Railway troca um teto sem publicar código e é o que `monkeypatch.setenv` exercita em 39 testes de cap. Cachear a env teria matado as duas coisas em silêncio"
  - "O cache em memória é só do valor vindo do kv. O custo de não cachear a ausência é um SELECT por chave primária no SQLite por leitura — a mesma classe do que o `metering` já faz várias vezes na mesma requisição"
  - "Valor acima de 2.000/dia é ACEITO com `aviso`. `rateMin` fica FORA da comparação: é por minuto, e compará-lo com um teto diário seria erro de unidade travestido de aviso"
  - "Sem permissão nova: `fontes_dados.configurar`, a mesma do orçamento brapi. É teto de consumo de fonte de dados externa, não governança de IA, e uma permissão nova exigiria mexer nos grupos do ADR-013 e nos testes de bootstrap sem ganho de granularidade real"
  - "A rota mora em `main.py`, fora do prefixo `/api/options/mcp`. Sob o prefixo ela precisaria passar por `_cap_check` (guardião IV do `test_mcp_guardioes`) — ajustar um teto não pode gastar o teto"
  - "O mínimo de 1 é imposto no CÓDIGO (`max(1, int(n))` no setter) ALÉM do 400 da rota. Um zero não é limite baixo, é o freio desligado; e a camada que menos se pode obrigar a lembrar é a de cima"
  - "`consumo_global_hoje()` mora em `options_mcp_api.py`, não na rota: a seção `mcpUsageGlobal` e a noção de dia (São Paulo) são do módulo. Lidas de fora, o painel mostraria um número que diverge do que o cap de fato conta"
  - "Auditoria por CAMPO alterado, nunca agregada — a pergunta que o audit log responde é 'quem mudou o quê', e um registro agregado não responde"

patterns-established:
  - "Guardião estático de card do portal admin com recorte por bloco + sanidade das regexes (o `.mjs` do web-admin lido por readFileSync, precedente do `test_fase5_auditoria_perm.mjs`)"

requirements-completed: ["pedido do Alex 2026-09-11 — configurar o limite da cota de opções"]

duration: ~55min
completed: 2026-09-12
---

# Fase 24 Plano 15: os três tetos da aba Opções saem do Railway e entram no painel — Summary

**Os limites que protegem um teto de 2.000 chamadas/dia compartilhado por toda
a base do Boris só existiam como env do Railway, e mexer neles exigia
redeploy. Agora eles são configuráveis pelo portal admin — com a origem de
cada número à vista, o consumo real do dia ao lado, prévia antes de gravar,
auditoria por campo e a ressalva de que o teto que de fato manda não é do
Boris.**

## Performance

- **Duration:** ~55 min
- **Completed:** 2026-09-12 00:35 (-03), somando a suíte canônica
- **Tasks:** 3
- **Files modified:** 6 (5 alterados + 1 criado)

## Por que isto existia como problema

O ADR-027 fechou com três tetos, todos como env:

```
B3_MCP_COTA_USUARIO_DIA = 60     # chamadas de UMA conta por dia
B3_MCP_RATE_MIN         = 20     # chamadas por minuto de uma conta
B3_MCP_COTA_GLOBAL_DIA  = 1800   # teto do Boris inteiro no dia
```

O que eles freiam é o contrato do serviço: **2.000 `tools/call` por dia para
TODA a base somada**. A Fase 24 acabou de multiplicar o consumo por sessão —
`/possibilidades` custa até 13 chamadas —, então o momento em que esse número
vai precisar de ajuste é justamente aquele em que o `/observabilidade` mostrar
o consumo real. Ajuste medido em redeploy chega tarde.

## O que foi feito

### A precedência, e por que a env não saiu

`memória → kv → env → default`, no padrão de
`brapi_budget.spot_intervalo_s`/`set_spot_intervalo` — incluindo o
`try/except` que engole falha de kv (banco indisponível degrada para a camada
de baixo, nunca derruba a rota).

A env **continua sendo camada** e continua lida a cada leitura. Não é
compatibilidade cerimonial: é como o Railway troca um teto sem publicar
código, e é o que `monkeypatch.setenv` exercita nos testes de cap que já
existiam. O cache em memória é, por isso, **só do valor vindo do kv** — que é
a única camada que muda por ação administrativa explícita, dentro do mesmo
processo que lê, e que o `set_*` invalida na hora.

Lixo em qualquer camada cai para a seguinte. Isso não é permissividade: um `0`
no banco não seria "limite baixo", seria o freio desligado.

As três privadas que o `_cap_check` usa (`_cota_usuario`, `_rate_min`,
`_cota_global`) passaram a delegar nas públicas. Um lugar só decide o valor
vigente — e é o lugar por onde o cap de verdade passa.

### A origem, que é metade da entrega

`limites()` devolve, por teto, `{valor, origem, env, default}`, com `origem`
em `"kv"`, `"env"` ou `"default"`. Sem ela o admin muda pelo painel, a env do
Railway continua dizendo outra coisa, e as duas verdades convivem sem ninguém
saber qual manda. No card ela aparece traduzida — *painel*, *variável de
ambiente*, *padrão* —, porque `kv` é vocabulário de backend.

### A rota, com prévia e auditoria

`GET /api/obs/opcoes/cota` devolve os três com origem **e o consumo global de
hoje**, lido do mesmo balde que o cap conta (`mcpUsageGlobal`, dia de São
Paulo). Decidir um teto sem ver o consumo é decidir no escuro.

`POST` sem `aplicar: true` é prévia: valida, diz o que mudaria, não escreve.
Com `aplicar: true`, valida **tudo antes de aplicar qualquer coisa** e grava
um `audit.record(entidade "mcp_cota")` por campo cuja valor mudou. Campo
ausente do corpo não é tocado.

Permissão `fontes_dados.configurar` — a mesma do orçamento brapi, porque é a
mesma classe de decisão. `"mcp_cota"` entrou em
`rbac.ENTIDADES_POR_PERMISSAO`, senão o evento existiria e cairia fora de todo
filtro do audit log, inclusive o de quem o produziu.

### O aviso, em vez da recusa

Valor acima de 2.000/dia é **aceito**, com `aviso` no corpo:

> Acima do teto do serviço: o contrato do MCP é de 2.000 chamadas/dia para
> TODA a base do Boris somada, e quem o controla é o serviço, não o Boris. Um
> limite acima disso não aumenta o que o serviço entrega — só faz o freio do
> Boris parar de agir antes dele, e a recusa passa a vir do próprio serviço.

Recusar fingiria que o Boris manda no teto do serviço; calar deixaria o admin
achar que subiu um teto que não subiu. `rateMin` fica fora da comparação: é
por minuto, e confrontá-lo com um teto diário seria erro de unidade vestido de
aviso.

### O card

`CotaOpcoes` renderiza **dentro** da aba "Fontes de dados" — mesma família
(teto de consumo de fonte externa), nenhuma aba nova, `VIEWS` intacto. Mostra
os três com origem, o consumo de hoje (`usado / teto`), três campos numéricos,
"Simular (não grava)" e "Aplicar (auditado)". Campo vazio significa "não
mexer": mandar o valor vigente de volta fixaria a origem no painel sem ninguém
ter pedido.

A frase que faz a decisão fazer sentido está no card, acima dos campos: *o
teto de 2.000 chamadas/dia é do serviço e é compartilhado por toda a base do
Boris; estes três limites são o freio do Boris dentro dele*. Sem ela, um admin
sobe a cota por usuário achando que aumentou o total disponível.

## Prova RED → GREEN

Os testes foram escritos **antes** de cada correção, nos arquivos canônicos, e
rodados contra o código de antes.

| Task | Teste escrito primeiro | RED observado (código de antes) | GREEN |
|---|---|---|---|
| 1 — os três limites | 11 testes em `test_mcp_cap.py` | `11 failed, 28 deselected` — `AttributeError: module 'app.options_mcp_api' has no attribute 'cota_usuario_dia' / 'set_cota_usuario_dia' / 'limites' / 'consumo_global_hoje' / 'reset_limites_cache' / 'TETO_SERVICO_DIA'` | `39 passed` no arquivo |
| 2 — rota admin | 10 testes em `test_mcp_cap.py` | `10 failed, 39 deselected` — `404 {"code":"rota_inexistente","message":"Este servidor não tem a rota /api/obs/opcoes/…"}` e a entidade fora de `ENTIDADES_POR_PERMISSAO` | `303 passed` com os irmãos do ADR-013 |
| 3 — o card | `web/tests/test_admin_cota_opcoes.mjs` (26 asserções) | `19 falha(s)` — nenhuma das três chamadas em `api.js`, nenhum `CotaOpcoes` em `App.jsx` | `todos os testes passaram` |

As 7 asserções que já passavam no RED da Task 3 são as que **não descrevem a
correção**: as de sanidade (têm de passar nos dois estados — é o que sanidade
significa) e as de não-regressão do array `VIEWS`, que este plano não podia
quebrar e não quebrou.

## Task Commits

1. **Task 1 — os três limites com precedência memória → kv → env → default** — `027d427` (feat)
2. **Task 2 — rota admin com prévia e auditoria por campo** — `5e08b1d` (feat)
3. **Task 3 — o card no portal admin** — `0d9c727` (feat)

## Files Created/Modified

- `server/app/options_mcp_api.py` — os três pares leitura/escrita,
  `_env_int`/`_kv_int`/`_valor_e_origem`/`_set_limite`, `limites()`,
  `consumo_global_hoje()`, `reset_limites_cache()`, `TETO_SERVICO_DIA`,
  `ENTIDADE_COTA`, `LIMITES`/`LIMITES_POR_DIA`; `db` no import; a chamada de
  invalidação em `configure()`; as três privadas do cap delegando
- `server/app/main.py` — `GET`/`POST /api/obs/opcoes/cota`,
  `_cota_opcoes_pedidos` (validação tudo-ou-nada), `_CAMPOS_COTA_OPCOES` e o
  texto do aviso. **`SERVER_BUILD_ID` não foi tocado**
- `server/app/rbac.py` — `"mcp_cota"` em
  `ENTIDADES_POR_PERMISSAO["fontes_dados.configurar"]`, com a nota de por que
  entrou
- `server/tests/test_mcp_cap.py` — 21 testes novos (11 da Task 1, 10 da Task 2)
- `web-admin/src/api.js` — `opcoesCotaGet`/`opcoesCotaPrevia`/`opcoesCotaAplicar`
- `web-admin/src/App.jsx` — `CotaOpcoes`, `ORIGEM_ROTULO`, `CAMPOS_COTA`;
  `FontesDeDados` passou a devolver os dois cards
- `web/tests/test_admin_cota_opcoes.mjs` — **criado** (guardião estático do
  card, 26 asserções)

## Deviations from Plan

### 1. [Rule 2 — verificação que não verificava] guardião `.mjs` do card criado

- **Found during:** Task 3
- **Issue:** a única verificação prevista para a Task 3 era `npx vite build`,
  que prova que o JSX compila e **nada** sobre os critérios de aceite reais
  (origem à vista, consumo de hoje, prévia separada do aplicar, a frase do
  teto compartilhado, o gate de permissão). Sem guardião, a próxima edição do
  card apaga qualquer um deles com o build verde — e o `web-admin/` não tem
  suíte própria.
- **Fix:** `web/tests/test_admin_cota_opcoes.mjs`, no precedente exato do
  `test_fase5_auditoria_perm.mjs` (lê o fonte do `web-admin/` por
  `readFileSync`, roda sem build). Inclui 3 asserções de sanidade das próprias
  regexes e a não-regressão do array `VIEWS`.
- **Files modified:** `web/tests/test_admin_cota_opcoes.mjs` (novo)
- **Commit:** `0d9c727`

### 2. [Rule 3 — vazamento entre testes] `reset_limites_cache()` em `configure()`

- **Found during:** Task 1
- **Issue:** o cache de processo do valor vindo do kv é exatamente o que faz
  um `set_*` de um teste valer como teto do teste seguinte — que roda contra
  OUTRO banco temporário. Isso não é fragilidade de suíte: é o mesmo cache que
  em produção precisa ser invalidado quando o processo passa a falar com outro
  banco.
- **Fix:** `configure()` chama `reset_limites_cache()`. É o ponto em que
  `main.py` entrega a conexão ao módulo, e a suíte re-importa `app.main` a
  cada cliente novo — a invalidação passou a ser automática, sem obrigar cada
  arquivo de teste a lembrar.
- **Files modified:** `server/app/options_mcp_api.py`
- **Commit:** `027d427`

### 3. [Rule 3 — a origem exigia distinguir env válida de default] `_int_env` refatorado

- **Found during:** Task 1
- **Issue:** `_int_env(nome, padrao)` devolvia `padrao` tanto para "env
  ausente" quanto para "env torta" quanto para "env igual ao default". A
  origem publicada precisa distinguir os três.
- **Fix:** `_env_int(nome) -> Optional[int]` decide (texto, vazio, 0 e
  negativo → `None`), e `_int_env` passou a delegar nela. Comportamento
  preservado byte a byte — `test_env_torta_nao_derruba_a_rota_e_cai_no_default`,
  que já existia, continua verde sem uma linha alterada.
- **Files modified:** `server/app/options_mcp_api.py`
- **Commit:** `027d427`

### 4. [colocação] `consumo_global_hoje()` ficou na Task 1, não na Task 2

- **Found during:** Task 2
- **Issue:** o PLAN pede o consumo no corpo do `GET` (Task 2, `main.py`), mas
  a seção (`mcpUsageGlobal`) e a noção de dia (São Paulo) são de
  `options_mcp_api.py`. Montar o snapshot na rota faria o painel mostrar um
  número que pode divergir do que o cap de fato conta.
- **Fix:** o helper mora no módulo dono do cap e a rota só o chama. Há teste
  provando que o número é o do balde da aba e **não** vazou para o balde da IA
  gerenciada.
- **Files modified:** `server/app/options_mcp_api.py`
- **Commit:** `027d427`

### 5. [não-desvio registrado] `test_adr013_cobertura_rotas.py` NÃO foi tocado

- **Found during:** Task 2
- **Issue:** o arquivo estava em `files_modified` do PLAN.
- **Fix:** nada a mudar — as duas rotas novas são gated por
  `require_permission`, então o guardião de cobertura passa e a allowlist
  pública continua com 25 entradas. Em vez de mexer no guardião, o fato ganhou
  um teste local
  (`test_as_duas_rotas_de_cota_sao_gated_e_nao_entram_na_allowlist_publica`),
  que importa a própria allowlist e afirma que as duas rotas estão fora dela.
- **Files modified:** — (nenhum)
- **Commit:** `5e08b1d`

### 6. [processo — honestidade sobre o RED] dois testes meus tinham defeito próprio

- **Found during:** Tasks 1 e 2
- **Issue:** três asserções falharam no GREEN por erro **do teste**, não do
  código: o espião do `/status` recebia um `dict` cru em vez de
  `mcp_client.ResultadoTool` (dois testes), e o audit log foi lido com
  `oldValue`/`newValue` como string e `actorId` em vez de `actorUserId`. Os
  três já estavam em RED por `AttributeError`/404 antes da correção — o RED é
  legítimo —, mas o defeito só apareceu depois.
- **Fix:** corrigidos os testes (o shape do espião e as chaves reais de
  `db._audit_row_to_dict`); nenhuma linha de produção mudou por causa disso.
- **Files modified:** `server/tests/test_mcp_cap.py`
- **Commit:** `027d427`, `5e08b1d`

## Verificação

```
bash scripts/executar.sh --testes    # exit 0
2532 passed, 5 skipped, 699 warnings in 55.88s
130 arquivos web/tests/*.mjs [OK], 0 [X]
```

Baseline a não regredir: `2511 passed, 5 skipped` + 129 `.mjs`. O delta de
`+21` é exatamente os testes deste plano (11 da Task 1 + 10 da Task 2); o
`+1 .mjs` é o guardião novo do card.

```
cd web-admin && npx vite build     # ✓ built in 855ms
```

Guardiões rodados isolados:
`tests/test_mcp_cap.py tests/test_adr013_cobertura_rotas.py
tests/test_adr013_rbac.py tests/test_mcp_guardioes.py tests/test_opcoes_dsl.py
tests/test_options_mcp_api.py` → `303 passed`.

`web/` não foi tocado, então `web/dist` não foi regerado e o incidente de
paridade do bundle iOS que o 24-14 registrou não se repetiu.

## Limitações conhecidas

- **Nada disto está no ar.** O backend só vale depois de um deploy e o card só
  depois de `scripts/publicar-admin.sh` — os dois fora do escopo desta
  execução, já combinados com o Alex como etapa posterior. Nenhum push, nenhum
  PR, nenhum bump.
- **Sem verificação ao vivo.** O card não foi visto numa tela real; o que
  existe é o build verde, o guardião de fonte e as rotas exercitadas pelo
  caminho HTTP completo em `TestClient`.
- **Aplicar um valor IGUAL ao vigente fixa a origem no painel sem gerar evento
  de auditoria.** O registro é por mudança de VALOR (o que o PLAN pede, e o
  que a pergunta "quem mudou o quê" significa). O efeito colateral — a env
  deixar de mandar naquele teto — fica visível em `limites()`/no card, mas não
  no audit log. Contornável pelo admin: o campo vazio significa "não mexer".
- **Mudar o teto não devolve cota já gasta.** Baixar `cotaGlobalDia` abaixo do
  consumo do dia recusa todo mundo até a virada em São Paulo; subir libera na
  hora. É o comportamento do `metering` e não foi alterado.
- **O aviso de 2.000 é textual, não um freio.** O Boris não sabe quanto a base
  inteira já consumiu no serviço — só o que ELE contou. Se houver consumo do
  contrato por fora do Boris, o `consumoGlobalHoje` do card subestima.

## Self-Check: PASSED

- `server/app/options_mcp_api.py` — FOUND
- `server/app/main.py` — FOUND
- `server/app/rbac.py` — FOUND
- `server/tests/test_mcp_cap.py` — FOUND
- `web-admin/src/App.jsx` — FOUND
- `web-admin/src/api.js` — FOUND
- `web/tests/test_admin_cota_opcoes.mjs` — FOUND
- `.planning/phases/24-opcoes-mcp-analise-e-setups/24-15-SUMMARY.md` — FOUND
- Commits `027d427`, `5e08b1d`, `0d9c727` — FOUND em `git log`
