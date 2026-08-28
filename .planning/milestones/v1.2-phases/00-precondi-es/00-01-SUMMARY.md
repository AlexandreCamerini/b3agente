---
phase: 00-precondi-es
plan: 01
subsystem: data
tags: [yahoo-finance, ticker-resolution, ledger, adr-017, backtest, tdd]

requires: []
provides:
  - "server/app/ledger_tickers.py — mapa de resolução de ticker do universo (ALIASES/EXCLUIDOS/resolver()) para o bootstrap do ledger"
  - "retry escopado de HTTP 404 em signal_ledger_bootstrap.carregar_candles (2 tentativas, decisão A-03)"
  - "bucket resumo['excluidos'] em signal_ledger_bootstrap.executar(), sempre presente, nunca silencioso"
  - "docs/DIAGNOSTICO-tickers-ledger-2026-08-28.md — evidência datada do veredito de cada um dos 9 tickers"
affects: [10-ponte-gatilho-put]

tech-stack:
  added: []
  patterns:
    - "Mapa de resolução de ticker isolado do universo visível (A-01): correção de fonte de dado nunca vaza para scanner.DEFAULT_UNIVERSE"
    - "Retry de HTTP específico escopado a UM caminho manual/offline (bootstrap), nunca na escada de retry global do provedor (yahoo._yfetch)"

key-files:
  created:
    - scripts/diagnostico-tickers-ledger.py
    - server/app/ledger_tickers.py
    - server/tests/test_ledger_tickers.py
    - docs/DIAGNOSTICO-tickers-ledger-2026-08-28.md
  modified:
    - server/app/signal_ledger_bootstrap.py
    - server/tests/test_signal_ledger_bootstrap.py
    - docs/OPERACAO-ledger-de-sinais.md

key-decisions:
  - "MRFG3 e EMBR3 fecharam como ALIAS (MBRF3, EMBJ3) via renomeação confirmada por série de preço contínua de 2 anos, não só busca por raiz de ticker"
  - "JBSS3/CRFB3/NTCO3/CPLE6/BRFS3 fecharam como EXCLUIR (reorganização societária, deslistagem ou classe extinta), nunca emendados ao ledger"
  - "ELET3/ELET6 ficaram INDETERMINADO — evidência de hoje não fecha nenhum dos outros vereditos"
  - "Investigação estendeu-se além das 3 sondas literais do script (Task 1) com verificação suplementar por metadado de quote + busca por nome de empresa — decisão autônoma D-EXEC-00-01-01, ver seção abaixo"

requirements-completed: [LEDGER-01]

duration: ~50min
completed: 2026-08-28
---

# Phase 00 Plan 01: Diagnóstico e resolução dos 9 tickers 404 no bootstrap do ledger Summary

**Fecha LEDGER-01: mapa de resolução (`ledger_tickers.py`) + retry de 404 escopado no bootstrap fazem os 74 tickers de `scanner.DEFAULT_UNIVERSE` atravessarem `signal_ledger_bootstrap` sem 404 residual — 2 renomeações confirmadas por série de preço contínua (MRFG3→MBRF3, EMBR3→EMBJ3), 5 exclusões documentadas (fusão/deslistagem/classe extinta) e 2 lacunas abertas e explícitas (ELET3/ELET6).**

## Performance

- **Duration:** ~50 min (investigação de rede real + TDD + validação dupla da suíte canônica)
- **Completed:** 2026-08-28
- **Tasks:** 3/3 completas
- **Files modified:** 7 (4 criados, 3 modificados)

## Accomplishments

- Diagnóstico datado com evidência bruta (JSON de 3 sondas + verificação suplementar) para os 9 tickers, cada um com veredito de uma das 4 palavras exatas exigidas pelo plano.
- `server/app/ledger_tickers.py` — mapa `ALIASES`/`EXCLUIDOS` + `resolver()`, isolado do universo visível do Radar (decisão A-01), com teste offline cobrindo todo o `<behavior>` do plano.
- `signal_ledger_bootstrap.py` ganhou retry escopado de HTTP 404 (2 tentativas, decisão A-03 — `yahoo._yfetch` intocado) e um bucket `resumo["excluidos"]` sempre presente e impresso pela CLI.
- Varredura real dos 74 tickers (`--dry-run --anos 1 --rng 2y --concorrencia 2`) fechou com **`erros: 0`** na primeira rodada — sem necessidade de segunda varredura de confirmação.
- `docs/OPERACAO-ledger-de-sinais.md` documenta o mapa, a chave `excluidos` e o retry, de forma aditiva (nenhum parágrafo antigo removido, confirmado por `git diff`).
- Suíte canônica (`bash scripts/executar.sh --testes`) rodou 2 vezes com resultado idêntico: backend `1530 passed, 1 skipped`, web `105/105 OK`, `exit 0` nas duas.

## Veredito final dos 9 tickers

| Ticker | Veredito | Evidência-chave |
|---|---|---|
| ELET3 | `INDETERMINADO` | 404 em 3/3, quote Yahoo vazio, sem candidato em nenhuma busca (raiz/nome) |
| BRFS3 | `EXCLUIR` | Sem série própria remanescente; fusão com Marfrig em "MBRF Global Foods Company S.A.", mas patamar de preço de MBRF3 bate com Marfrig, não com BRF |
| ELET6 | `INDETERMINADO` | Mesma ausência total de ELET3, classe 6/PNB |
| JBSS3 | `EXCLUIR` | Sucessora (JBSS32.SA) é DR2 da JBS N.V. — classe/papel diferente do original |
| CRFB3 | `EXCLUIR` | Quote Yahoo confirma `quoteType=NONE`/`tradeable=false`; sem sucessora em nenhuma busca |
| NTCO3 | `EXCLUIR` | Mesmo padrão de CRFB3 (stub inativo confirmado); sem sucessora |
| CPLE6 | `EXCLUIR` | Classe PNB extinta; únicos candidatos são ON (CPLE3 e variantes), papel diferente |
| MRFG3 | `ALIAS:MBRF3` | Série de preço contínua de 2 anos (2024-08-27→2026-08-27), mesma classe ON, quote ativo |
| EMBR3 | `ALIAS:EMBJ3` | Série de preço contínua de 2 anos, mesma classe ON, quote ativo "Embraer S.A." |

**Varredura de fechamento (Task 3):** `tickers processados: 74 · sinais avaliados: 10929 · novas linhas gravadas: 0 · erros: 0`. 67 tickers processados com sucesso (incluindo os 2 aliases, buscados com sucesso pelo símbolo novo) + 7 excluídos sem tocar rede = 74. Nenhum ticker sumiu em silêncio.

## Task Commits

1. **Task 1: Diagnosticar os 9 tickers e escrever a evidência** - `d1553d3` (docs)
2. **Task 2 (RED — mapa de resolução):** `f0770e1` (test)
2. **Task 2 (GREEN — mapa de resolução):** `c5442ca` (feat)
2. **Task 2 (RED — retry/resolução no bootstrap):** `5d1e6b7` (test)
2. **Task 2 (GREEN — retry/resolução no bootstrap):** `be928e6` (feat)
3. **Task 3: Varredura do universo completo + docs + suíte canônica** - `728c819` (docs)

_TDD: Task 2 seguiu RED→GREEN em dois ciclos separados (mapa isolado, depois integração no bootstrap) — 4 commits, sequência confirmada em `git log`._

## Files Created/Modified

- `scripts/diagnostico-tickers-ledger.py` - script one-off de 3 sondas (primária/alias/contraprova) contra o Yahoo real, sem tocar produção
- `docs/DIAGNOSTICO-tickers-ledger-2026-08-28.md` - evidência bruta + veredito datado dos 9 tickers, incluindo verificação suplementar e "Verificação de fechamento" (Task 3)
- `server/app/ledger_tickers.py` - `ALIASES`, `EXCLUIDOS`, `resolver()` — mapa de resolução consumido pelo bootstrap, isolado do universo visível
- `server/tests/test_ledger_tickers.py` - cobertura offline de `resolver()`, disjunção dos mapas, formato das razões
- `server/app/signal_ledger_bootstrap.py` - retry escopado de 404 em `carregar_candles`; `executar()` resolve cada ticker antes de agendar fetch; `main()` imprime bloco de exclusões
- `server/tests/test_signal_ledger_bootstrap.py` - testes de retry (sucesso na 2ª tentativa, falha nas duas, erro não-404 sem retry) e de integração com `ledger_tickers` (exclusão não toca rede, alias busca símbolo novo e grava sob ticker do universo, chave `excluidos` sempre presente)
- `docs/OPERACAO-ledger-de-sinais.md` - seção 8 nova (aditiva) documentando o mapa, a chave `excluidos` e o retry; parágrafo adicional na seção 6

## Decisões Autônomas

Sob o contrato de autonomia da execução noturna (nenhuma pausa possível — ver
`<autonomy_contract>` do prompt de execução). Ambas registradas também em
`.planning/notes/decisoes-autonomas-v1.2.md` como `D-EXEC-00-01-01` e
`D-EXEC-00-01-02`.

### D-EXEC-00-01-01: Estender a investigação além das 3 sondas literais do script

**Decisão:** além das 3 sondas descritas no `<action>` da Task 1 (primária,
alias por raiz, contraprova), rodei uma verificação suplementar contra o
Yahoo real — metadado de `/v7/finance/quote` (distingue "código nunca
existiu" de "código existe mas está inativo") e `/v1/finance/search` por
NOME da empresa, não só raiz do ticker.

**Por quê:** a sonda de alias por raiz (Task 1) só encontra renomeação
quando o DÍGITO final muda, não quando a RAIZ inteira muda (ex.: `EMBR` →
`EMBJ`). Rodando só o script literal, MRFG3 e EMBR3 (que tinham renomeação
real, confirmável e evidenciável) teriam ficado `INDETERMINADO` por
limitação da busca, não por ausência real de dado — um resultado pior que
o alcançável com investigação adicional de baixo custo e sem tocar
produção.

**Alternativa descartada:** marcar os 9 como `INDETERMINADO` sempre que a
sonda de alias por raiz não encontrasse candidato — mais fiel à letra do
`<action>`, mas deixaria 2 renomeações reais sem fechar, forçando os 65+2=67
tickers resolvíveis hoje a ficarem em 65, sem necessidade.

**Efeito:** `ledger_tickers.py` nasce com 2 `ALIASES` e 5 `EXCLUIR` em vez
de 7 tickers adicionais em `INDETERMINADO`. Reversível: um diagnóstico
futuro pode reclassificar qualquer entrada trocando só o dicionário, sem
tocar `signal_ledger_bootstrap.py`.

### D-EXEC-00-01-02: BRFS3 classificado `EXCLUIR`, não `INDETERMINADO`

**Decisão:** BRFS3 recebeu veredito `EXCLUIR` (fusão com Marfrig em "MBRF
Global Foods Company S.A.") apesar de não haver uma sucessora de BRF
encontrada sob nenhum código — a evidência é circunstancial (nome da
entidade combinada + ausência total de registro de BRFS3), não uma
sucessora direta testada com série de preço.

**Por quê:** o quote de `BRFS3.SA` está VAZIO no Yahoo (nem stub inativo,
diferente de CRFB3/JBSS3/NTCO3) e `MBRF3.SA` (nome
"MBRF Global Foods Company S.A.") confirma uma fusão real Marfrig+BRF; a
série de MBRF3 tem patamar de preço de Marfrig, não de BRF, o que é
evidência (não prova definitiva) de que BRF foi incorporada via troca de
ações, não simplesmente renomeada. `EXCLUIR` e `INDETERMINADO` têm efeito
IDÊNTICO em `ledger_tickers.EXCLUIDOS` (ambos removem o ticker do
bootstrap) — a diferença é só o rótulo de documentação.

**Alternativa descartada:** `INDETERMINADO` — mais conservador, mas
esconderia a evidência real encontrada (nome da entidade combinada) atrás
de um rótulo que sugere "nenhuma pista". Optei pela opção que preserva
mais informação no texto sem mudar o efeito prático no bootstrap —
critério de reversibilidade do contrato de autonomia.

## Deviations from Plan

Nenhum desvio de Regra 1-4 além das decisões autônomas documentadas acima
(que o próprio plano antecipou como território de decisão do executor via
A-04 — "ticker que o diagnóstico não conseguir resolver hoje vira
INDETERMINADO, não falha do plano"). Nenhuma arquitetura nova, nenhum
bug pré-existente corrigido fora de escopo.

## Issues Encountered

Nenhum. A varredura de fechamento (Task 3) fechou com `erros: 0` na
primeira tentativa — não foi necessária a segunda rodada prevista no passo
3 da Task 3 para separar "transitório da janela" de "persistente".

## User Setup Required

None - nenhuma configuração de serviço externo necessária. Nenhuma env var
criada/alterada (guardrail verificado por `git status`/`git diff --stat`
não mostrando `.env` nem config de ambiente).

## Next Phase Readiness

- LEDGER-01 fechado: a Fase 10 (ponte gatilho→put) pode consumir o ledger
  de sinais sabendo que os 74 tickers do universo (menos os 2
  `INDETERMINADO` documentados) contribuem para a ponderação do ADR-017
  sem viés silencioso de amostra.
- ELET3/ELET6 seguem como lacuna aberta e documentada — não bloqueiam a
  Fase 10 (a ponte gatilho→put opera sobre o que já está no ledger), mas
  ficam candidatos a um diagnóstico futuro caso surja evidência nova
  (ex.: Eletrobras reaparecer no índice de busca do Yahoo).
- `docs/DIAGNOSTICO-tickers-ledger-2026-08-28.md` seção 5 registra a
  limitação da sonda de alias por raiz — útil para quem reexecutar este
  diagnóstico no futuro.

---
*Phase: 00-precondi-es*
*Completed: 2026-08-28*

## Self-Check: PASSED

All created files verified present on disk (scripts/diagnostico-tickers-ledger.py,
server/app/ledger_tickers.py, server/tests/test_ledger_tickers.py,
docs/DIAGNOSTICO-tickers-ledger-2026-08-28.md, this SUMMARY.md,
.planning/notes/decisoes-autonomas-v1.2.md). All 6 task commits (d1553d3,
f0770e1, c5442ca, 5d1e6b7, be928e6, 728c819) verified present in `git log`.
