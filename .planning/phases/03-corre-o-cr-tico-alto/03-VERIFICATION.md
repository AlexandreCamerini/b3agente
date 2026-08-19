---
phase: 03-corre-o-cr-tico-alto
verified: 2026-08-19T04:28:51Z
status: human_needed
score: 10/10 must-haves verified (code-level); 2 human-check items outstanding
human_verification:
  - test: "Abrir a tela 'Operador IA' (app consumidor, Modo Operador) e observar o card de status de 3 badges no topo."
    expected: "O card aparece no topo, antes do título 'Operador IA'. Trocar o Modo do app em Perfil e voltar move o badge 1 ('Modo do app') e o badge 3 ('Executar/sinalizar') JUNTOS. Ligar/desligar o toggle 'Operador no servidor' no card-herói move o badge 2 ('Operador no servidor') e o rótulo ATIVO/INATIVO do card-herói NA MESMA direção — nunca em direções opostas."
    why_human: "Comportamento reativo entre dois componentes React (card novo + card-herói) e navegação entre telas (AgenteScreen ↔ Perfil) — não verificável por grep/leitura estática. Este item foi explicitamente registrado como human-check pendente no PLAN 03-03 Task 2 (`<verify><human-check>`) e no SUMMARY 03-03 ('não executável neste ambiente... delegar ao Alex antes do deploy'), mas NÃO aparece nos 7 passos verificados no checkpoint humano de 03-06 Task 3 (que cobriu Fonte/orçamento/ticker inválido/KPIs/kill-switches/'Ligado há'/Custos, mas não a tela Operador IA)."
  - test: "No portal admin, com uma conta que tem `execucao_automatica.ver` mas NÃO tem `execucao_automatica.controlar`, abrir a aba Automação e observar o box 'Kill-switch do push de gatilho (timing_watch)'."
    expected: "O box mostra o estado (Kv 'Estado vigente') mas o botão de alternância é substituído pela mensagem 'Sem permissão para alternar (requer execucao_automatica.controlar).' — nenhum controle interativo aparece para essa conta."
    why_human: "Comportamento condicional de UI dependente de RBAC real (papel da conta autenticada) — não verificável por leitura estática do componente isoladamente. Este item consta explicitamente na seção de verificação humana do PLAN 03-05 ('confirmar que uma conta sem execucao_automatica.controlar vê a mensagem de sem permissão') mas não aparece nos 7 passos cobertos pelo checkpoint de 03-06 Task 3."
---

# Phase 3: Correção Crítico + Alto — Verification Report

**Phase Goal:** As 2 violações de princípio (dado de mercado com proveniência
enganosa ou opaca) e os 8 achados Alto (erro cru vazando detalhe interno,
guardiões estruturais que não travam a classe do erro, gating comercial
inerte, kill-switches sem visibilidade operacional) deixam de ser risco
silencioso.

**Verified:** 2026-08-19T04:28:51Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

All 10 requirement-level truths were verified directly against the codebase
(source reading + running the actual guardian tests + running the full
backend suite + both `vite build`s), not from SUMMARY.md narrative.

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `TechnicalModal` shows real source (brapi/Yahoo), never fixed "Yahoo Finance" (FIX-C11) | ✓ VERIFIED | `web/src/App.jsx:1556` reads `data.source ? FONTE_LABEL(data.source) : "—"`; `grep -c "Yahoo Finance" web/src/App.jsx` = 0; `server/app/technical_snapshot.py:196` propagates `hist.get("source")`; `server/app/main.py:1117` puts `"degradado"` in payload |
| 2 | Degraded budget state (>80%, TTL 3×) surfaces to user/admin, not silence (FIX-C30) | ✓ VERIFIED | `web/src/App.jsx:1557` renders warn-colored qualifier when `data.degradado`; `web-admin` `FonteDadosScreen` line 5458 renders "estado do orçamento: degradado (TTL 3×)" / "normal" from `orc.fatias.spot.degradado` |
| 3 | Buy/sell invalid ticker returns clean 502 error, no leaked URL/param (FIX-C12) | ✓ VERIFIED | `server/app/candle_provider.py` `get_quote()` wraps both branches in `try/except QuoteUnavailable: raise` / `except Exception: return {"error": "sem cotação (falha do provedor de dados)"}` — no `str(e)` interpolated |
| 4 | Generic guardian test fails on any undocumented store-method asymmetry (FIX-C20) | ✓ VERIFIED | `web/tests/test_fase3_paridade_stores_generica.mjs` executed — passes; extracts 60/60 methods from both stores, allowlist for the one documented exception (`_setDeviceScope`) |
| 5 | Single status card summarizing the 3 order-trigger switches at top of "Operador IA" (FIX-C19) | ✓ VERIFIED | `web/src/App.jsx:3845-3872` — card is the first element of `AgenteScreen`'s return, before the `<h1>`; reads `operador`, `ag.serverEnabled && logged`, `modoEfetivo` (the same canonical sources as the hero card); read-only (only `onClick` is `A.go("perfil")`); old partial strip absorbed — `grep -c "Modo do app:" web/src/App.jsx` = 1 |
| 6 | `can_add_ticker`/`can_analyze` resolve the real user plan via `current_plan(user)`, not global `ACTIVE_PLAN` (FIX-C31) | ✓ VERIFIED | `server/app/main.py:111` `_plano_do_escopo()`, called at lines 973, 422; fail-closed on unknown plan/DB failure (tests confirm) |
| 7 | `can_analyze` and `metering.check` no longer duplicate/race the same AI quota in one request (FIX-C32) | ✓ VERIFIED | `server/app/main.py:409` `_gate_analise()` is the single decision point, called from both analysis routes (lines 1351, 1491); `grep -c 'plan\.can_analyze('` in main.py = 1 (inside `_gate_analise`) |
| 8 | Admin portal shows 2nd kill-switch (`timing_watch`) state, runtime toggle, no redeploy needed (FIX-C35) | ✓ VERIFIED | `server/app/timing_watch.py` gained memory→DB→env pattern (`kill_switch_on`, `set_kill_switch`, `configure_db`); `GET`/`PUT /api/admin/timing-watch/kill-switch` at `main.py:743/748`; `TimingWatchKillSwitchBox` + KPI "PUSH DO GATILHO" in `web-admin/src/App.jsx` |
| 9 | Cost panel shows `vazios`/`alerta`/`taxaFalha`, not just `erros` (FIX-C36) | ✓ VERIFIED | `web-admin/src/App.jsx:189-191` — 3 new `Kv` lines ("Respostas vazias", "Taxa de falha", "Alerta do provedor primário") coexisting with the pre-existing "Erros (janela 3 dias)" line, never merged |
| 10 | "Kill-switch ligado há N horas" alert appears in Automação tab (FIX-C37) | ✓ VERIFIED | `server/app/agent.py:215` `kill_switch_ligado_desde()`, `:251` `_alertar_kill_switch()` hooked at line 1054 — confirmed BEFORE the first `kill_switch_on()` gate at line 1078; `web-admin/src/App.jsx:501` renders "Ligado há" `Kv` conditioned on `data.on` |

**Score:** 10/10 truths verified at the code level. All backend/frontend guardian
tests for these truths were executed directly by the verifier (not read from
SUMMARY claims) and pass. However, 2 human-check items from the plans were
never actually performed (see Human Verification Required below), which
overrides an otherwise-clean score per the verification decision tree.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `server/app/technical_snapshot.py` | propagates `source` | ✓ VERIFIED | line 196, `hist.get("source")` in return dict |
| `server/app/main.py` | `source`/`degradado` in `/api/technicals` payload; `_plano_do_escopo`/`_gate_analise`; 2 timing_watch routes; `rastreavel`/`desde`/`horas` | ✓ VERIFIED | all present, grepped and read directly |
| `web/src/App.jsx` | `FONTE_LABEL(data.source)` line, FonteDadosScreen budget line, C-19 card, no `Modo do app:` duplication | ✓ VERIFIED | all present; `Yahoo Finance` count = 0 |
| `server/app/candle_provider.py` | `get_quote` try/except, no `str(e)` leak | ✓ VERIFIED | both branches wrapped |
| `web-admin/src/App.jsx` | Custos 3 new lines; TimingWatchKillSwitchBox + KPI; "Ligado há" line | ✓ VERIFIED | all present |
| `server/app/plan.py` | written contract: `metering` is sole counter | ✓ VERIFIED | docstring updated, no executable code change (as required by D-03) |
| `server/app/timing_watch.py` | memory→DB→env kill-switch pattern | ✓ VERIFIED | mirrors `agent.py` pattern |
| `server/app/db.py` | `user_ids_with_roles` (internal-only), `audit_last` | ✓ VERIFIED | `grep -c "user_ids_with_roles" server/app/main.py` = 0 (no HTTP route exposure) |
| `server/app/agent.py` | `kill_switch_ligado_desde`, `_alertar_kill_switch`, hook placement | ✓ VERIFIED | hook confirmed before first gate |
| 8 new guardian test files (backend + web) | pass and are structurally sound | ✓ VERIFIED | all executed directly, all pass (see below) |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `web/src/App.jsx` (TechnicalModal) | `/api/technicals` | `FONTE_LABEL(data.source)` | ✓ WIRED | confirmed by direct read + build |
| `server/app/main.py` | `brapi_budget.degradado` | `_degradado_spot()` | ✓ WIRED | try/except-wrapped, confirmed |
| `server/app/main.py` (rota /api/buy) | `candle_provider.get_quote` | 502 on `price is None` | ✓ WIRED | unchanged pre-existing check, now actually reachable |
| `web-admin/src/App.jsx` | `/api/agent/status` → `candles` | `data.candles.(vazios|taxaFalha|alerta)` | ✓ WIRED | confirmed |
| `web/src/App.jsx` (card C-19) | `ctx.operador`/`ag.serverEnabled`/`modoEfetivo` | direct variable reads | ✓ WIRED | confirmed via guardian test + direct read; no `config.appMode` inside card block |
| `server/app/main.py` | `server/app/plan.py` | `plan.current_plan(user)` via `_plano_do_escopo` | ✓ WIRED | confirmed |
| `web-admin/src/App.jsx` | `/api/admin/timing-watch/kill-switch` | `api.timingWatchKillSwitchGet/Put` | ✓ WIRED | confirmed |
| `server/app/agent.py` (scheduler_loop) | `server/app/push.py` | `push.send_to_user` per admin | ✓ WIRED | confirmed, and placement before kill-switch gate confirmed by index comparison |

### Behavioral Spot-Checks / Guardian Test Execution

All new guardian tests introduced by this phase were executed directly by the
verifier (not trusted from SUMMARY pass claims):

| Test | Command | Result | Status |
|------|---------|--------|--------|
| `test_fase3_proveniencia_technicals.py` | part of full pytest run | included in 1100 passed | ✓ PASS |
| `test_fase3_get_quote_erro_limpo.py` | part of full pytest run | included in 1100 passed | ✓ PASS |
| `test_fase3_paridade_stores_generica.mjs` | `node web/tests/test_fase3_paridade_stores_generica.mjs` | "todos os testes passaram" | ✓ PASS |
| `test_fase3_c19_card_status.mjs` | `node web/tests/test_fase3_c19_card_status.mjs` | "todos os testes passaram" (7 assertions) | ✓ PASS |
| `test_auditoria_status_strip.mjs` (pre-existing, preserved) | `node web/tests/test_auditoria_status_strip.mjs` | "todos os testes passaram" (4 assertions, none removed) | ✓ PASS |
| `test_fase3_gate_plano.py` | `pytest -q tests/test_fase3_gate_plano.py` | 12 passed | ✓ PASS |
| `test_fase3_timing_watch_kill.py` | `pytest -q tests/test_fase3_timing_watch_kill.py` | 17 passed | ✓ PASS |
| `test_fase3_admin_timing_watch.mjs` | `node web/tests/test_fase3_admin_timing_watch.mjs` | "TODOS OS TESTES PASSARAM" | ✓ PASS |
| `test_fase3_kill_switch_duracao.py` | `pytest -q tests/test_fase3_kill_switch_duracao.py` | 24 passed | ✓ PASS |
| `test_fase3_admin_duracao.mjs` | `node web/tests/test_fase3_admin_duracao.mjs` | "TODOS OS TESTES PASSARAM" | ✓ PASS |
| Full backend suite | `cd server && ./.venv/bin/python -m pytest -q` | 1100 passed | ✓ PASS |
| `web` build | `cd web && npx vite build` | built in 1.09s, PWA generated | ✓ PASS |
| `web-admin` build | `cd web-admin && npx vite build` (temp symlink to installed `node_modules`, removed after) | built in 1.06s | ✓ PASS |
| **Canonical suite** | `bash scripts/executar.sh --testes` | exit 0, zero `[X]` across all backend + `web/tests/*.mjs` files | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|--------------|--------|----------|
| FIX-C11 | 03-01 | Rótulo de fonte real no painel técnico | ✓ SATISFIED | verified above |
| FIX-C30 | 03-01 | Estado degradado da cota brapi visível | ✓ SATISFIED | verified above |
| FIX-C12 | 03-02 | Erro de fonte de dado não vaza detalhe interno | ✓ SATISFIED | verified above |
| FIX-C36 | 03-02 | Painel de custos mostra vazios/taxaFalha/alerta | ✓ SATISFIED | verified above |
| FIX-C20 | 03-03 | Guardião genérico de paridade de stores | ✓ SATISFIED | verified above |
| FIX-C19 | 03-03 | Card de status único (corrigido D-02) | ✓ SATISFIED (code); ? outstanding live behavioral check | see Human Verification |
| FIX-C31 | 03-04 | Gate resolve plano real do usuário | ✓ SATISFIED | verified above |
| FIX-C32 | 03-04 | Gate único de análise (sem duplicidade com metering) | ✓ SATISFIED | verified above |
| FIX-C35 | 03-05 | 2º kill-switch (timing_watch) visível/controlável | ✓ SATISFIED (code); ? outstanding "sem permissão" live check | see Human Verification |
| FIX-C37 | 03-06 | Alerta ativo de kill-switch ligado há N horas | ✓ SATISFIED | verified above; human checkpoint for this specific item was performed and approved (see 03-06-SUMMARY.md, steps 6-8) |

**No orphaned requirements found** — all 10 IDs from ROADMAP.md and PLAN
frontmatter are accounted for above; all 10 are code-verified.

**Traceability document gap (not a functional gap):** `.planning/REQUIREMENTS.md`
still lists all 10 `FIX-C*` items as unchecked (`- [ ]`) and `Pending` in its
status table (lines 25-57, 138-147), despite every one of them being
code-verified complete above. `.planning/ROADMAP.md` (currently uncommitted
in the working tree) already reflects "Phase 3 ... 6/6 ... Complete
2026-08-19", but the corresponding
`docs(03): mark FIX-C* complete in REQUIREMENTS.md` commit — the same pattern
used for Phase 1 (`a54123d`) and Phase 2 (`fa2ccad`) — has not been made yet.
This does not block the phase goal (the underlying fixes are real and
verified), but it is an explicit deliverable gap in traceability bookkeeping
that should be closed before this phase is considered administratively done.

### Anti-Patterns Found

Scanned all files modified by plans 03-01 through 03-06 for TBD/FIXME/XXX/TODO/HACK,
empty-return stubs, and hardcoded-empty props.

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | none found | — | No `TBD`/`FIXME`/`XXX` unreferenced debt markers in any phase-3-modified file. Comments containing "FUTURO: passar a contagem do mes do usuario" (`main.py`) and "C-33 (fase 5)" are explicit, dated forward-references to a already-scheduled future phase item — not undocumented debt. |

No blockers found in this category.

### Human Verification Required

Two items, both harvested from `<verify><human-check>` blocks in phase-3 PLAN
files that were never actually executed (the phase-level human checkpoint in
03-06 Task 3 covered 7 specific screens/steps, but neither of these two items
appears among them):

#### 1. Operador IA status card — reactive behavior (FIX-C19)

**Test:** Open the "Operador IA" screen (Modo Operador). Toggle "Modo do
app" via Perfil and return to the screen. Toggle "Operador no servidor" from
the hero card.
**Expected:** The 3-badge card appears at the top, before the "Operador IA"
title. Toggling app mode moves badge 1 ("Modo do app") and badge 3
("Executar/sinalizar") together. Toggling the server switch moves badge 2
("Operador no servidor") and the hero card's ATIVO/INATIVO label in the SAME
direction — never opposite.
**Why human:** Reactive cross-component state sync and screen navigation —
not verifiable by static grep. Explicitly flagged as a pending human-check by
PLAN 03-03 Task 2 and its own SUMMARY ("não executável neste ambiente...
delegar ao Alex antes do deploy"); never subsequently covered by the phase's
end-of-phase checkpoint (03-06 Task 3).

#### 2. Timing-watch kill-switch box — permission fallback (FIX-C35)

**Test:** With an admin account that has `execucao_automatica.ver` but NOT
`execucao_automatica.controlar`, open the Automação tab.
**Expected:** The "Kill-switch do push de gatilho (timing_watch)" box shows
state but no interactive toggle — instead the message "Sem permissão para
alternar (requer execucao_automatica.controlar)."
**Why human:** RBAC-conditional rendering with a real restricted account —
not verifiable from static component inspection alone. Explicitly listed in
PLAN 03-05's verification section; not covered by 03-06 Task 3's 7-step
checklist.

### Gaps Summary

No functional/code-level gaps were found. All 10 FIX-C* requirements for
Phase 3 are implemented, guarded by passing automated tests (backend +
frontend), and confirmed by direct source inspection rather than SUMMARY
narrative. The full canonical suite (`bash scripts/executar.sh --testes`)
exits 0 with zero failures, and both `web`/`web-admin` production builds
succeed.

Two items block a clean `passed` verdict:

1. Two `<human-check>` items from PLAN 03-03 and PLAN 03-05 were never
   actually performed live, despite the phase running an end-of-phase human
   checkpoint (03-06 Task 3) that covered 7 other screens/steps but omitted
   these two. Per the verification decision tree, any outstanding human-check
   item forces `status: human_needed` regardless of automated score.
2. `.planning/REQUIREMENTS.md` traceability was not updated to reflect Phase
   3 completion (still shows all 10 `FIX-C*` as `Pending`/unchecked), unlike
   the precedent set by Phase 1 and Phase 2. This is a WARNING, not a
   blocker — it does not indicate any missing functionality, only a
   bookkeeping step that should be closed with a follow-up
   `docs(03): mark FIX-C* complete in REQUIREMENTS.md` commit before the
   milestone is considered fully closed.

The `deferred-items.md` note about pre-existing `candle_cache`/`app.main`
test-isolation contamination (03-06 entry) was reviewed and is correctly
scoped out of this phase: it is a pre-existing test-infrastructure gap
spanning ~10 test files outside every phase-3 plan's file list, was not
introduced by any phase-3 change, was remediated as a data-only fix
(gitignored DB file), and does not affect the correctness of any phase-3
deliverable. No action required from this verification.

---

_Verified: 2026-08-19T04:28:51Z_
_Verifier: Claude (gsd-verifier)_
