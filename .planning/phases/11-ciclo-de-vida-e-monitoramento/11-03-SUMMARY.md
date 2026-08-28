---
phase: 11-ciclo-de-vida-e-monitoramento
plan: 03
subsystem: options
tags: [put, ciclo-de-vida, guardiao, adr-022, threat-model, long-only, dormancy]

# Dependency graph
requires:
  - phase: 11-ciclo-de-vida-e-monitoramento (plano 01)
    provides: "put_suggestions.transicionar/ESTADOS/TRANSICOES (porta única de escrita) e put_lifecycle.decidir/resolver_spots/intrinseco (máquina de decisão PURA)"
  - phase: 11-ciclo-de-vida-e-monitoramento (plano 02)
    provides: "put_lifecycle.run_diario/maybe_run pendurado no scheduler_loop, fora do gate de kill-switch/pregão/radar_fetch"
provides:
  - "server/tests/test_put_lifecycle_sem_carteira.py: guardião permanente — carteira intocada por comportamento, produto cartesiano de transições recusadas, anti-limbo, ausência de superfície"
  - "docs/adr/022-ciclo-de-vida-da-sugestao-de-put.md: registro permanente da decisão de desenho (fora de .planning/)"
  - "docs/OPERACAO-ciclo-de-vida-put.md: runbook de operação da varredura diária"
affects: []

tech-stack:
  added: []
  patterns:
    - "Guardião de comportamento (não de diff, D-10-M): monta carteira real via db.kv_set DIRETO (bypass de store.buy_option/sell_option/etc), roda ciclo de vida completo, compara == e json.dumps(sort_keys=True) antes/depois — pega qualquer via de escrita, conhecida ou não (A-11-11)"
    - "Produto cartesiano ESTADOS × ESTADOS sobre a porta única de escrita (transicionar) prova que nenhuma transição não-declarada é gravável, sem depender de enumerar casos individualmente"
    - "Anti-limbo por tricotomia: toda linha pós-rodada satisfaz terminal ∨ avançou-hoje (estado_em em UTC real) ∨ pendência-datada (pendente_desde em BRT real) — os dois relógios são intencionalmente distintos (transicionar usa db._now_iso() UTC; run_diario usa datetime.now(BRT) para `hoje`)"

key-files:
  created:
    - server/tests/test_put_lifecycle_sem_carteira.py
    - docs/adr/022-ciclo-de-vida-da-sugestao-de-put.md
    - docs/OPERACAO-ciclo-de-vida-put.md
  modified: []

key-decisions:
  - "Nenhuma decisão autônoma exigida nesta execução — os 3 blocos do guardião (A: leitura de fonte, B: comportamento, C: prova de RED) passaram na primeira tentativa, incluindo a prova de RED real (não erro de import) e a asserção anti-limbo com os dois relógios (UTC/BRT) distintos calculados dinamicamente a partir do relógio real, sem data hardcoded"

requirements-completed: [PUTLIFE-01, PUTLIFE-02, PUTLIFE-03, PUTLIFE-04]

duration: ~13min
completed: 2026-08-28
---

# Phase 11 Plan 03: Guardião permanente do ciclo de vida + ADR-022 + runbook Summary

**`test_put_lifecycle_sem_carteira.py` prova por COMPORTAMENTO — carteira montada via `db.kv_set` direto, nunca `store.buy_option`/`sell_option` — que um ciclo de vida completo (armada→executada_simulada→monitorada→fechada) deixa `optionPositions`/`cash`/`history` byte-idênticos, que nenhuma transição de estado fora do produto cartesiano declarado é gravável, e que nenhuma linha fica em limbo silencioso; ADR-022 e o runbook fecham os 4 requisitos da Fase 11 com evidência que sobrevive ao `.planning/`.**

## Performance

- **Duration:** ~13 min (leitura de contexto até o commit final de Task 2)
- **Completed:** 2026-08-28
- **Tasks:** 2/2
- **Files modified:** 3 (todos criados, nenhum modificado)

## Accomplishments

- `server/tests/test_put_lifecycle_sem_carteira.py` nasce com 15 testes em 3 blocos:
  - **Bloco A (5 testes, leitura de fonte):** `put_lifecycle.py`/`put_suggestions.py` nunca mencionam `buy_option`/`sell_option`/`close_option_vencida`/`set_option_position`/`optionPositions` (nem em docstring, comentários filtrados); nenhum dos dois importa `store`; nenhum dos dois menciona `web/`/`skill_ref`/`defaults`; `put_lifecycle.py` nunca menciona `options_provider`/`mydata_client`/`candle_provider`/`httpx`/`B3_OPTIONS_PROVIDER`; `agent.py` não ganha a string `putLifecycle`.
  - **Bloco B (9 testes, comportamento):** ciclo de vida completo de 4 rodadas sobre uma carteira REAL (cash=8500.0, 1 posição, 2 entradas de histórico, 1 posição de opção pré-existente) prova `cash`/`positions`/`history`/`optionPositions` **idênticos** (`==` e `json.dumps(sort_keys=True)`) antes/depois, com a linha percorrendo `armada → executada_simulada → monitorada → monitorada (remarcação) → fechada` e fechando com `precoFechamento==6.5`/`pnlPorAcao==5.35` (intrínseco real, ADR-005); mesma prova no ramo `expirada_sem_uso` (sem prêmio, nunca inventa preço); anti-limbo sobre rodada mista (candle disponível / candle ausente / linha já terminal) — toda linha termina terminal, avançou hoje (UTC real), ou tem `pendenteDesde` datado; produto cartesiano `ESTADOS × ESTADOS` recusa toda transição não declarada (estado não muda) + estado inexistente devolve 0; nenhuma rota nova em `app.main.app.routes`; agregações do ADR-017 (`agregar_cumulativo`/`agregar_janela`) seguem `porSetup == {}` com o ciclo de vida rodando de verdade.
  - **Bloco C (prova de RED, executada e revertida):** sentinela de código `_SENTINELA_RED = "optionPositions"` acrescentado ao fim de `put_lifecycle.py` fez `test_a1_nenhuma_funcao_de_escrita_de_opcao_mencionada[caminho0]` FALHAR de verdade (1 failed, 14 passed) — não um erro de import. `git checkout -- server/app/put_lifecycle.py` reverteu, `git diff --stat` voltou vazio, suíte de volta a 15/15.
- `docs/adr/022-ciclo-de-vida-da-sugestao-de-put.md`: 4 decisões no formato do ADR-021. Decisão 1 (o coração do ADR) cita as duas evidências duras com caminho e linha: `server/app/store.py:10` (`SECTIONS` inclui `optionPositions`/`cash`/`history`/`positions`) e `server/app/agent.py:531` (`_avaliar_opcoes` retorna cedo sem posição real de opção — a leitura literal do ROADMAP seria tecnicamente inerte). Decisão 2 documenta a tabela de 5 transições e a regra "armada com prêmio real sempre executa" (medição, sem filtro de qualidade inventado). Decisão 3 documenta as 3 razões do hook ficar fora do gate de kill-switch/pregão (com o precedente do incidente de 2,5 dias). Decisão 4 documenta custo de rede zero e a dormência de produção herdada do ADR-021.
- `docs/OPERACAO-ciclo-de-vida-put.md`: runbook de 6 seções (formato do runbook da ponte) — o que roda e quando (09:45 BRT), as 2 env vars (nenhuma definida em produção), por que `linhas: 0` hoje é o desenho, query SQL de inspeção (`GROUP BY estado` + linhas pendentes por `pendente_desde`), custo zero de rede, e o que explicitamente NÃO existe nesta fase.

## Task Commits

1. **Task 1: Guardião permanente — carteira intocada, ausência de superfície, anti-limbo**
   - `8a77dd6` (test) — 15 testes novos, todos passando na primeira tentativa; prova de RED executada e revertida antes do commit (diff vazio confirmado)
2. **Task 2: ADR-022 + runbook de operação + fechamento da suíte canônica**
   - `63afe72` (docs) — ADR-022 + `OPERACAO-ciclo-de-vida-put.md`; suíte canônica fechada 2x com resultado idêntico

## Files Created/Modified

- `server/tests/test_put_lifecycle_sem_carteira.py` — novo: 439 linhas, 15 testes (5 leitura de fonte + 9 comportamento + prova de RED documentada, não commitada como teste permanente)
- `docs/adr/022-ciclo-de-vida-da-sugestao-de-put.md` — novo: 4 decisões, 2 evidências duras com caminho/linha, tabela de transições, consequências com 3 itens "A revisitar"
- `docs/OPERACAO-ciclo-de-vida-put.md` — novo: runbook de 6 seções

## Acceptance Criteria (verificadas literalmente do plano)

`FASE10` = `6e7936348e0f01b53b9c2cc314a81dcbc752f607` (`git log --grep='docs(phase-10): evolve PROJECT.md'` resolveu no primeiro comando, sem precisar do fallback documentado no plano).

### Task 1

| Critério | Resultado |
|---|---|
| `pytest tests/test_put_lifecycle_sem_carteira.py -q` → exit 0, ≥12 testes, nenhum skip | PASSOU (15 passed) |
| `pytest tests/test_put_bridge_sem_superficie.py -q` → exit 0, 8 passed (guardião Fase 10 sem regressão) | PASSOU (23 passed no total combinado: 15+8) |
| Prova de RED: sentinela → ≥1 teste FALHA; `git checkout --` → diff vazio, suíte volta a exit 0 | PASSOU (1 failed com sentinela; diff vazio após reverter; 15 passed de volta) |
| `git diff --stat "$FASE10" -- server/app/store.py` → vazio | PASSOU |
| `git diff --stat "$FASE10" -- web/ web-admin/ server/app/skill_ref.py server/app/main.py server/app/defaults.py` → vazio | PASSOU |
| `git diff --stat -- server/app/` ao fim da task → vazio | PASSOU |
| `pytest -q` → exit 0, sem regressão | PASSOU (1674 passed, 1 skipped; baseline Plano 02 = 1659 + 15 novos) |

### Task 2

| Critério | Resultado |
|---|---|
| `ls docs/adr/022-...md docs/OPERACAO-ciclo-de-vida-put.md` | PASSOU (ambos existem) |
| `grep -c "PUTLIFE-02"` ADR-022 ≥ 1 | PASSOU (2) |
| `grep -c "ADR-021"` ADR-022 ≥ 1 | PASSOU (7) |
| `grep -cE "ADR-003\|ADR-004\|ADR-005"` ADR-022 ≥ 3 | PASSOU (10) |
| `grep -c "expirada sem uso"` ADR-022 ≥ 1 | PASSOU (1) |
| `grep -cE "B3_PUT_LIFECYCLE_HHMM\|B3_PUT_LIFECYCLE_OFF"` runbook ≥ 2 | PASSOU (2) |
| `git diff --stat -- docs/adr/021-*.md docs/OPERACAO-ponte-gatilho-put.md docs/adr/003*.md docs/adr/004*.md docs/adr/005*.md` → vazio | PASSOU |
| `git diff --stat -- server/app/` → vazio | PASSOU |
| `bash scripts/executar.sh --testes` → exit 0 nas DUAS execuções, contagem idêntica | PASSOU (ver seção abaixo) |
| `git status -sb` sem tracking remoto; `git ls-remote --heads origin \| grep -c worktree-agent` == 0 | PASSOU |
| `git diff --stat "$FASE10" -- server/app/store.py web/ web-admin/ server/app/skill_ref.py server/app/main.py server/app/defaults.py` → vazio | PASSOU |

### Suíte canônica (contrato de autonomia — 2 rodadas)

- `bash scripts/executar.sh --testes` rodada 1: `1674 passed, 1 skipped`, exit 0, 105 `.mjs` OK / 0 FAIL
- `bash scripts/executar.sh --testes` rodada 2: `1674 passed, 1 skipped`, exit 0, 105 `.mjs` OK / 0 FAIL
- Resultado idêntico nas duas rodadas. `git status --short` mostrou só os 2 arquivos novos de doc (nenhum artefato gerado deixado para trás) até o commit da Task 2.

## Fase 11 completa — requisitos mapeados à prova

| Requisito | Prova |
|---|---|
| PUTLIFE-01 (máquina de estado, porta única de escrita) | `put_suggestions.transicionar`/`ESTADOS`/`TRANSICOES` (Plano 01) + `test_b4_transicoes_nao_declaradas_sao_recusadas_produto_cartesiano`/`test_b4_estado_inexistente_e_recusado` (Plano 03): produto cartesiano `ESTADOS × ESTADOS` inteiro provado, não só casos avulsos |
| PUTLIFE-02 (nunca toca a carteira real) | `test_a1..a3` (leitura de fonte, Plano 03) + `test_b1_carteira_intocada_em_ciclo_completo`/`test_b2_carteira_intocada_no_ramo_sem_execucao` (comportamento: `==` e `json.dumps(sort_keys=True)` antes/depois de um ciclo completo, carteira montada via `db.kv_set` direto) |
| PUTLIFE-03 (reuso do intrínseco real do motor, vocabulário ADR-005) | `put_lifecycle.intrinseco()`/`MOTIVO_VENCIMENTO` (Plano 01, wrapper sobre `agent.intrinseco_opcao`) exercitado em `test_b1` (fechamento com `precoFechamento==6.5`, fórmula `max(0, strike-spot)` real) + `test_a4` (nenhuma fórmula paralela) |
| PUTLIFE-04 (nenhuma linha em limbo silencioso) | `put_suggestions.registrar_pendencia`/`listar_abertas` (Plano 01) + `run_diario` (Plano 02) + `test_b3_nenhuma_linha_em_limbo_apos_rodada_mista` (Plano 03: tricotomia terminal/avançou-hoje/pendência-datada sobre rodada mista real) |

## Decisões autônomas

Nenhuma decisão autônoma foi necessária nesta execução. Os 3 blocos do guardião (leitura de fonte, comportamento, prova de RED) passaram na primeira tentativa; a única atenção redobrada foi deliberada (não uma correção pós-falha): a asserção anti-limbo (B3) usa dois relógios DIFERENTES de propósito — `estadoEm` é escrito por `db._now_iso()` (UTC real, sempre, independente do `now=` passado a `run_diario`) enquanto `pendenteDesde`/a checagem de vencimento usam `datetime.now(BRT)` quando `run_diario` é chamado sem `now=` explícito. O teste computa os dois relógios reais dinamicamente (`datetime.now(timezone.utc)` e `datetime.now(put_lifecycle.BRT)`) em vez de datas hardcoded, e usa datas de candle/vencimento relativas ao relógio real (`agora - timedelta(days=1)`, `agora + timedelta(days=90)`) para o teste nunca ficar frágil a quando de fato executar. Isso não é uma decisão de arquitetura nem uma correção de bug — é uma escolha de implementação de teste dentro do escopo já assinado do plano, mas registrada aqui para transparência: se o teste tivesse comparado contra uma data hardcoded, ficaria frágil ao dia em que rodasse.

Nada foi acrescentado a `.planning/notes/decisoes-autonomas-v1.2.md` (nenhuma entrada nova, por não haver decisão de autonomia real a registrar — nem Regra 4, nem ambiguidade de plano).

## Deviations from Plan

Nenhum desvio de Regra 1/2/3/4. Comportamento, cobertura de teste e conteúdo de documentação exatamente como especificado no `11-03-PLAN.md`.

---

**Total deviations:** 0.
**Impact on plan:** Nenhum.

## Verificações adicionais pós-implementação

- Confirmado que `put_lifecycle.run_diario` nunca chama `options_provider`/`candle_provider`/`mydata_budget` — o guardião A4 é estrutural (leitura de fonte), e o comportamento (B1/B2/B3) nunca populou nada além de `candle_cache._CACHE` diretamente, sem passar por nenhum adaptador de rede.
- `test_b1` fecha com `pnlPorAcao == 5.35` (não um valor arredondado por acaso) — `round(6.5 - 1.15, 2)` bate exatamente com o cálculo manual, confirmando que `decidir()` não introduz nenhum erro de ponto flutuante perceptível no caminho feliz.
- O guardião de RED (Bloco C) foi executado de verdade nesta sessão (não é uma alegação): a saída literal com sentinela mostrou `1 failed, 14 passed` (o teste `test_a1...[caminho0]` — `put_lifecycle.py` — falhou; `put_suggestions.py` não tinha o sentinela, continuou passando), confirmando que o guardião de fato detecta o padrão proibido quando ele existe, não é um teste que sempre passa por acidente de asserção fraca.

## Issues Encountered

Nenhum bloqueio. `server/.venv` não existe dentro do worktree (mesmo achado recorrente dos planos anteriores) — usado o Python do `.venv` do clone principal (`/Users/acamerini/dev/bolsia/b3-agente/server/.venv/bin/python`) para os comandos `pytest` diretos; `scripts/executar.sh` resolve isso sozinho.

## User Setup Required

None. Nenhuma variável de ambiente de produção tocada (`B3_PUT_LIFECYCLE_HHMM`/`B3_PUT_LIFECYCLE_OFF` continuam não-definidas); `B3_OPTIONS_PROVIDER` nunca lido nem alterado neste plano (o guardião A4 prova estruturalmente que `put_lifecycle.py` nem menciona o nome dessa variável). Nenhum git push, nenhum deploy, nenhum branch remoto.

## Nota de dormência em produção (contrato de autonomia, item 5)

Com `B3_OPTIONS_PROVIDER=yahoo` (default de produção, intocado por este milestone), a ponte da Fase 10 nunca grava uma linha `armada` com proveniência completa (o contrato do Yahoo não publica `exerciseStyle`) — `put_suggestions` fica vazia em produção, e `put_lifecycle.run_diario` sempre devolve `{"linhas": 0, ...}`. **Todo requisito desta fase (PUTLIFE-01 a PUTLIFE-04) é provado por teste, não por dado de produção**, até o dia em que o seletor `B3_OPTIONS_PROVIDER` apontar para `mydata` (decisão de arquitetura/negócio explicitamente fora do escopo de v1.2). Isto está documentado em 3 lugares permanentes, não só nesta SUMMARY: ADR-022 Decisão 4, `docs/OPERACAO-ciclo-de-vida-put.md` §3, e (herdado) ADR-021 Decisão 3/`docs/OPERACAO-ponte-gatilho-put.md` §3 para a ponte que alimenta este ciclo de vida.

## Next Phase Readiness

- Este é o ÚLTIMO plano da Fase 11 e do milestone v1.2. Os 4 requisitos da fase (PUTLIFE-01..04) têm prova automatizada apontável (tabela acima).
- `server/tests/test_put_lifecycle_sem_carteira.py` é um guardião PERMANENTE — não se apaga; reversão deliberada atualiza o guardião com nota (mesma regra do CLAUDE.md do repositório para guardiões de teste).
- Suíte canônica validada 2x (exigência do contrato de autonomia): ambas `1674 passed, 1 skipped`, exit 0, 105 `.mjs` OK / 0 falhas.
- Pendências não-bloqueantes herdadas para o Alex revisar de manhã (não resolvidas nem agravadas por este plano): WR-01 (gate de orçamento não-atômico, `mydata_budget`) e as 3 notas "A revisitar" do ADR-022 (alargar o gatilho quando houver dado real; decisão de expor a medição; WR-01 repetido por visibilidade) — todas já registradas em `.planning/notes/decisoes-autonomas-v1.2.md` e no `STATE.md` por planos anteriores, nenhuma nova aqui.

---
*Phase: 11-ciclo-de-vida-e-monitoramento*
*Completed: 2026-08-28*

## Self-Check: PASSED

- FOUND: `server/tests/test_put_lifecycle_sem_carteira.py`
- FOUND: `docs/adr/022-ciclo-de-vida-da-sugestao-de-put.md`
- FOUND: `docs/OPERACAO-ciclo-de-vida-put.md`
- FOUND: commit `8a77dd6` (Task 1)
- FOUND: commit `63afe72` (Task 2)
