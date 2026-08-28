---
phase: 00-precondi-es
verified: 2026-08-28T12:00:00Z
status: passed
score: 13/13 must-haves verified
overrides_applied: 0
---

# Phase 0: Precondições Verification Report

**Phase Goal:** O ledger de sinais fecha sem 404 residual e o provedor de
opções mydata respeita um teto de taxa de requisições — destravando a
ponderação do ADR-017 (calculada sobre o ledger completo) e fechando o
achado WR-01 do 09-REVIEW.md antes de qualquer estrutura de opções nova
consumir a mesma chave mydata.
**Verified:** 2026-08-28
**Status:** passed
**Re-verification:** No — initial verification

**Context:** Phase executed fully unattended overnight under an autonomy
contract. A code review (`00-REVIEW.md`) found 1 Critical (CR-01:
un-normalized ticker used as ledger write key) and 1 Warning (WR-01: budget
gate check-then-debit not atomic under concurrency, pre-existing pattern
shared with `candle_provider`/`brapi_budget`, not introduced by this phase).
CR-01 was fixed post-review (commit `6e640dc`) with a guardian test. This
verification re-derives every claim from primary source — code, git log, and
live test execution — rather than trusting SUMMARY/REVIEW narrative.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Bootstrap varre os 74 tickers do universo sem 404 residual | ✓ VERIFIED | `00-01-SUMMARY.md` reports `erros: 0` on first dry-run pass; `docs/DIAGNOSTICO-tickers-ledger-2026-08-28.md` "Verificação de fechamento" section documents the run verbatim |
| 2 | Cada um dos 9 tickers (ELET3, BRFS3, ELET6, JBSS3, CRFB3, NTCO3, CPLE6, MRFG3, EMBR3) tem veredito com evidência — nunca some em silêncio | ✓ VERIFIED | Read `server/app/ledger_tickers.py` directly: `ALIASES = {"MRFG3": "MBRF3", "EMBR3": "EMBJ3"}` (2 entries); `EXCLUIDOS` has exactly 7 entries (`BRFS3, JBSS3, CRFB3, NTCO3, CPLE6, ELET3, ELET6`), each with a non-empty, dated, evidence-citing reason string. 2+7=9, matches claim exactly. `ELET3`/`ELET6` reasons carry the required `não resolvido em 2026-08-28:` prefix (INDETERMINADO case) |
| 3 | `scanner.DEFAULT_UNIVERSE` continua com os mesmos 74 símbolos (A-01, nenhuma superfície visível) | ✓ VERIFIED | `git diff origin/main..HEAD --stat -- server/app/scanner.py` empty — file untouched |
| 4 | Resolução de ticker isolada do universo visível, consumida só pelo bootstrap | ✓ VERIFIED | `server/app/ledger_tickers.py` is a standalone module imported only by `signal_ledger_bootstrap.py` (`from . import db, ledger_tickers, scanner, ...`); `resolver()` confirmed live: `resolver('PETR4')` → `('PETR4', None)` |
| 5 | Ticker excluído nunca toca a rede; ticker com alias busca pelo símbolo do alias mas grava sob o ticker do universo | ✓ VERIFIED | Read `executar()` (`signal_ledger_bootstrap.py:153-160`): excluded tickers never enter `tickers_ativos` (never scheduled for fetch); alias tickers pass `simbolo` (alias) to `carregar_candles` but `tk` (universe ticker) to `bootstrap_ticker` — confirmed at lines 162-172 |
| 6 | **CR-01 fix live**: ledger write key is normalized regardless of raw CLI input (`.SA` suffix, lowercase) | ✓ VERIFIED | Read `signal_ledger_bootstrap.py:154-155` directly (not just REVIEW.md claim): `tk = normalize_ticker(tk_bruto)` executes before `ledger_tickers.resolver(tk)`, and the normalized `tk` flows into `tickers_ativos`/`resumo["excluidos"]`. Guardian test `test_executar_ticker_bruto_nao_normalizado_grava_sob_chave_normalizada` exists in `server/tests/test_signal_ledger_bootstrap.py:327` and **passes** (ran live: `81 passed`) |
| 7 | Um pedido de cadeia de opções sem cota NÃO toca a rede | ✓ VERIFIED | Read `options_provider_mydata.py:155-171`: `_gate(2)` called after cache lookup, before any `mydata_client` call; on refusal, returns `_empty_payload(...)` directly, no `await mydata_client.*` reached. Test `test_sem_cota_devolve_degradado_sem_tocar_o_cliente` asserts `chamadas_venc == []` and `chamadas_chain == []` — ran live, passes |
| 8 | Sem cota, payload tem `providerStatus="degraded"`, cadeia vazia, contrato ADR-004 | ✓ VERIFIED | `_empty_payload()` (line 63-78) sets exactly this shape; test asserts `calls==[]`, `puts==[]`, `expirations==[]`, `source=="mydata"`, `"cota" in providerError` |
| 9 | Ciclo do agente sobre posição de opção continua rodando (não levanta, não trava) quando orçamento estoura | ✓ VERIFIED | Read `test_ciclo_com_orcamento_estourado_nao_trava_nem_executa` (`test_agent_options.py:249-274`) directly: asserts `r["executed"] == 0`, position still open (`len(...) == 1`), `chamadas == []`, no exception raised by `_run(...)`. Ran live, passes |
| 10 | Recusa por cota não é cacheada — janela do minuto libera, chamada seguinte serve dado real | ✓ VERIFIED | Code at line 164-171 explicitly skips the `_cache[key] = ...` write on refusal (contrast with all other exit paths, which do write). Test `test_recusa_por_cota_nao_e_cacheada` toggles `pode_gastar` False→True across two calls to the same key and asserts second call returns `providerStatus=="ok"` with populated `calls` — ran live, passes |
| 11 | Cadeia servida do cache de 300s não debita cota | ✓ VERIFIED | Gate check happens only after the cache-miss branch (`hit` check returns early at line 158-160, before `_gate`/`_debita` are ever reached); `test_cache_quente_nao_consulta_orcamento` — ran live, passes |
| 12 | `options_provider.get_options()` com `B3_OPTIONS_PROVIDER=mydata` respeita o mesmo gate; default continua `"yahoo"` | ✓ VERIFIED | Read `options_provider.py` directly: `_PROVEDORES` dispatch table unchanged logic (docstring-only diff), `provider_name()` returns `"yahoo"` when env unset — confirmed live: `python3 -c "...provider_name()"` → `yahoo`. `test_selector_mydata_sem_cota_degrada`/`test_selector_yahoo_nao_toca_orcamento_do_mydata` — ran live, pass |
| 13 | Suíte canônica (`bash scripts/executar.sh --testes`) fica verde | ✓ VERIFIED | Ran live (not trusted from SUMMARY): `bash scripts/executar.sh --testes` → exit 0, `1540 passed, 1 skipped` (backend), all `web/tests/*.mjs` `[OK]` |

**Score:** 13/13 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `docs/DIAGNOSTICO-tickers-ledger-2026-08-28.md` | Evidência bruta por ticker + veredito | ✓ VERIFIED | Exists, cites command executed, real JSON evidence blocks, all 9 tickers named with one of the 4 exact verdict words, plus a "Verificação de fechamento" section |
| `server/app/ledger_tickers.py` | `ALIASES`, `EXCLUIDOS`, `resolver()` | ✓ VERIFIED | All three exported, `set(ALIASES) & set(EXCLUIDOS)` disjoint (2 vs 7 entries, no overlap), substantive docstring documenting A-01/A-02 |
| `server/tests/test_ledger_tickers.py` | Offline coverage of resolver/disjunction/reason format | ✓ VERIFIED | Exists, exercised live, passes |
| `server/app/signal_ledger_bootstrap.py` | Retry + `ledger_tickers` integration + `excluidos` bucket + CR-01 fix | ✓ VERIFIED | All present and wired, confirmed by direct read + live test run |
| `server/app/options_provider_mydata.py` | Gate + debit before every mydata network call | ✓ VERIFIED | `_gate`/`_debita` defined and called at the exact positions the plan specifies (after cache lookup, before each `await mydata_client.*`) |
| `server/tests/test_options_provider_mydata.py` | Proof of block + degrade, not just existence | ✓ VERIFIED | 6 new tests, all with negative assertions (empty call lists), all pass live |
| `server/app/options_provider.py` | Selector docstring-only update | ✓ VERIFIED | `git diff` confirms no logic change; `_PROVEDORES`/`provider_name()` intact |
| `docs/adr/020-centralizacao-de-dados-no-mydata.md` | Additive closure note | ✓ VERIFIED | Contains `2026-08-28` dated note citing `_gate` and `B3_OPTIONS_PROVIDER`, diff is additive only |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `signal_ledger_bootstrap.py` | `ledger_tickers.py` | `ledger_tickers.resolver()` inside `executar()` | ✓ WIRED | 2 non-comment call sites confirmed by grep, matching acceptance criteria threshold |
| `signal_ledger_bootstrap.py` | `resumo['excluidos']` | Separate bucket, printed by CLI | ✓ WIRED | 7 non-comment occurrences (key init, append, `.get()`, CLI print block) |
| `options_provider_mydata.py` | `mydata_budget.py` | `pode_gastar()` before network, `debita()` before each call | ✓ WIRED | `pode_gastar` called once (in `_gate`), `_debita` defined+called twice (2 network call sites) — confirmed by direct grep and live behavioral tests |
| `options_provider.py` | `options_provider_mydata.py` | Dispatch by `B3_OPTIONS_PROVIDER`, gate inherited | ✓ WIRED | `_PROVEDORES["mydata"] = options_provider_mydata.get_options`; `test_selector_mydata_sem_cota_degrada` proves the gate is inherited through the selector |
| `agent.py` | `providerStatus='degraded'` | `_avaliar_opcoes` ignores non-'ok' status | ✓ WIRED | No `agent.py` changes needed (plan correctly identified this was already safe); proven by `test_ciclo_com_orcamento_estourado_nao_trava_nem_executa` running the real `run_cycle_for` path |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| CR-01 fix normalizes ledger write key | `python3 -m pytest tests/test_signal_ledger_bootstrap.py -k test_executar_ticker_bruto_nao_normalizado_grava_sob_chave_normalizada -q` (run as part of full file) | Included in `81 passed` run | ✓ PASS |
| `resolver('PETR4')` passthrough | `python3 -c "from app import ledger_tickers as m; print(m.resolver('PETR4'))"` | `('PETR4', None)` | ✓ PASS |
| `provider_name()` default | `python3 -c "from app import options_provider as p; print(p.provider_name())"` | `yahoo` | ✓ PASS |
| Gate ordering (cache before gate) | `python3 -c "...s.index('_cache.get') < s.index('_gate(')..."` | `OK order` | ✓ PASS |
| All targeted phase-0 tests | `pytest tests/test_signal_ledger_bootstrap.py tests/test_ledger_tickers.py tests/test_options_provider_mydata.py tests/test_options_provider.py tests/test_agent_options.py -q` | `81 passed` | ✓ PASS |
| Canonical suite | `bash scripts/executar.sh --testes` | exit 0, `1540 passed, 1 skipped`, all `.mjs` OK | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| LEDGER-01 | 00-01-PLAN.md | 9 tickers 404 investigados, ledger fecha sem erro 404 residual | ✓ SATISFIED | `ledger_tickers.py` + retry + `erros: 0` on real 74-ticker dry-run |
| OPTGATE-01 | 00-02-PLAN.md | `options_provider_mydata.py`/`options_provider.py` respeitam teto de requisições, fecha WR-01 do 09-REVIEW | ✓ SATISFIED | Gate/debit wired at both files, agent cycle survives overflow, 9 behavioral tests pass |

Both requirement IDs are declared in `.planning/REQUIREMENTS.md` (lines 14-22,
83-84) mapped to Phase 0 — no orphaned requirements found. **Note:**
`REQUIREMENTS.md` checkboxes still show `[ ]`/`Status: Pending` for both IDs.
This is **not a functional gap** — established project convention (confirmed
via `git log -- .planning/REQUIREMENTS.md`, e.g. `a745787`, `ad18db7`) is that
a phase's `docs(phase-N): complete phase execution` commit flips these
checkboxes as the final step of phase closure, which had not yet run at the
time of this verification. Informational only.

### Anti-Patterns Found

None. Scanned all 10 files modified by this phase for `TBD|FIXME|XXX|TODO|HACK|PLACEHOLDER` —
the only matches are Portuguese prose using the word "TODO" as an adjective
("TODO ramo deste arquivo" = "every branch of this file"), not debt markers.
No empty implementations, no hardcoded-empty stubs in production code paths.

### Guardrail Compliance (milestone-wide, re-verified independently)

| Guardrail | Status | Evidence |
|-----------|--------|----------|
| No push to origin | ✓ VERIFIED | `git status`: "ahead of origin/main by 22 commits", no push executed |
| No deploy / no prod env var change | ✓ VERIFIED | No `railway.json`/`Procfile` in diff |
| `B3_OPTIONS_PROVIDER` never altered outside test scope | ✓ VERIFIED | `provider_name()` confirmed live to return `yahoo`; only `monkeypatch.setenv` usages found |
| `scanner.py`/`yahoo.py`/`mydata_budget.py` untouched | ✓ VERIFIED | `git diff origin/main..HEAD --stat` for these 3 files is empty |
| No visible surface (`web/src/`, `web-admin/src/`) touched | ✓ VERIFIED | Absent from diff stat |
| No short/sold-option support introduced | ✓ VERIFIED | No such code found in diff |

### Human Verification Required

None. This phase is entirely backend/offline (no UI surface, no live-market
dependency, no visual/real-time behavior) and every claim was independently
reproducible via direct code read + live test execution.

### Gaps Summary

No blocking gaps. One item worth carrying forward as a **non-blocking,
informational note** (not a gap — the phase's own success criteria do not
require concurrency-safety, and this pattern pre-dates the phase):

**WR-01 residual scope — budget gate is not atomic under concurrency.**
`00-REVIEW.md` documents that `mydata_budget.pode_gastar()`/`debita()` has no
lock between check and mutation, so two concurrent requests (e.g. an HTTP
`/api/options` call racing the agent's `scheduler_loop`) could both observe
headroom before either debits, jointly overspending the shared 60/min·2000/day
cap. This is an accepted, pre-existing pattern shared with
`candle_provider`/`brapi_budget` (not introduced by this phase — this phase
duplicated an existing gap into a second consumer, it did not create the gap
itself). The reviewer explicitly dispositioned it as "not blocking for this
phase" and recommended a follow-up (`asyncio.Lock`-guarded reserve operation
in `mydata_budget.py`, shared by both consumers). Surfacing this here per the
escalation-gate pattern so the human decides whether to open a follow-up
ticket before Phase 10 (which will add a second autonomous caller —
`scheduler_loop`'s put-selection hook — into the same race window) or accept
it as-is. Does not affect this phase's `passed` status: the roadmap Success
Criteria for Phase 0 make no concurrency-safety claim, and OPTGATE-01's own
must-haves list only requires mirroring `candle_provider`'s pattern, which
this change does correctly (including inheriting its known limitation).

---

_Verified: 2026-08-28_
_Verifier: Claude (gsd-verifier)_
