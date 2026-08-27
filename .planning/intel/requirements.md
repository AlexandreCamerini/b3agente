# Requirements (from PRDs)

**Zero documents in this ingest batch were classified as PRD.** Of the 32 classified documents in scope for this run (19 ADR, 5 SPEC, 8 DOC), none met the PRD content-signal checklist (user-story language, acceptance-criteria-first framing, product-scope document independent of a specific technical decision or spec).

(`docs/prompts/admin-mobile-otimizado.md` was deliberately excluded from this ingest batch per product-owner decision — see `../INGEST-CONFLICTS.md` [INFO] — and is not part of the 32-document count above.)

This file exists as the contractual output of the synthesizer per `gsd-doc-synthesizer.md`, deliberately near-empty rather than omitted.

## Closest adjacent content (not PRD, cross-referenced for downstream awareness)

- **`docs/plano-operador-entrada-e-modos.md`** (classified **SPEC**, not PRD) contains a section literally titled "Decisões fechadas (aprovadas pelo Alex em 2026-08-07)" — D1 through D6, product-level decisions on entrada automática (Modo Estudo trava, teto compartilhado `maxOpsDia`, `allocPct` reused with backend-enforced ceiling, only `COMPRAR` side is auto-executable). These read like locked requirements but the document lacks ADR structure (no Status/Accepted, no numbered ADR file) and is dominated by implementation-plan content (files, functions, phases), so it was classified SPEC per the classifier's own reasoning. Full content is in `constraints.md`.
- **ADR action-item checklists** (e.g., ADR-001 items 1-9, ADR-013's rotas NOVAS propostas, ADR-017's "Sequenciamento de entrega") function as requirement-like acceptance criteria but originate from ADRs and are kept in `decisions.md`, not duplicated here, to preserve single-source-of-truth per document type.
- **`docs/refactor/ESPEC-A-eixo-selecao.md`** and **`docs/refactor/ESPEC-B-validacao-regime.md`** (both SPEC) each have a "Critérios de aceite" section — acceptance criteria for a technical spec, not a product requirement. Kept in `constraints.md`.

If `gsd-roadmapper` needs product-requirement-shaped input, the nearest source is `PROJECT.md`'s own "Requirements" section (Validated/Active/Out of Scope), which is existing project context, not part of this ingest batch.
