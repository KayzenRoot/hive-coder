# GEF Bootstrap V1.0.0 — Universal Adoption Baseline for Hive Coder

## Status
`GEF_V1_ADOPTED_READY_FOR_GOVERNED_DEVELOPMENT` subject only to the documentation-only closeout record itself passing exact-head gates/audit and merge verification.

## Classification
`BROWNFIELD`.

## Accepted adoption identity
- Pre-adoption main: `ccfed1f960c80dc58e4f45cb627451e77c7d5a79`.
- Technical adoption head: `a62d7602be8a1ed23ca3fc4459aa40188205c860`.
- Final adoption PR head: `f323e8f6337e5d7b323ff9d256fb197beca8e171`.
- Squash merge main: `6c9fbda50c0477ef353018df1e5aea6f738d3aa4`.
- PR: `#73`.
- Final PR gates: Governance #398 and Desktop Shell #234 SUCCESS.
- Post-merge gates: Governance #399 and Desktop Shell #235 SUCCESS.
- CRITICAL/HIGH: 0/0.

## Repository-native mapping
- Project identity / purpose -> `docs/project-brain/01-PROJECT-OVERVIEW.md`.
- Requirements -> `docs/project-brain/02-REQUIREMENTS.md`.
- Scope -> `docs/project-brain/03-SCOPE.md`.
- Architecture -> `docs/project-brain/04-ARCHITECTURE.md`.
- Security -> `docs/project-brain/05-SECURITY.md`.
- Test/benchmark plan -> `docs/project-brain/06-TEST-BENCHMARK-PLAN.md`.
- Deployment/recovery -> `docs/project-brain/07-DEPLOYMENT.md` plus Work Order recovery sections.
- Backlog -> `docs/project-brain/08-BACKLOG.md`.
- Definition of Done -> `docs/project-brain/09-DEFINITION-OF-DONE.md`.
- Decisions -> `docs/project-brain/10-DECISIONS-LEDGER.md` + ADRs.
- Human checkpoint -> `docs/project-brain/11-CHECKPOINT.md`.
- Machine adoption/resume state -> `.engineering/gef/GEF-UNIVERSAL-CHECKPOINT.json`.
- Work Orders -> `.engineering/work-orders/`.
- Context Locks -> `.engineering/context-locks/`.
- Evidence -> `.engineering/evidence/`.
- Checkpoint Deltas -> `.engineering/checkpoint-deltas/`.
- Universal GEF policy/protocols -> `.engineering/gef/`.

## Preservation outcome
No product/runtime/source/test/workflow/dependency behavior was changed by the adoption. Existing Project Brain is project authority and was mapped rather than duplicated. Historical Work Orders/checkpoints/evidence remain historical.

## Known drift recorded, not fabricated away
`docs/project-brain/11-CHECKPOINT.md` still declares CP-0021 while main history includes later CP-0022 and PLATFORM-001 evidence. This remains a separate source reconciliation debt.

## Active increment preservation
Draft PR #69 / `HCODER-WO-0023` remains the active non-canonical product increment. It must merge/reconcile the adopted main before its next executor mutation, then continue with the rewritten GEF V1 Prompt 05.
