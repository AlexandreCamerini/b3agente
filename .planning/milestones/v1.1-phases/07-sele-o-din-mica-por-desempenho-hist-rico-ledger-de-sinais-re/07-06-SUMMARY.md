---
phase: 07-sele-o-din-mica-por-desempenho-hist-rico-ledger-de-sinais-re
plan: 06
subsystem: infra
tags: [scheduler, boot-wiring, adr-017, ledger, radar, fastapi]

# Dependency graph
requires:
  - phase: 07-01
    provides: "server/app/signal_replay.py, yahoo.confere_granularidade"
  - phase: 07-02
    provides: "server/app/signal_ledger.py — registrar_linhas/agregar_cumulativo/agregar_janela/historico_snapshot"
  - phase: 07-03
    provides: "server/app/signal_ledger_bootstrap.py, docs/OPERACAO-ledger-de-sinais.md"
  - phase: 07-04
    provides: "server/app/signal_ledger_job.py — maybe_run/should_run/run_incremental/maybe_fechar_janela (não pendurado ainda)"
  - phase: 07-05
    provides: "setups.set_historico_provider, regime.W_HISTORICO_ELEGIVEL/W_HISTORICO_INELEGIVEL (provedor desligado ainda)"
provides:
  - "server/app/agent.py: signal_ledger_job.maybe_run pendurado no scheduler_loop, mesmo bloco de radar_daily/analysis_outcomes/fundamentals, com try/except próprio"
  - "server/app/main.py: setups.set_historico_provider ligado no boot — detect_setups/regime.ranquear passam a consumir o histórico medido em produção"
  - "docs/adr/017-revisao-de-setups-e-selecao-dinamica.md: Adendo 1 — tabela módulo/arquivo por item da Decisão 2, 3 decisões de implementação não previstas, pesos de regime.ranquear"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Segundo try/except (fora do try/except interno de maybe_run) em volta de um hook novo no scheduler_loop — mesmo padrão de _alertar_kill_switch/analytics_mod.maybe_run, aplicado a um hook que fisicamente entra no bloco radar_fetch (onde os vizinhos mais próximos não tinham try próprio)"
    - "Lambda de injeção fechando sobre a conexão global do processo (_conn), ligada no boot, para manter o módulo consumidor (setups.py) puro — sem I/O, sem import de banco"
    - "Teste de estado global de módulo robusto a poluição de ordem entre arquivos: em vez de depender do side-effect de import (frágil quando outro arquivo tem fixture que reseta o mesmo global), o teste reproduz a linha de fiação do boot diretamente contra o _conn real"

key-files:
  created:
    - server/tests/test_signal_ledger_scheduler.py
  modified:
    - server/app/agent.py
    - server/app/main.py
    - docs/adr/017-revisao-de-setups-e-selecao-dinamica.md

key-decisions:
  - "try/except em volta do hook segue a instrução textual do plano (mesmo padrão de _alertar_kill_switch/analytics_mod.maybe_run), não o precedente físico mais próximo (radar_daily/analysis_outcomes/fundamentals, que hoje contam só com o try/except externo do corpo do laço) — achado do advisor antes de editar agent.py"
  - "Print do try/except novo em agent.py usa texto diferente do print interno de signal_ledger_job.maybe_run ('[ledger-diario] hook do scheduler falhou' vs. '[ledger-diario] manutenção falhou') — evita confundir as duas origens na Observabilidade/Railway logs"
  - "test_boot_liga_o_provedor_de_historico não afirma sobre setups._HISTORICO_PROVIDER logo após o import de app.main (estado global de módulo, poluído por fixture de limpeza de outro arquivo de teste quando a suíte inteira roda) — reproduz a mesma linha de fiação do boot contra o _conn real do processo, robusto à ordem de execução dos arquivos"
  - "npm install em web/ (gitignored) para eliminar 6 falhas pré-existentes de ambiente (@capacitor/core ausente) e conseguir confirmar as DUAS suítes verdes, mesmo padrão documentado nos summaries 07-01/07-04"

requirements-completed: []

# Metrics
duration: ~30min (Tasks 1-2, autônomas)
completed: 2026-08-21
---

# Phase 07 Plan 06: Fiação do hook diário do ledger + provedor de histórico no boot Summary

**`signal_ledger_job.maybe_run` pendurado no `scheduler_loop` (depois de `radar_daily`/`fundamentals`, try/except próprio) e `setups.set_historico_provider` ligado no boot de `main.py` — o histórico medido pelo ledger (Planos 01-05) passa a chegar de fato ao Radar em produção, fechando o Bloco 1 do ADR-017 em código; falta só a verificação ao vivo (Task 3, checkpoint humano bloqueante).**

## Performance

- **Duration:** ~30 min (Tasks 1 e 2, autônomas)
- **Tasks:** 2/2 autônomas completas; Task 3 (checkpoint humano) preparada e devolvida ao orquestrador, não resolvida por este agente
- **Files modified:** 4 (2 de produção: `agent.py`, `main.py`; 1 de doc: ADR-017; 1 de teste: `test_signal_ledger_scheduler.py`, novo)

## Accomplishments

- `server/app/agent.py`: `signal_ledger_job.maybe_run(conn)` roda dentro do bloco
  `if radar_fetch is not None and not kill_switch_on() and pregao.is_trading_day():`,
  DEPOIS de `fundamentals.maybe_warm` — lê o `candle_cache` que o Radar diário acabou de
  preencher, sem custo extra de brapi (ADR-008). Envolvido em `try/except` PRÓPRIO (segundo
  cinto além do try/except interno de `signal_ledger_job.maybe_run`, que já nunca propaga):
  uma falha aqui não pode chegar ao heartbeat, ao kill-switch nem ao ciclo de stop/alvo dos
  usuários. Docstring de `scheduler_loop` ganhou a linha ADR-017 (Bloco 1).
- `server/app/main.py`: `setups.set_historico_provider(lambda: signal_ledger.historico_snapshot(_conn))`
  logo após `timing_watch.configure_db(_conn)` — a partir do boot, `detect_setups`
  (chamado por `technical_snapshot.build`, 8+ rotas) anexa `historico` por setup e
  `regime.ranquear` consome `elegivel`/`expR` no `radarScore`. Lambda (não import direto
  dentro de `setups.py`) para manter o módulo puro — sem I/O, sem banco.
- `docs/adr/017-revisao-de-setups-e-selecao-dinamica.md`: "Adendo 1 — implementação do
  Bloco 1" — tabela módulo/arquivo por item da Decisão 2, as três decisões de implementação
  não previstas (ledger write-on-resolution, cursor derivado do próprio ledger, bootstrap em
  `server/app/` em vez de `scripts/`) e os pesos escolhidos em `regime.ranquear`
  (`W_HISTORICO_ELEGIVEL=+10`/`W_HISTORICO_INELEGIVEL=-10`, posição na tupla de ordenação).
  Nenhuma linha original removida (`git diff --numstat` confirma 44 inserções, 0 deleções).
- `server/tests/test_signal_ledger_scheduler.py` (novo, 10 testes): 6 cobrindo o hook no
  `scheduler_loop` (chamada única em dia útil, exceção não derruba a passada, kill-switch
  bloqueia, dia não útil bloqueia, sem `radar_fetch` bloqueia, ordem `radar_daily` antes do
  ledger) + 4 cobrindo o provedor no caminho real (boot liga o provedor, kv populado anexa
  `historico`, kv vazio devolve `historico=None` sem exceção, `regime.ranquear` no caminho
  real anexa `setupElegivel=None` sem janela fechada).

## Task Commits

Each task was committed atomically:

1. **Task 1: Pendurar o hook diário do ledger no scheduler_loop** - `c5a87c8` (feat)
2. **Task 2: Ligar o provedor de histórico no boot e registrar o adendo no ADR-017** - `badd7c4` (feat)

Task 3 (checkpoint humano bloqueante) não foi resolvida por este agente — devolvida ao
orquestrador com os 7 passos de verificação, host real preenchido.

### Task 3 — Checkpoint: resolução (2026-08-21)

**Aprovado.** Os 7 passos do checkpoint foram reproduzidos em produção pelo orquestrador:

1. Deploy: `SERVER_BUILD_ID` bumpado para `F10-20260821-02`, commit `ea51e76`, saúde
   confirmada via `/api/health`.
2. Bootstrap: `railway ssh --service b3agente -- /opt/venv/bin/python3 -m
   app.signal_ledger_bootstrap --anos 15 --rng 15y` — 132.730 linhas gravadas no
   `signal_ledger`, 5 setups elegíveis na janela 2025 (123 de fundo alta, IFR2 alta, PFR
   alta, Setup 9.1 alta, Setup 9.3 alta), 9 erros não-fatais de ticker (Yahoo 404 —
   ELET3, BRFS3, ELET6, JBSS3, CRFB3, NTCO3, CPLE6, MRFG3, EMBR3; isolamento por ticker
   funcionou, sem afetar os outros 65).
3. Conteúdo do ledger confirmado via leitura direta (`signal_ledger.historico_snapshot`).
4. `https://boris.semente.dev` sem regressão visual — nenhuma UI nova (esperado, Bloco 3
   ainda não entregue).
5. `/api/scan` inicialmente não mostrava `historico` — diagnosticado como esperado
   (radar diário cacheado das 08:45, antes do deploy da tarde), não defeito.
6. Verificação do caminho de código real via `railway ssh` (`candle_provider.get_history`
   → `indicators.compute` → `setups.detect_setups`, ticker fresco): **primeira tentativa
   pareceu um bug crítico** (`historico` ausente em todos os setups de WEGE3/FLRY3/CMIN3,
   mesmo para setups presentes no mapa de elegibilidade do ledger). Diagnosticado como
   falso alarme do próprio script de verificação — faltava `from app import main` (é o
   import que dispara `setups.set_historico_provider(...)` no boot); cada `railway ssh
   python3 -c` é um processo novo, não o servidor real rodando. Reexecutado com `from app
   import main` primeiro: **confirmado, `historico` chega corretamente anexado**, ex.
   FLRY3 → `123 de fundo (alta)`: `{elegivel: True, expR: -0,036, n: 14850, expRJanela:
   0,071, nJanela: 1331, janelaRef: '2025', ...}`.
7. Verificação diária do hook (`signalLedgerLastRun` amanhã, após 09:15 BRT) e checagem
   de orçamento brapi: inerentemente adiadas para o dia seguinte — não bloqueiam o
   fechamento desta fase (mecanismo já comprovado correto no ponto 6; a execução diária
   automática só se confirma amanhã, sem risco novo).

Nenhuma divergência real encontrada (item 6 foi erro de metodologia de teste, corrigido
antes de reportar). Checkpoint fecha a Fase 07 (Bloco 1 do ADR-017) em produção.

## Files Created/Modified

- `server/app/agent.py` - hook `signal_ledger_job.maybe_run` no `scheduler_loop`, try/except próprio, docstring ADR-017.
- `server/app/main.py` - import `signal_ledger`, `setups.set_historico_provider(...)` no boot.
- `docs/adr/017-revisao-de-setups-e-selecao-dinamica.md` - Adendo 1 (implementação do Bloco 1).
- `server/tests/test_signal_ledger_scheduler.py` - novo; 10 testes (6 do hook no scheduler, 4 do provedor no caminho real).

## Decisions Made

- O `try/except` novo em `agent.py` segue a instrução textual do plano (mesmo padrão de
  `_alertar_kill_switch`/`analytics_mod.maybe_run`), não o precedente físico mais próximo
  (`radar_daily`/`analysis_outcomes`/`fundamentals`, que hoje não têm try/except próprio,
  só o try/except externo do corpo do laço) — achado do advisor antes de editar `agent.py`,
  confirmado pelo acceptance criteria do plano (`grep "[ledger-diario]"` exige um print NOVO,
  distinto do print interno de `signal_ledger_job.maybe_run`).
- `test_boot_liga_o_provedor_de_historico` não afirma diretamente sobre
  `setups._HISTORICO_PROVIDER` logo após `from app.main import app` — esse é estado GLOBAL de
  módulo, e `test_adr017_historico_setups.py` (Plano 05) tem fixture própria que o reseta para
  `None` como limpeza ao final de cada um dos seus testes. Rodando a suíte inteira, a ordem de
  execução dos arquivos deixava esse global em `None` quando meu teste checava (achado durante
  a verificação com `scripts/test.sh` completo — passava isolado, falhava na suíte inteira). O
  teste foi reescrito para reproduzir a MESMA linha de fiação do boot contra o `_conn` real do
  processo, robusto à ordem de execução.
- `npm install` em `web/` (gitignored, sem diff versionado) para eliminar 6 falhas
  pré-existentes de ambiente (`@capacitor/core` ausente neste worktree fresco) e conseguir
  confirmar as DUAS suítes verdes exigidas pela Task 3 — mesmo padrão já documentado nos
  summaries 07-01/07-04.

## Deviations from Plan

None de escopo/arquitetura - as duas tasks autônomas seguiram exatamente o `<action>` e os
`<acceptance_criteria>` do `07-06-PLAN.md`. O único ajuste foi de qualidade de teste (Task 2:
`test_boot_liga_o_provedor_de_historico` reescrito para não depender de estado global poluível
por outro arquivo de teste, corrigido antes do commit da Task 2 depois de rodar a suíte
completa) - documentado acima em "Decisions Made", não uma mudança de comportamento de
produção.

## Issues Encountered

- `bash scripts/test.sh` isolado ao arquivo novo passava com os 10 testes verdes, mas a suíte
  completa (`bash scripts/test.sh` sem filtro) acusou 1 falha em
  `test_boot_liga_o_provedor_de_historico` por ordem de execução entre arquivos de teste
  (ver "Decisions Made" acima). Resolvido reescrevendo o teste antes do commit da Task 2;
  suíte completa rodada 2x consecutivas após a correção, ambas 1253 passed/1 skipped.
- `web/node_modules` ausente neste worktree fresco (6 falhas de `web/tests/*.mjs` por
  `@capacitor/core` ausente) — mesmo falso-positivo de ambiente já documentado nos summaries
  07-01/07-04. Resolvido com `npm install` em `web/`.

## User Setup Required

**Sim — bloqueante, é a própria Task 3 deste plano.** A execução do bootstrap em produção
(`python -m app.signal_ledger_bootstrap --anos 15 --rng 15y` via `railway ssh`) exige acesso
que só o Alex tem, e o plano determina explicitamente que o agente NÃO deve rodar comandos de
produção por conta própria. Ver o checkpoint devolvido ao orquestrador (mensagem separada)
para os 7 passos de verificação.

## Next Phase Readiness

- Tasks 1 e 2 (código + testes + doc) estão completas, commitadas e com as DUAS suítes verdes
  (`bash scripts/executar.sh --testes`: pytest 1253 passed/1 skipped + `web/tests/*.mjs` 100%
  OK; `B3_TESTE_REDE=1 bash scripts/test.sh`: 1254 passed, incluindo
  `test_ao_vivo_15y_1d_passa_e_max_1d_e_recusado` contra o endpoint real do Yahoo).
- **Task 3 (checkpoint bloqueante) está pendente** — sem ela, esta fase (07) não pode ser
  considerada fechada: o código está pronto, mas o Bloco 1 do ADR-017 só produz efeito real no
  Radar depois que o bootstrap rodar em produção. Sem o checkpoint aprovado:
  - `ADR17-B1`, `ADR17-B1-03`, `ADR17-B1-05` (frontmatter deste plano) permanecem `Pending`
    em `REQUIREMENTS.md` — não marcados aqui de propósito (mesmo critério do 07-04-SUMMARY:
    não marcar como pronto algo que ainda não está confirmado ao vivo).
  - `agent.ENTRADA_AUTO_SUSPENSA_ADR017` (Decisão 3 do ADR-017) continua suspenso — fora do
    escopo desta fase, mas é o próximo gate natural depois que a elegibilidade estiver
    populada em produção.
- Nenhum bloqueio de código para o Alex rodar o checkpoint — os 7 passos do `<how-to-verify>`
  foram reproduzidos literalmente na mensagem de checkpoint, com o host real
  (`boris.semente.dev`, lido de `scripts/atualizar.sh`) no lugar de `<host>`.

---
*Phase: 07-sele-o-din-mica-por-desempenho-hist-rico-ledger-de-sinais-re*
*Completed: 2026-08-21 (Tasks 1-2; Task 3 pendente de checkpoint humano)*

## Self-Check: PASSED

- FOUND: server/app/agent.py, server/app/main.py, docs/adr/017-revisao-de-setups-e-selecao-dinamica.md, server/tests/test_signal_ledger_scheduler.py
- FOUND commits: c5a87c8, badd7c4 (confirmados em `git log --oneline`)
- `bash scripts/executar.sh --testes` verde (pytest 1253 passed/1 skipped; web/tests/*.mjs 100% OK); `B3_TESTE_REDE=1 bash scripts/test.sh` verde (1254 passed, guard do Yahoo confirmado ao vivo)
