# Constraints (from SPECs)

5 SPEC-classified documents were ingested. One entry per constraint document below (type breakdown noted per entry).

---

## ESPEC-A — Inversão do eixo de seleção do Radar (regime + momentum relativo)
- source: `docs/refactor/ESPEC-A-eixo-selecao.md`
- type: protocol / api-contract (ranking algorithm contract for `/api/scan`)
- status: "patch aplicável, testes passando (10/10)" — implements ADR-009 (locked)
- content:
  - Problem statement: `scanner.run_scan` sorted by `(-confluencia, -score_tecnico, ticker)`; confluência measures pattern adherence, not statistical edge.
  - New module `regime.py` (pure) API: `classificar(snap) -> {regime, direcao, forca, adx14, base, confiavel}`; `ranquear(resultados, snaps_por_ticker) -> resultados` annotating `regime`, `momentumRelPct`, `momentumParcial`, `gatilhoAlinhado`, `radarScore`.
  - `scanner.run_scan` patch: 3 hunks — import `regime`, build `snaps` dict per symbol, replace `results.sort(...)` with `regime.ranquear(results, snaps)`.
  - Degradation contract preserved: window <200 candles → `base="sma50"`, `confiavel=False`; missing `change252` → `momentumParcial=True`, rank by `change63` only; regime `indefinido` → tier 0, never promoted to compensate for missing data.
  - Guardrail addition (pending Alex decision, TODO): system prompt for N2 must state that setups of the SAME family (e.g., RSI/stochastic/MACD) do not stack as independent confirmations — must be mirrored byte-for-byte in `server/app/defaults.py` ↔ `web/src/catalog.js` (paridade guardião trava).
  - Acceptance criteria: `bash scripts/executar.sh --testes` verde; `test_regime.py` 10/10; Radar keeps `confluencia`/`veredito`/`plano`/`spark` in every result (no contract regression); an asset in strong uptrend with high relative momentum and low confluência must rank above a lateral asset with confluência 90 (inverse of pre-patch behavior); interlock with ESPEC-B — `r["regime"]["regime"]` is the field ESPEC-B persists and segments by.
  - Residual risk: percentile is relative to the SCANNED universe (small/biased universe → biased ranking, assumes IBOV+-scale universe); `radarScore` does not yet incorporate measured expectancy (that is ESPEC-B's job).

## ESPEC-B — Fechar o loop de validação por regime
- source: `docs/refactor/ESPEC-B-validacao-regime.md`
- type: schema / api-contract (extends `analysis_outcomes.py` persistence + aggregation contract)
- status: spec only, depends on ESPEC-A (regime field) being merged first
- content:
  - Delta 1: `registrar()` in `analysis_outcomes.py` gains new optional param `regime=None` (from `regime.classificar()["regime"]`), persisted per analysis at the moment of analysis (not at outcome-resolution time). Call sites `main.py:865` (scanDeep/N1) and `main.py:969` (analyze/N2) pass `regime=snap["regime"]["regime"]`. Pre-existing records get `regime=None` → fall into a `"—"` bucket, no breakage.
  - Delta 2: `compute_stats` segments by `porRegime` and `porSetupRegime`, reusing existing `_celula` (with `MIN_N` guard already in place).
  - Delta 3: new pure function `historico_do_par(stats, setup, regime) -> {status, expectanciaR, n}` — status ∈ `favoravel|desfavoravel|neutro|sem_dados`. Two consumers, both non-destructive: **B1** (annotation only — UI shows `historicoRegime`, zero reorder risk) enters first; **B2** (rebaixamento — `regime.ranquear` applies a ceiling on `radarScore` when `desfavoravel` AND `n ≥ MIN_N`) enters only after sample accumulates.
  - Guardrail (non-negotiable, CVM): expectância medida is descriptive/educational only, never a prediction; every surface showing `expectanciaR`/`historicoRegime` carries the disclaimer and fixed vocabulary ("resultado medido em leituras passadas", never "vai dar X%"); samples below `MIN_N` never render as a percentage; "past favorable ≠ future guarantee" text is mandatory.
  - Acceptance criteria: `compute_stats` returns `porRegime`/`porSetupRegime` with sub-`MIN_N` cells suppressed from percentage display; old `regime=None` records don't break aggregation; `historico_do_par` is pure and unit-tested (all 4 status branches); B1 annotates without reordering; B2 only downgrades with `n ≥ MIN_N` and always with disclaimer.
  - Sequencing mandated: Delta 1+2 → `historico_do_par`+tests → B1 (UI annotation) → B2 (ranking downgrade), B2 explicitly gated on sufficient sample to avoid reordering on noise.

## MEDIÇÃO — brapi plano gratuito com token real (Fase 0 do qa/43)
- source: `docs/MEDICAO-Brapi-2026-08-11.md`
- type: api-contract (empirical constraint report that establishes binding integration rules for `candle_provider.py`)
- status: measurement, explicitly framed as deltas over ADR-008 — **if content conflicts with ADR-008, ADR-008 is the higher-precedence source of record** (per the document's own framing)
- content:
  - Confirmed via real token spike (2026-08-11, 8 requests consumed, out-of-market-hours): quota 15,000 confirmed via `x-ratelimit-limit` header, reset window NOT exposed in headers (presumed monthly, needs confirmation from account panel); **1 ticker per request** (else `QUOTES_PER_REQUEST_EXCEEDED`); **only `interval=1d`** on free plan (else `INVALID_INTERVAL`); **max `range=3mo`** (else `INVALID_RANGE`; allowed: 1d/5d/1mo/3mo); **a rejected (400) request DEBITS quota** — client-side validation of interval/range MUST precede any brapi call, no "try and fall back on error"; `close` ≠ `adjustedClose` diverges in 25/62 candles of ITSA4 (3mo) — confirms "different source = replacement, never merge" for adjusted series; two distinct error envelope shapes (plan-violation `{error,message,code}` vs. Zod validation `{success:false,error:{issues:[...]}}}`).
  - Design consequence declared: warmup/long-history stays on Yahoo permanently (free plan has no `1y`/`2y`); brapi free serves spot + daily delta up to 3mo only; `x-ratelimit-remaining` should be exposed alongside the local budget counter in `/api/status` (header is ground truth, local counter is the prediction).
  - Open/pending at time of writing: real spot delay in live trading hours (measurement was out-of-hours); quota reset window (monthly vs. daily) unconfirmed.
  - Gate outcome: "aprovado com ressalva" — architecture (spot + delta ≤3mo on brapi, everything else Yahoo) stands; the ressalva (spot delay) only affects spot-slice TTL, not the direction of the decision.

## Plano — Operador IA: separação Estudo/Operador e entrada automática
- source: `docs/plano-operador-entrada-e-modos.md`
- type: protocol (agent execution-mode contract + entrada-automática mechanics)
- status: "Status: aguardando aprovação" (2026-08-07) — classifier notes contains a "Decisões fechadas (aprovadas pelo Alex em 2026-08-07)" section (D1-D6) that reads as quasi-locked; treat as near-locked constraints per classifier recommendation, though the document as a whole is not an ADR
- content — Decisões fechadas (D1-D6):
  - **D1**: backend forces `mode="sinalizar"` whenever `appMode != "operador"`, silently, regardless of what's saved (not a user preference in that case — a hard trava, both on read via `agent_params` and on write via `set_agent`).
  - **D2**: entrada automática shares the SAME `maxOpsDia` ceiling already used for exits (no separate `maxEntradasDia`).
  - **D3**: % of cash for auto-entry is configurable per account, with an absolute backend-enforced ceiling (never accepts above the ceiling even if the client sends more) — same spirit as `MAX_ALVO_EXTENSOES` not being client-configurable.
  - **D4**: reuse existing `allocPct` field ("Alocação por operação," 1-20%, default 5%, currently decorative/unread by `agent_params()`) instead of creating a new field.
  - **D5**: only the BUY side is auto-executable — `store.py` has no short position; a `VENDER` plan stays informational (push) only, in any mode.
  - **D6** (explicitly out of scope): no changes to the `autonomous`/"Modo local" legacy toggle; no general cleanup of the Operador screen.
  - Sizing rule (Fase B): `orcamento = cash * (allocPct/100)`; `qty = (orcamento // price // 100) * 100` — rounds DOWN, never rounds up past the % ceiling; if `qty < 100`, logs a warn event and does NOT execute (no forcing a lot that exceeds the promised %).
  - Dedup rule: when auto-entry EXECUTES for a ticker+day, it marks that ticker as `avisados` in `timing_watch` state — prevents a "nothing was bought" push from competing with the real buy push in the same cycle.
  - Coupling rule (Fase A): writing `mode="executar"` via `set_agent` also writes `serverEnabled=True` if not already true — eliminates the ambiguous "want to execute but only protected with the app open" state (the bug's primary hypothesis).
- relationship to ADR-017 (locked, later, 2026-08-20/21): complementary, not conflicting. This document defines the base entrada-automática mechanics (sizing, mode gating, dedup); ADR-017 Adendo 2 adds an additional eligibility gate (`elegivel is True` per setup×lado from the signal ledger) on top of this same code path — see `INGEST-CONFLICTS.md` [INFO].
- explicitly out of scope: cleanup of `autonomous`/"Modo local"; any change to short positions; real-money Modo Operador (`PROPOSTA-MODO-OPERADOR.md`) — this plan is entirely about the simulated wallet.

## v2 — Opções como classe de primeira ordem
- source: `docs/v2-opcoes-proposta.md`
- type: schema + api-contract (data model, UX contract, and agent-loop behavior for options as a first-class layer)
- status: "implementado, aguardando deploy (2026-08-04)" — backend/UI coded and locally verified, not committed/deployed at time of writing; the three ADRs it names (003/004/005) have since been written and locked (see `decisions.md`)
- content:
  - Product decisions already locked before the panel (not reopened): options are a LAYER inside the asset card (not a sibling tab); scope of operation is BUY ONLY of call/put à seco (1 leg); options appear in BOTH modes (Estudo/Operador) with the same vocabulary treatment as stocks.
  - UX contract: collapsed line in card footer (`⚡ opções · call 38 · R$ 0,72 · 24 dias ▾`), replacing the old isolated "Opções ▸" button. Expansion = "A acoplado" (single control; the asset block auto-shrinks to a persistent spine carrying stop/alvo/move-dia/veredito, never fully hiding — Principle 5/9 requires the user be able to VERIFY the coherence check, not just trust a label). Only 1 contract open at a time (accordion). Discoverability gated on a liquidity flag from the backend (no loud badge). 5 above-the-fold fields: cost/risk (premium×100), breakeven distance + days to expiration (reuses `PlanRuler`), does-the-underlying's-trend-support-the-direction (never contradicts the stock's own analysis), can-you-exit (3-state liquidity seal), cost-of-waiting (theta as %/week, never raw greek). Full greeks/BSM/IV-vs-HV go to "Aprofundar."
  - Data model: `optionPositions` shape (see `decisions.md` ADR-003 for the frozen schema) — this document is the source proposal ADR-003/004/005 were extracted from.
  - Agent-loop contract (`agent.py` `_run_cycle_inner`): option quote resolution needs a new getter keyed by `(underlying, expiration)` (1 fetch per expiration, not per contract); trailing (F2) falls back to `_percentual()` for options (ATR is in underlying R$, incompatible unit with premium) — monotonicity survives, but theta can trigger the stop via pure decay, must be named in the Diário; alvo dinâmico (F3) returns `(None, None)` for options in v2 (no extension); expiration-close branch is mandatory in BOTH server (`agent.py`) and iOS foreground (`persistence.js`) paths to avoid worsening the pre-existing 5-path divergence in position closing.
  - `analysis_outcomes.py`: explicit decision NOT to measure option R-multiple in v2 (would need historical premium series, unavailable — COTAHIST redistribution restriction); only the underlying's directional thesis continues to be measured.
  - Cost table: layer in card (Watchlist+Radar) = zero new fetch by default; full chain overlay = 1 fetch per ticker/expiration, cached 300s; expiration-close branch = marginal (1 date comparison per open option position, no extra fetch).
  - Explicitly out of v2: multi-leg/spreads (v3); early exercise/assignment; measuring option P&L in `analysis_outcomes.py`; `CarteiraScreen`/Posições layer (that screen doesn't use `AtivoCard` yet — reconciliation incomplete, not blocked by options); IV rank/percentile (no historical IV series); `greek_score` fix (found dead/hardcoded at 50, filed as separate item).
  - Verification limitation noted at time of writing: Yahoo's options chain was returning empty for ALL tested tickers at verification time — full flow verified with mocked network response in-browser; the gate itself (blocking on bad data) was verified against the real backend.
