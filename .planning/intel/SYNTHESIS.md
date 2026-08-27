# Synthesis Summary — b3-agente doc ingest

Mode: **merge** (existing `.planning/` project already has PROJECT.md, ROADMAP.md, STATE.md, MILESTONES.md, RETROSPECTIVE.md; no REQUIREMENTS.md or CONTEXT.md existed prior to this ingest — treated as absent, not an error).

This is a **re-run**. The prior pass raised 1 BLOCKER and 1 WARNING; both were resolved by the product owner (Alex, 2026-08-27) and are reflected below. See "Conflicts" section for what changed and why.

## Doc counts

- 32 documents classified and consumed in this run (all read at primary-source level, not just from classifier summaries).
- By type: **19 ADR**, **5 SPEC**, **8 DOC**. No UNKNOWN in this run.
- No PRD-classified documents in this batch.
- `docs/prompts/admin-mobile-otimizado.md` (classified UNKNOWN/low-confidence in the prior pass) was **deliberately excluded** from this ingest batch per product-owner decision (2026-08-27) — its classification JSON was moved out of `CLASSIFICATIONS_DIR` before this run, so it was never loaded and is not part of the 32-document count. Treated as out of scope, not as a dropped/lost input. See `../INGEST-CONFLICTS.md` [INFO].

## Decisions (decisions.md)

19 ADR entries. Locked (status: locked, i.e. Aceito/Accepted/Implementado): ADR-001, 003, 004, 005, 006, 007, 008, 009, 012, 013, **014**, 017, 018, 019 — **14 locked**.
Proposed/not locked (Proposto, awaiting decision or approval): ADR-002, 010, 011, 015, 016 — **5 proposed**.

ADR-014 moved from proposed to locked in this re-run: the product owner confirmed it was approved and implemented after the ADR document was written; the document's own "Proposto — aguardando aprovação" status text is stale and was never updated to reflect the later approval. Synthesized as locked/accepted, consistent with `PROJECT.md`'s existing "existing" tag. Re-checked against every other locked ADR in this batch for LOCKED-vs-LOCKED contradiction — none found (see `../INGEST-CONFLICTS.md` [INFO]).

Notable locked decisions the roadmapper should treat as fixed unless the user explicitly reopens them: Yahoo=intraday/brapi=daily+spot data sourcing (ADR-001/008), options as a card-layer with `optionPositions` as a separate collection (ADR-003/004/005), backend-first deterministic didactic layer (ADR-006/007), regime+momentum Radar ranking axis (ADR-009, see caveat below), RBAC with 7 permission groups (ADR-013), mobile admin surface via in-app browser handoff to web-admin (ADR-014, approved/implemented — status text in the source file is stale), dynamic setup selection replacing static confluência-based entry (ADR-017), no E2E automation for now (ADR-018), COTAHIST daily ingestion (ADR-019).

Proposed items awaiting explicit Alex decision: temporal-triad parameter validation (ADR-002), commercial plan pricing/caps (ADR-010), observability-module hosting/auth (ADR-011), recommendation-engine instrumentation fix + backtest (ADR-015), setup quality corrective action (ADR-016, superseded in decision terms by the already-locked ADR-017).

## Requirements (requirements.md)

Zero PRD documents in this batch. File is intentionally near-empty, pointing to the closest adjacent content (a SPEC with quasi-locked product decisions, and ADR action-item checklists that already live in `decisions.md`).

## Constraints (constraints.md)

5 SPEC entries, breakdown by type: 2 protocol/api-contract (ESPEC-A Radar ranking, plano-operador-entrada-e-modos agent execution-mode contract), 2 schema+api-contract (ESPEC-B analysis_outcomes segmentation, v2-opcoes-proposta options data model), 1 api-contract-as-measurement (MEDIÇÃO-Brapi, empirical binding constraints on the brapi integration, explicitly deferring to ADR-008 on conflict).

## Context (context.md)

8 DOC entries organized under 8 topics: product overview (AJUDA.md), technical architecture map (ARQUITETURA.md, self-declared non-authoritative vs. ADRs), Radar refactor handoff mechanics (HANDOFF-claude-code.md), Yahoo intraday feasibility measurement (MEDICAO-Yahoo-Intraday), signal ledger operations runbook (OPERACAO-ledger-de-sinais), appMode UX incident history (auditoria-controle-ordens-parametros — largely superseded by later v1.1 work per MILESTONES.md, noted inline), didactic-layer inventory (didatica-inventario, input to ADR-006), and native iOS voice bugfix (plano-voz-nativa-ios, self-flagged as unverified on real device).

## Conflicts: 0 blockers, 0 competing-variants, 7 auto-resolved/informational

Full detail in `../INGEST-CONFLICTS.md`. Summary of what changed in this re-run:

- **0 BLOCKERS** (was 1). The prior BLOCKER — `docs/prompts/admin-mobile-otimizado.md` classified UNKNOWN/low-confidence — is resolved: the product owner excluded the document from this ingest batch entirely rather than re-tagging it. It is out of scope for this run, not a routing failure. Recorded as INFO for auditability.
- **0 WARNINGS** (was 1). The prior WARNING — ADR-014's own "awaiting approval, do not implement" status text contradicting PROJECT.md's "existing" claim — is resolved: the product owner confirmed ADR-014 was approved and implemented after the ADR was written, and the source document's status text is simply stale. ADR-014 is now synthesized as locked/accepted in `decisions.md`. Recorded as INFO, including a LOCKED-vs-LOCKED re-check against the rest of the batch (no contradiction found).
- **7 INFO** items: (1) admin-mobile-otimizado.md exclusion audit note; (2) ADR-014 stale-status/now-locked audit note; (3) cycle scan found only benign companion-doc mutual references, not contradictory authority loops (011↔012, 009↔ESPEC-A, 009↔HANDOFF) — synthesis proceeded on all 32 docs in scope, none excluded for cyclicity; (4) ADR-008 narrows ADR-001's scope by mutual, non-disputed agreement (daily/spot vs. intraday split); (5) ADR-012 (locked) supersedes ADR-011 (not locked) on the portal's color-palette decision, explicitly documented in both sources; (6) ADR-016 (not locked) explicitly calls ADR-009's (locked) ranking thesis "refutada" by 15-year backtest evidence — the locked decision is not auto-overridden, but the roadmapper should know the rationale behind it is empirically contested and ADR-017 (locked) already layers a corrective mechanism on top without revoking it; (7) `plano-operador-entrada-e-modos.md`'s quasi-locked D1-D6 and ADR-017's later eligibility gate modify the same code path complementarily, not competitively.

No LOCKED-vs-LOCKED contradictions were found (including after ADR-014's status flip to locked). No competing PRD acceptance-criteria variants exist (zero PRDs in this batch).

## Where to look next

- `decisions.md` — all 19 ADRs, one entry each, with locked/proposed status and cross-notes on supersession. ADR-014 is now locked.
- `requirements.md` — near-empty, explains why.
- `constraints.md` — all 5 SPECs.
- `context.md` — all 8 DOCs, topic-organized.
- `../INGEST-CONFLICTS.md` — the full BLOCKER/WARNING/INFO report; **0 blockers in this re-run — safe to route.**
