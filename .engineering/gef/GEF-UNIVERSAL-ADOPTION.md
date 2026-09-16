# GEF Bootstrap V1.0.0 — Universal Adoption Baseline for Hive Coder

## Classification
`BROWNFIELD`.

Evidence: material Python runtime, React/Tauri desktop application, tests, workflows, Project Brain, ADR/decision ledger, many completed Work Orders/checkpoints, active PR history and an existing local GEF layer.

## Pre-GEF-universal baseline
Universal-adoption base main: `ccfed1f960c80dc58e4f45cb627451e77c7d5a79`.

The repository already used a Hive-specific GEF/HEDS system. This adoption upgrades/reconciles that system to the universal brownfield rules. It does not claim that earlier work was executed under this universal adoption prompt.

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
- PR governance -> `.github/PULL_REQUEST_TEMPLATE.md` + hosted workflows.

## Existing user work preserved
No product/runtime/source/test/workflow file is replaced by the adoption. Existing Project Brain is project authority and is mapped rather than duplicated. Existing CI remains in place. Historical Work Orders/checkpoints remain historical.

## Known drift recorded, not fabricated away
`docs/project-brain/11-CHECKPOINT.md` still declares CP-0021 while main history includes later CP-0022 and PLATFORM-001 evidence. This is a source reconciliation debt, not permission to invent a new checkpoint. The next governed source reconciliation may fix it using evidence.

## Active increment preservation
Draft PR #69 / `HCODER-WO-0023` remains the active non-canonical product increment. Universal adoption does not rewrite its implementation. After this adoption reaches main, that branch must merge/reconcile current main before continuing.

## Adoption STOP condition
Candidate state: `GEF_ADOPTION_EXACT_HEAD_EVIDENCE_REQUIRED` until hosted exact-head gates and technical review pass. After merge and a post-adoption resume receipt, state becomes `GEF_V1_ADOPTED_READY_FOR_GOVERNED_DEVELOPMENT`.
