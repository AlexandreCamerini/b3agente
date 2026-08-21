---
phase: 08-interface-e-ia-da-sele-o-din-mica-vocabul-rio-novo-skill-ref
plan: 02
subsystem: agent
tags: [python, fastapi, sqlite, adr-017, entrada-automatica, seleção-dinâmica, pytest]

# Dependency graph
requires:
  - phase: 07-sele-o-din-mica-por-desempenho-hist-rico-ledger-de-sinais-re
    provides: "signal_ledger.historico_snapshot(conn) em produção, medindo elegibilidade por setup×lado na janela anual fechada"
provides:
  - "Gate de elegibilidade em server/app/agent.py:_avaliar_entradas, substituindo a suspensão cega ENTRADA_AUTO_SUSPENSA_ADR017"
  - "Guardião reescrito test_entrada_automatica_suspensa_adr017.py provando os 3 casos negativos (False/None/ausente) + liberação (True) + falha-fechada + leitura única por chamada"
  - "test_entrada_automatica.py rodando contra o gate real (stub elegível), não mais contra uma flag desligada"
  - "Adendo 2 no ADR-017 registrando o religamento gated do Bloco 4"
affects: [08-05, agent.py, adr-017]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Import local dentro de função para evitar ciclo (mesmo padrão de signal_ledger_job em agent.py:1112, replicado para signal_ledger)"
    - "Predicado único `is not True` cobrindo todos os casos de bloqueio (False, None, ausente) em vez de branches separados"
    - "Leitura única de fonte cacheada (historico_snapshot) fora do laço de candidatos, não por-ticker"

key-files:
  created: []
  modified:
    - server/app/agent.py
    - server/tests/test_entrada_automatica_suspensa_adr017.py
    - server/tests/test_entrada_automatica.py
    - docs/adr/017-revisao-de-setups-e-selecao-dinamica.md

key-decisions:
  - "Bloqueio permanece SILENCIOSO (sem events.append, sem log) — mesmo comportamento da suspensão anterior, decisão explícita do 08-CONTEXT.md (T-08-09, ausência de transparência aceita nesta camada; a vitrine vive nos Planos 08-03/08-04)"
  - "Fixtures dos dois arquivos de teste trocaram o literal inventado \"rompimento\" por \"IFR2 (alta)\" (nome real do catálogo, setups.py:303) para exercitar de fato o acoplamento de chave por nome exato entre timing.montar()['setup'] e o snapshot do ledger (T-08-08)"

patterns-established:
  - "Gate de elegibilidade fica ANTES das checagens de orçamento/tetos, nunca as substitui — mecânica de lote/orçamento/maxOpsDia/maxValorOp/dedupe idêntica de antes"

requirements-completed: [ADR17-B34-04]

# Metrics
duration: ~35min
completed: 2026-08-21
---

# Phase 08 Plan 02: Gate de elegibilidade no lugar da suspensão cega (ADR-017 Bloco 4) Summary

**A entrada automática do Modo Operador volta a existir, mas só executa o setup que a seleção dinâmica (ledger, Fase 7) mediu como elegível na janela anterior fechada — sem lista hardcodada, hoje restrito a 5 pares setup×lado (123 de fundo alta, IFR2 alta, PFR alta, Setup 9.1 alta, Setup 9.3 alta), e nenhum deploy foi feito neste plano.**

## Performance

- **Duration:** ~35 min
- **Started:** 2026-08-21T20:10:00Z (aprox.)
- **Completed:** 2026-08-21T20:44:43Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Removida a constante `ENTRADA_AUTO_SUSPENSA_ADR017` e o early-return incondicional em `_avaliar_entradas` — substituída por um gate por elegibilidade medida do setup do gatilho (`signal_ledger.historico_snapshot`, consultado uma única vez por chamada, import local no mesmo padrão de `signal_ledger_job`).
- Guardião `test_entrada_automatica_suspensa_adr017.py` reescrito (nome preservado, guardrail do repositório) cobrindo `elegivel is True` (libera), `False`/`None`/ausente (bloqueiam em silêncio), snapshot vazio por falha de leitura (falha FECHADO) e leitura única por chamada com spy.
- `test_entrada_automatica.py` (mecânica: lote, orçamento, maxOpsDia, maxValorOp, dedupe com o vigia) passa a rodar contra o gate REAL, com um stub de `historico_snapshot` que devolve o setup dos cenários como elegível — nenhuma asserção de mecânica mudou (10/10 testes mantidos).
- ADR-017 ganhou o Adendo 2, por adição, sem reescrever texto histórico (Decisão 3, Consequências, Adendo 1 intactos).

## Task Commits

Each task was committed atomically:

1. **Task 1: Gate de elegibilidade no lugar da suspensão cega** - `70cd2c1` (feat)
2. **Task 2: Fixture da mecânica + Adendo 2 no ADR-017** - `ab5554c` (test)

**Plan metadata:** (commit deste SUMMARY, feito pelo orquestrador junto com STATE.md/ROADMAP.md — este agente NÃO grava esses arquivos compartilhados)

## Files Created/Modified
- `server/app/agent.py` - `_avaliar_entradas`: gate por `elegivel is True` do setup do gatilho, import local de `signal_ledger`, leitura única do snapshot fora do laço, flag antiga removida
- `server/tests/test_entrada_automatica_suspensa_adr017.py` - reescrito: guardião do gate (7 testes: flag ausente, True libera, False/None/ausente/snapshot-vazio bloqueiam, leitura única por chamada com spy)
- `server/tests/test_entrada_automatica.py` - fixture autouse trocada (`_desliga_suspensao_adr017` → `_setup_elegivel_no_ledger`, monkeypatch de `historico_snapshot`); literal `"rompimento"` trocado por `"IFR2 (alta)"`
- `docs/adr/017-revisao-de-setups-e-selecao-dinamica.md` - Adendo 2 acrescentado ao fim (religamento gated, regra exata, foto do dado do bootstrap, checkpoint humano pendente no Plano 08-05)

## Decisions Made
- Bloqueio silencioso mantido — não é erro, é o gate funcionando (decisão já registrada no 08-CONTEXT.md, T-08-09 aceito no threat model do plano).
- `"rompimento"` (nome inventado, fora do catálogo de `setups.py`) trocado por `"IFR2 (alta)"` (nome real) nas duas fixtures — sem essa troca, o teste do acoplamento de chave por nome exato (T-08-08) não exercitava o caminho real.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- `bash scripts/executar.sh --testes` falhou inicialmente com 7 testes web fora do escopo deste plano (`test_appmode_sincroniza_servidor`, `test_carteira_nativa_sincroniza`, `test_fase2_portfolio`, `test_notif_central`, `test_notify`, `test_oauth_repassa_name_e_code`, `test_pet_resumo_modo_web`) — causa já documentada em PROJECT.md: worktree novo sem `web/node_modules` instalado. Resolvido rodando `npm install` em `web/` (nenhuma mudança de código, `node_modules` é gitignored). Após o install, suíte completa (backend 1258 passed/1 skipped + toda a suíte web) verde, `exit 0`.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Código do gate pronto e testado; NÃO foi deployado (nenhum `atualizar.sh`/`entregar.sh`/`railway`/`git push` executado neste plano, por escopo explícito do plano).
- O checkpoint humano bloqueante antes do deploy em produção deste religamento vive no Plano 08-05 desta mesma fase — não seguir sem aprovação explícita do Alex.
- Planos 08-01/08-03/08-04 (vocabulário e telas) seguem independentes deste plano, sem overlap de arquivo.

---
*Phase: 08-interface-e-ia-da-sele-o-din-mica-vocabul-rio-novo-skill-ref*
*Completed: 2026-08-21*
