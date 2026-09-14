---
phase: quick-260914-b6p
plan: 01
subsystem: server/app (provider de opções mydata)
tags: [bugfix, opcoes, mydata, curadoria, fase-14, fase-30]
dependency-graph:
  requires: []
  provides:
    - "options_provider_mydata.get_options escolhe vencimento por data futura, não por vence_no_pregao"
  affects:
    - "opcoes_lastreadas.py / opcoes_curadoria.py (consomem o expiration escolhido; dias negativos eliminados)"
    - "Fase 14 (venda coberta) e Fase 30 (curadoria de 4 melhores)"
tech-stack:
  added: []
  patterns:
    - "hoje injetável por argumento + default hoje_brt() (mesmo padrão de opcoes_lastreadas.py e options_provider_mock.py)"
key-files:
  created: []
  modified:
    - server/app/options_provider_mydata.py
    - server/tests/test_options_provider_mydata.py
    - server/tests/test_options_provider.py
decisions:
  - "D-01 a D-05 do plano aplicadas como especificado (hoje injetável, campo vence_no_pregao fora da decisão, expiration explícito honrado mesmo vencido, degradação antes da segunda perna de rede, sorted() defensivo)"
metrics:
  duration: "~35min"
  completed: "2026-09-14"
---

# Phase quick-260914-b6p Plan 01: Corrigir seleção de vencimento no provider mydata Summary

Seleção de vencimento em `options_provider_mydata.get_options` deixou de depender do campo `vence_no_pregao` (sempre `0`/falsy em produção: BBAS3 27/27, PETR4 31/31) e passou a comparar `dt.date` contra `hoje`, escolhendo o primeiro vencimento estritamente futuro — elimina os dias negativos que zeravam a Fase 14 e a Fase 30.

## O que foi feito

**Task 1 — `server/app/options_provider_mydata.py` (commit `05e6ffa`)**
- `import datetime as dt`; `BRT`/`hoje_brt()` no módulo, mesmo padrão de `options_provider_mock.py:31-42` (offset fixo -3h, não `date.today()` — container Railway roda em UTC).
- Nova constante `MYDATA_SEM_VENCIMENTO_FUTURO_WARNING` (PT-BR, sem interpolar data).
- `get_options(ticker, expiration=None, hoje=None)`: `hoje_efetivo = hoje or hoje_brt()` resolvido ANTES do lookup de cache.
- Chave de cache do ramo sem `expiration` passou a carregar o dia (`f"{t}:first@{hoje_efetivo.isoformat()}"`), para um payload cacheado às 23:58 BRT não sobreviver à virada do dia.
- Novo helper `_primeiro_vencimento_futuro(venc, hoje)`: `dt.date.fromisoformat` com `try/except (TypeError, ValueError)` por item (item malformado ignorado, nunca levanta), candidatos filtrados por `d > hoje` (futuro ESTRITO), `sorted()` defensivo (D-05), devolve o primeiro ou `None`.
- Sem vencimento futuro → `_empty_payload` com o warning novo, cacheado com TTL de erro (60s), retornando ANTES do segundo `_debita()`/`get_options_chain` (D-04 — cota não gasta à toa).
- `expiration` explícito continua honrado mesmo vencido (D-03) — nenhuma linha do ramo `if expiration:` mudou.
- Docstring do módulo ganhou um parágrafo de decisão citando a medição de produção e D-01..D-05.
- `grep -n "vence_no_pregao" server/app/options_provider_mydata.py` → vazio (o campo permanece no payload cru/`_clean_contract` sob a mesma chave; só saiu da PROSA e da decisão — as referências em comentário usam "flag de vencimento-no-pregão" para não colidir com o grep de verificação do plano).

**Task 2 — testes (commit `f079bfd`)**
- `test_options_provider_mydata.py`: `_HOJE = dt.date(2026, 9, 14)` (data real da medição) + `_cache_limpo` agora recebe `monkeypatch` e faz `monkeypatch.setattr(provider, "hoje_brt", lambda: _HOJE)` — nenhuma das ~30 chamadas pré-existentes de `get_options` precisou mudar.
- 8 novos testes de regressão com a amostra BBAS3 real (todo item `vence_no_pregao: 0`, primeiro no passado): escolhe o futuro e não o vencido; propriedade dura (`dt.date.fromisoformat(expiration) > _HOJE`); lista fora de ordem; vencimento igual a hoje não conta (futuro estrito); flag ligado num vencimento futuro não impede a escolha (D-02); item com `dt_vencimento` `None`/`"31/12/2026"` ignorado sem levantar; `expiration` explícito vencido continua honrado com chain chamada com a data vencida (D-03); cache não reusa entre `hoje` diferentes (duas idas ao cliente).
- Guardiões antigos ATUALIZADOS, não apagados:
  - `test_sem_expiration_escolhe_primeiro_vencimento_que_nao_vence_no_pregao` → renomeado para `test_sem_expiration_escolhe_o_primeiro_vencimento_futuro`; assertion segue `2026-09-19`, motivo trocado (era passado por causa do `vence_no_pregao`, agora é passado por causa da data).
  - `test_todos_vencem_no_pregao_escolhe_o_primeiro_da_lista` → reescrito como `test_todos_vencidos_degrada_sem_chamar_a_cadeia`, com nota explícita de REVERSÃO DELIBERADA (protegia o comportamento agora errado de servir vencido; motivo da queda é a medição de produção; o que protege agora é a degradação + espião provando que `get_options_chain` nunca é chamado).
- `test_options_provider.py`: `test_payload_ok_mydata_contem_todas_as_chaves_de_topo_do_payload_ok_yahoo` ganhou `monkeypatch.setattr(options_provider_mydata, "hoje_brt", lambda: dt.date(2026, 9, 14))` — dependia de `2026-09-19` continuar futuro por acidente de calendário.
  - Nota: o plano citava "os dois fakes de `get_vencimentos` (linhas ~99 e ~151)" como dependentes de `2026-09-19`; na leitura do arquivo real só o de ~linha 99 (`test_payload_ok_mydata...`) usa essa data — o outro (`test_selector_mydata_sem_cota_degrada`) devolve `[]` e degrada antes de qualquer comparação de data, então não precisava de patch. Deixado como estava, sem mudança sem necessidade.

## Prova do bug morto (mesma forma da seção `<verification>` do plano)

```
$ .venv/bin/python -c "import datetime as dt; from app import options_provider_mydata as p; \
  print(p._primeiro_vencimento_futuro([{'dt_vencimento':'2026-09-11','vence_no_pregao':0}, \
  {'dt_vencimento':'2026-09-18','vence_no_pregao':0}], dt.date(2026,9,14)))"
2026-09-18
```

## Suíte canônica

`bash scripts/executar.sh --testes` (fora do sandbox), exit 0:
`2864 passed, 5 skipped, 3 xfailed` (pytest) + `147` `.mjs` OK — contagem acima da baseline (2856 passed): +8 testes novos de regressão, líquido (os 2 guardiões atualizados trocaram de nome/corpo sem alterar a contagem).

Falha isolada e pré-existente vista durante um `pytest -k options` exploratório dentro do sandbox padrão (`test_options_provider_yahoo.py::test_options_provider_degrades_instead_of_raising_on_yahoo_401`, `[Errno 1] Operation not permitted` em vez de `401`) — é o falso-negativo de rede do sandbox documentado no CLAUDE.md do repo, não relacionado a este módulo; some fora do sandbox (confirmado: a suíte canônica completa, rodada com `dangerouslyDisableSandbox`, ficou 100% verde).

## Deviations from Plan

Nenhuma que mude comportamento. Três ajustes textuais/documentais:

1. **Grep-compliance, decisão explícita:** referências a `vence_no_pregao` em comentários/docstring de `options_provider_mydata.py` foram reescritas como "flag de vencimento-no-pregão" (sem underscore) para satisfazer literalmente o critério de verificação do plano (`grep -n "vence_no_pregao" server/app/options_provider_mydata.py` → vazio, item 4 de `<verification>`). Isso significa que quem grepar SÓ este arquivo por `vence_no_pregao` não encontra a explicação da remoção — julgamento deliberado, não descuido: o nome literal do campo permanece grepável no repo, e bem próximo do módulo, em `server/tests/test_options_provider_mydata.py` (fixtures `_vencimentos_ok`, `_venc_bbas3_real`, os dois guardiões atualizados — inclusive a nota de reversão que narra por que o campo saiu da decisão), em `server/tests/test_options_provider.py`, `server/tests/test_mydata_client.py` e `server/tests/test_opcoes_fronteira.py`. Verificado com `grep -rn "vence_no_pregao" server/app/ server/tests/` antes de fechar esta entrega — a explicação da decisão sobrevive no lugar que o repo trata como fonte de comportamento (os testes), só não dentro do módulo de produção em si.
2. Item (d) da Task 2 citava dois fakes de `get_vencimentos` dependentes de `2026-09-19`; só um existe de fato no arquivo (o outro devolve lista vazia e não depende de data) — documentado acima, nenhuma mudança de comportamento.
3. **"Todos vencidos → degrada" não ganhou teste dedicado separado em 2(b):** essa propriedade, listada como um dos 8 novos testes de regressão do item 2(b), é coberta pelo guardião reescrito em 2(c) (`test_todos_vencidos_degrada_sem_chamar_a_cadeia`, que já inclui o espião provando que `get_options_chain` nunca é chamado). Escrever uma segunda cópia quase idêntica seria redundante — a contagem líquida de "8 novos testes" no corpo deste SUMMARY já reflete essa fusão (não são 9 testes distintos porque este é coberto pela atualização do guardião, não duplicado).

## Achado para o Alex (reportado, NÃO implementado — decisão de produto)

Esta correção mata os dias NEGATIVOS, mas por si só NÃO garante que a Fase 14 / Fase 30 voltem a produzir proposta. O provider escolhe o primeiro vencimento FUTURO; `opcoes_lastreadas`/`opcoes_curadoria` exigem `_PRAZO_MIN_DIAS(15) <= dias <= _PRAZO_MAX_DIAS(60)`. Na amostra BBAS3 medida, o primeiro futuro é `2026-09-18` — 4 dias a partir de `2026-09-14`, ABAIXO do piso de 15. Como os vencimentos da B3 são mensais, "dias até o primeiro futuro" percorre ~0..30 todo mês: por volta de metade do mês a cadeia default cai abaixo do piso e a proposta segue vazia — agora por um motivo legítimo (prazo curto), não por bug.

Pergunta em aberto (fora do escopo pedido): o provider deveria preferir o primeiro vencimento DENTRO da janela 15..60 em vez do primeiro futuro? Mudaria a cadeia default para TODOS os consumidores (inclusive o vencimento pré-selecionado na UI de opções) — decisão de produto. Alternativa menos invasiva: o motor de propostas pedir explicitamente o vencimento da janela via `get_options(t, expiration=...)` (já existe e é honrado, D-03), usando a lista `expirations` que o payload já devolve.

**Decisão do Alex (2026-09-14, depois de ver o impacto medido em 16 tickers líquidos — todos caem no mesmo vencimento 18/09, 4 dias, abaixo do piso): manter "o primeiro futuro, seja qual for".** Não mudar para pular pro primeiro dentro da janela 15-60. Consequência aceita conscientemente: a proposta de venda coberta e a curadoria (Fase 30) ficam vazias para o mercado inteiro sempre que o vencimento mais próximo cair abaixo de 15 dias — o que acontece por boa parte de cada ciclo mensal (nesta medição, só volta a produzir por volta de meados de outubro, quando `2026-10-16` entrar na janela). **Fechado — não re-litigar sem novo pedido explícito do Alex.**

## Deploy

**Publicado em produção**: `F10-20260914-02` (deploy só-backend, `server/app/main.py:1662`), confirmado ao vivo via `railway run` contra o mydata real — BBAS3/PETR4 agora resolvem `expiration: 2026-09-18` (futuro), não mais `2026-09-11` (vencido). Suíte canônica verde antes do push (2864 passed, 147 .mjs, exit 0). Commit `70ffa53`.

## Self-Check: PASSED

- `server/app/options_provider_mydata.py`: FOUND
- `server/tests/test_options_provider_mydata.py`: FOUND
- `server/tests/test_options_provider.py`: FOUND
- commit `05e6ffa`: FOUND (`git log --oneline --all | grep 05e6ffa`)
- commit `f079bfd`: FOUND (`git log --oneline --all | grep f079bfd`)
- `grep -n "vence_no_pregao" server/app/options_provider_mydata.py`: vazio, conforme esperado
- suíte canônica: exit 0, 2864 passed / 5 skipped / 3 xfailed + 147 `.mjs` OK
