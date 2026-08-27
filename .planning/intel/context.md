# Context (from DOCs)

8 DOC-classified documents were ingested. Notes below are organized by topic, each block attributed to its source. Excerpts are quoted where load-bearing; otherwise summarized.

(Note: `docs/prompts/admin-mobile-otimizado.md` was deliberately excluded from this ingest batch per product-owner decision (2026-08-27), before this run started — its classification JSON was moved out of `CLASSIFICATIONS_DIR` (to `_excluded/`), so it was never loaded, never classified in this run, and is not one of the 32 documents synthesized here. This is a scope decision, not a routing failure or data loss — see `../INGEST-CONFLICTS.md` [INFO] for the audit note. It is not surfaced as a BLOCKER in this run.)

---

## Topic: Product overview / user-facing modes

- source: `docs/AJUDA.md` ("Boris+ — Como funciona", mirrors the in-app Perfil → Como funciona screen)
  > "Boris+ é um app educacional de análise técnica da B3. Ele varre o mercado, mostra oportunidades de estudo e deixa você simular uma carteira — tudo com dinheiro fictício. Nada aqui é ordem real nem recomendação personalizada: nenhuma ordem é enviada à corretora."
  - Two modes: **Modo Estudo** ("um professor: explica o porquê de cada setup") and **Modo Operador** ("uma mesa de operações: dá o plano objetivo"). Switch in Perfil → Modo de trabalho.
  - Radar/Mesa de oportunidades: Veredito, Confluência (explicitly: "Mede aderência ao padrão em dados passados, **não** probabilidade de resultado" — user-facing language already matches the ADR-009/016 finding that confluência ≠ statistical edge).
  - Fundamento (A/B/C): "um filtro de qualidade, nunca um gatilho de compra" — valuation, rentabilidade, solidez; "sem dado, o app mostra 'sem dado' — nunca inventa."
  - Eficiência da IA: 10-pregão outcome tracking, "autoavaliação sobre o passado, não garantia de futuro," exportable as CSV.

## Topic: Technical architecture (map, ADRs are authoritative on conflict)

- source: `docs/ARQUITETURA.md` (last revised 2026-08-06; explicitly self-declares: "Quando este texto e um ADR divergirem, o ADR vence — e este arquivo ganha uma correção.")
  - "Um monólito FastAPI no Railway que serve API e front web da mesma origem... **o backend calcula, a LLM interpreta, a pessoa decide**" (Princípio 1).
  - Topology: iPhone (Capacitor/WKWebView, bundle embedded, `deviceStore` local-first) + browser PWA (`serverStore`) → Railway (`rootDirectory=/server`) → FastAPI + SQLite → Yahoo/brapi.
  - Front: single large `web/src/App.jsx` by design (navigating modules costs more than scrolling one file; `.mjs` guardians assert contract by regex over that source). Two stores need parity (`serverStore`/`deviceStore`); new method/field must enter both.
  - Backend: agent's internal loop (`agent.py`) drives radar diário + intraday pass, no external cron. LLM (`llm.py`): do not touch `llm._CHARS_POR_TOKEN` — global, calibrated (cross-reference: ADR-007's cache-margin discussion explains why).
  - Camada de entendimento: 3 degraus (conceitos determinísticos → pet → assistente LLM), grátis sempre responde primeiro.
  - Operational kill-switches: `B3_DIDATICA_OFF`, `B3_ASSISTENTE_OFF`, `B3_TIMING_PUSH_KILL`, `B3_ASSISTENTE_TETO_BRL`.
  - Delivery: `entregar.sh` runs suítes → build+publish `web_dist` → commit+push → `cap sync ios` → Xcode; build-before-commit order is mandatory (a past incident left production web one release behind while `/api/health` reported healthy).
  - Fronteiras/pendências listed at time of writing: MyData integration pending; Opções v2 (ADRs 003/004/005) backend+UI ready but no real premium source; `greek_score` dead code awaiting decision; pet voice measured in browser only, pending WKWebView measurement (see `plano-voz-nativa-ios.md` below — this was later addressed).

## Topic: Radar ranking refactor (ADR-009 delivery mechanics)

- source: `docs/refactor/HANDOFF-claude-code.md` (execution handoff that produced ADR-009)
  - Runbook for applying "Refactor A" (regime.py + scanner.py integration) via a specific Claude Code prompt, explicit ordering: apply patch → run canonical suite (both pytest + `.mjs`) → confirm no contract regression (`confluencia`/`veredito`/`plano`/`spark` intact, new fields present) → write `docs/adr/009-eixo-de-selecao.md`.
  - Explicitly deferred to "Fase A parte 2": the family-guardrail prompt addition (ESPEC-A §6) and anything from ESPEC-B (validation depends on this phase being merged and `regime` accumulating weeks of data before B2 downgrade logic is safe).

## Topic: Yahoo intraday feasibility measurement (input to ADR-001)

- source: `docs/MEDICAO-Yahoo-Intraday-2026-07-30.md` (empirical benchmark, pregão fechado, IP residencial + separately from Railway IP)
  - Interval/window limits measured directly: `1m`→7d, `2m`/`5m`/`15m`/`30m`/`90m`→1mo, `60m`→2y, `1d`→max. **Trap measured**: `range=max` with ANY intraday interval silently degrades to HTTP 200 with monthly candles (`dataGranularity:"1mo"`) — mislabeled as intraday. (Cross-reference: this exact bug reappears and is fixed inside `ADR-016`'s Adendo 3, and the fix is generalized into `yahoo.get_history` under `ADR-017`.)
  - Universe coverage: 65/74 tickers served at any interval including `1d`; the same 9 tickers (ELET3, ELET6, JBSS3, EMBR3, CPLE6, CRFB3, NTCO3, MRFG3, BRFS3) 404 everywhere — "não é limitação do intraday — é um buraco que já existe na produção de hoje."
  - Latency does not vary with granularity (network-bound, not payload-bound): p50 ~175-200ms residential.
  - Burst test: 1,300 requests in 17s from residential IP, zero non-200; from Railway's `sfo` datacenter IP (measured separately, §8): 65 tickers in 0.45s at concurrency 8, p50 50ms, zero errors across 266 requests — **datacenter IP is 3.5× faster, not penalized**.
  - Cost conclusion: ~US$1/month infrastructure; the real cost driver is risk (no contract/SLA/ToS-vs-commercial-use), not money.
  - Explicitly flagged as unresolved at the time this doc was written: feed delay during live trading hours (resolved the next day, becomes ADR-001 Decision 2) and whether the "bolsai" vendor (already used for fundamentals) has undocumented intraday.

## Topic: Signal ledger bootstrap operations (ADR-017 Bloco 1 runbook)

- source: `docs/OPERACAO-ledger-de-sinais.md`
  - Clarifies the retrospective/prospective distinction that also underlies ADR-015: the signal ledger is BACKTEST (retrospective replay over closed candles), `analysis_outcomes` is FORWARD (prospective, what the LLM said live). "Misturar os dois números produziria uma conclusão sem sentido."
  - Bootstrap (`python -m app.signal_ledger_bootstrap`) is manual, run only in 3 cases: first install, disaster recovery, or setup-family change (`--reset`). It is NOT a cron job — the daily incremental job (`signal_ledger_job`) is separate and automatic, hooked into `scheduler_loop`.
  - Runs outside `scheduler_loop` deliberately — explicit precedent cited: a kill-switch incident once silently halted execution for 2.5 days because heartbeat masked the problem; the bootstrap is a separate process specifically to never compete with that loop.
  - Cost: 74 Yahoo requests total (zero brapi budget consumed — ADR-008 exclusivity confirmed here), ~126k signals evaluated.
  - Production Railway path requires `/opt/venv/bin/python3` explicitly (bare `python3` lacks project deps).

## Topic: appMode / Operador UX incident and fixes (predates and is superseded by later fixes)

- source: `docs/auditoria-controle-ordens-parametros.md` (2026-08-07, root-cause audit of "não me deixa mais selecionar o modo executar")
  - Root cause: NOT a regression — `config.appMode` was correctly `"estudo"`, and the "Executar" trava is working as designed (Fase A). The real bug: the trava is **mute** — `title` attribute is the only explanation and doesn't fire on touch (no hover in WKWebView/iOS), and the real toggle (`appMode`) lives in a completely different screen (Perfil → Modo de trabalho) with no link from where the user is.
  - Structural finding: two different things are both called "Operador" in the UI — the "Operador IA" tab (agent config panel) vs. "Modo Operador" (the actual master switch, `config.appMode`) — same word, two places, one secretly controls the other. `appMode === "operador"` was independently recomputed in 11+ places in `App.jsx` at the time of writing.
  - Three unrelated data bugs fixed the same day, same root-cause category ("um estado importante mudava num lugar que outro lugar não enxergava"): stop/alvo silently saved `null` on blur; iOS `deviceStore` buy/sell/putPosition were 100% local, never syncing to server; agent cycle only ran on the scheduled interval (up to 60min), missing freshly-armed triggers.
  - **Status as of this document (2026-08-07): items 1-4 done same day (F10-20260807-07/08); item 5 (single source of truth for `appMode` across all 11+ read sites) marked PARTIAL** — `ctx.operador` created and `AgenteScreen` migrated, but the other 9+ locations were explicitly NOT migrated in this round ("escopo maior, não migrado nesta rodada").
  - Cross-reference: `PROJECT.md`'s Validated section claims this full-migration is done ("Migração mecânica de 7+3 leituras redundantes de `appMode` para a fonte única `ctx.operador`", per `MILESTONES.md` v1.1 entry) — this appears to be a LATER, separate completion (v1.1 Fase 5) that finished what this 2026-08-07 document left partial. Not a contradiction — just note the two documents describe different points in time of the same migration; no conflict entry needed since MILESTONES.md (dated later, v1.1 shipped 2026-08-23) supersedes this doc's "PARTIAL" status chronologically.

## Topic: Didactic-layer inventory (input to ADR-006)

- source: `docs/didatica-inventario.md` (2026-08-05, read of `web/src/App.jsx`)
  - Found 18 undexplained assertions on the single `AtivoCard`, most in jargon — P1 (can't act correctly without understanding) items: manchete/veredito, TimingBadge (gatilho, barra15m, r), chip confluência, chip fundamento, PlanRuler (stop/alvo), R:R line, sizing CTA.
  - Conclusion driving ADR-006 design: `gatilho` is the calibration anchor (P1, appears everywhere, pulls in `r` and `barra15m`); the proactive/first-time explanation path cannot live in a list (would fire 6× or randomly — one Watchlist has 6 cards); a single affordance (tap the term) must serve all 18 assertions, not 18 different interactions; `alvo` deliberately has no own "?" (only reachable via "veja também" from `stop`/`r` — it only makes sense in relation to stop).
  - Priority ranking for follow-up: card first, then "Operador IA" screen next (only screen where not understanding has a real simulated-money consequence) — ahead of Radar.

## Topic: Boris pet voice on native iOS (bugfix plan, pending device verification)

- source: `docs/plano-voz-nativa-ios.md` ("Status: aguardando aprovação")
  - Root cause confirmed in code, not assumed: `Boris.jsx`'s own header comment already documented that WKWebView doesn't trust `speechSynthesis` and that native TTS should be used, but the ported component kept calling `window.speechSynthesis` directly via the legacy `falarTexto` function, only wrapping mouth animation (`boris.talk()/.stop()`) around it. `@capacitor-community/text-to-speech` was confirmed NOT installed.
  - Planned fix: install the plugin, add a routing helper (`Capacitor.isNativePlatform()` branches to native TTS vs. unchanged `falarTexto` for PWA/browser), redirect both call sites (`PetSheet.ouvir()`, `BorisChat.enviarAgora()`), add native `calarVoz()` equivalent, `cap sync ios`.
  - **Explicitly self-limited**: "Eu não tenho como testar áudio de verdade no WKWebView — não tenho iPhone nem TestFlight." The author can guarantee compilation, plugin installation, and static branch-logic correctness, but real on-device audio verification is deferred to the human (Alex), consistent with `ARQUITETURA.md`'s "Voz do pet: medida no navegador; pendente de medição no WKWebView real" pendência — this document is the fix attempt for that exact open item, not yet confirmed closed.
