---
quick_id: 260926-uhl
phase: quick-260926-uhl
plan: 01
status: complete
subsystem: web-dependencies, planning-docs
tags: [npm, capacitor, social-login, cherry-pick, planning]
provides:
  - "@capgo/capacitor-social-login pinned to ^8.3.34 in web/package.json and web/package-lock.json (was 'latest')"
  - "STATE.md/PROJECT.md hand-edited to reflect borisv2 as an independent repo (2026-09-26)"
affects: [web, planning-docs]
tech-stack:
  added: []
  patterns: ["git cherry-pick -x for cross-branch commit reuse"]
key-files:
  created: []
  modified:
    - web/package.json
    - web/package-lock.json
    - .planning/STATE.md
    - .planning/PROJECT.md
key-decisions:
  - "Cherry-pick applied cleanly with git merge (no manual conflict resolution needed) — lockfile version was already 2.0.0, so only the dependency spec changed"
  - "STATE.md/PROJECT.md edited by hand with Edit tool per repo guardrail — gsd-sdk state.*/milestone.*/roadmap.* mutators never called"
duration: ~20min
completed: 2026-09-26
---

# Quick Task 260926-uhl: Fixa social-login ^8.3.34 (cherry-pick ac20a9c) + registra borisv2 independente Summary

**Cherry-picked the manifest pin for `@capgo/capacitor-social-login` (`latest` → `^8.3.34`) from the archived branch into `v2/interacao-estrutural`, validated with the full canonical suite outside the sandbox, and hand-documented that borisv2 is now an independent git repository (no longer dependent on the old worktree/folder).**

## Performance
- **Duration:** ~20 min
- **Tasks:** 3/3 complete
- **Files modified:** 4 (2 code/manifest, 2 docs)

## Accomplishments

### Task 1: Cherry-pick ac20a9c and validate the manifest
- `git cherry-pick -x ac20a9cff8924f9bf3395496b8b588d36de5bf34` applied **cleanly** (git auto-merged `web/package-lock.json`; no manual conflict resolution needed).
- Commit created: `f8c1ec5` — message preserved verbatim from the original (`chore(web): fixa @capgo/capacitor-social-login em ^8.3.34 (era latest)`, `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`), with `(cherry picked from commit ac20a9c...)` appended by `-x`.
- `web/package.json`: `"@capgo/capacitor-social-login": "latest"` → `"^8.3.34"`.
- `web/package-lock.json`: same dependency string updated in `packages[""].dependencies`. The `"version"` field hunk (`1.0.0`→`2.0.0`) was a **no-op** as anticipated by the plan — both root `"version"` and `packages[""].version` were already `2.0.0` in the current HEAD, so git's merge dropped that redundant hunk automatically; only the dependency spec line changed (2 lines total in the diff, confirmed via `git show f8c1ec5`).
- `web/package.json`'s public `"version"` field was NOT touched (confirmed by diff — plan explicitly forbade this).
- Verification: `cd web && npm ls @capgo/capacitor-social-login` → `@capgo/capacitor-social-login@8.3.34`, no UNMET DEPENDENCY (ran with `dangerouslyDisableSandbox: true`; the run emitted 66 lines of `ERROR: failed to copy trust settings of system certificate-25291` — this is the same TLS/keychain sandbox artifact documented elsewhere in this repo's history, not a real npm error; the resolved-version line printed cleanly at the end).
- `npm install --package-lock-only --ignore-scripts` was NOT run — not needed since the cherry-pick's lockfile diff already matched exactly what a real npm resolution would produce (inspection-only check, as the plan allowed as a fallback).

### Task 2: Canonical suite + build validation
- `bash scripts/executar.sh --testes` run FULLY outside the sandbox (`dangerouslyDisableSandbox: true`), background-safe with generous timeout.
- **Backend (pytest): 3050 passed, 5 skipped, 3 xfailed, 0 failed** — exact match to the v1.8-close baseline cited in the plan.
- **Web (.mjs): 165/165 OK** — exact match to baseline (165 `[OK]` lines counted, zero failures).
- `cd web && npx vite build` — **clean, 119 modules transformed, built in 1.22s**. Only pre-existing warning: main chunk >500kB (unrelated code-splitting advisory, not a regression from this change).
- No divergence from baseline — no investigation needed.
- No publish/deploy performed (manifest-only change, no runtime effect, per plan constraint).

### Task 3: Hand-registered borisv2 independence in STATE.md/PROJECT.md
- `.planning/STATE.md`, `## Current Position` → `Ambiente:` block replaced: removed the obsolete warning that archiving the old folder (`bolsia=boris antigo/b3-agente`) would break borisv2's worktree link. New text records: borisv2's own `.git` created via `git clone --mirror --no-hardlinks` (no alternates, `core.bare=false`); `origin` = `https://github.com/AlexandreCamerini/b3agente.git`; old folder's worktree metadata removed + `git worktree prune` (which also cleared a stale orphan entry `zen-nightingale-492c64`); old-repo-only data preserved on GitHub in `origin/arquivo/main-bolsia-antigo` (`a7358e4`, includes `ac20a9c`; the `260923-fst` docs commit on that branch was deliberately NOT brought in — conflicts with current STATE.md) and `origin/arquivo/stash-pre-gateway` (`0f7f79b`); old folder can now be archived/deleted safely — only untracked items worth Alex checking first are `web/.env-local` and `.claude/skills/swiftui-pro`.
- New row added to `### Quick Tasks Completed` table (same 6-column format) for `260926-uhl`, dated 2026-09-26, commit `f8c1ec5`, status `Verified` (suite matched baseline exactly), directory link `[260926-uhl](./quick/260926-uhl-fixa-social-login-8-3-34-cherry-pick-ac2/)`.
- `.planning/PROJECT.md`, "Key Decisions" table: row starting "Worktree `borisv2` ficou órfão..." — Outcome column changed from `⚠️ Revisit — reparado com git worktree repair...` to `✓ Good — risco eliminado em 2026-09-26: borisv2 convertido em repositório independente (clone --mirror, origin próprio, dados antigos preservados em origin/arquivo/*); pasta antiga pode ser arquivada/apagada sem quebrar este repo`. Decision/Reasoning columns left untouched.
- Verified with `git diff --stat .planning/STATE.md .planning/PROJECT.md` — only these two files touched (2 lines in PROJECT.md, 18 lines net in STATE.md). Neither file was committed by this execution — per plan constraint, that commit is the orchestrator's responsibility.

## Task Commits
1. **Task 1: Cherry-pick ac20a9c e validar o manifest** — `f8c1ec5`
2. **Task 2: Validar suíte canônica e build** — no commit (validation only, no files modified)
3. **Task 3: Registrar à mão a independência do borisv2** — no commit (STATE.md/PROJECT.md left staged for the orchestrator's docs commit, per plan constraint)

## Files Created/Modified
- `web/package.json` — dependency spec `@capgo/capacitor-social-login` pinned `^8.3.34` (was `latest`)
- `web/package-lock.json` — same dependency spec updated; `"version"` fields were already `2.0.0`, no change needed there
- `.planning/STATE.md` — `Ambiente:` block rewritten (independence narrative), new Quick Tasks Completed row (edited, not committed by this execution)
- `.planning/PROJECT.md` — Key Decisions table Outcome column for the borisv2-worktree row updated to `✓ Good` (edited, not committed by this execution)

## Deviations from Plan

None — plan executed exactly as written. Cherry-pick applied clean (no conflict path exercised); no auth gates; no architectural questions arose.

## Known Stubs

None.

## Threat Flags

None — this quick task only touches a dependency version pin (already covered by the plan's own threat model, T-quick-01) and hand-edited planning docs. No new network endpoints, auth paths, or trust-boundary surface introduced.

## Self-Check: PASSED

- `web/package.json` — FOUND, contains `"@capgo/capacitor-social-login": "^8.3.34"`.
- `web/package-lock.json` — FOUND, contains `"@capgo/capacitor-social-login": "^8.3.34"` in `packages[""].dependencies`.
- Commit `f8c1ec5` — FOUND in `git log --oneline` on `v2/interacao-estrutural`.
- `.planning/STATE.md` — FOUND, diff confirmed scoped to `Ambiente:` block + new table row.
- `.planning/PROJECT.md` — FOUND, diff confirmed scoped to single Outcome cell.

## Next Phase Readiness

Manifest pin is durable and committed. Canonical suite and build are green at baseline. STATE.md/PROJECT.md edits are staged (uncommitted) for the orchestrator's docs commit. No further action required from this quick task; the old folder (`/Users/acamerini/dev/bolsia=boris antigo/b3-agente`) can be archived/deleted by Alex whenever convenient, after he personally checks the two untracked items named above.
