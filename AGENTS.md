# AGENTS.md — Hive Coder

## Source hierarchy
Read canonical truth in this order before implementation or review:
1. `docs/project-brain/11-CHECKPOINT.md`
2. `docs/project-brain/10-DECISIONS-LEDGER.md`
3. `docs/project-brain/03-SCOPE.md`
4. `docs/project-brain/09-DEFINITION-OF-DONE.md`
5. `docs/project-brain/04-ARCHITECTURE.md`
6. `docs/project-brain/02-REQUIREMENTS.md`
7. remaining Project Brain / `.engineering` sources.

## Engineering flow
Use stable Work Order IDs and follow:
`ANALYZE -> SOURCE CHECK -> NEXT NECESSARY INCREMENT -> WORK ORDER -> CONTEXT LOCK -> PREFLIGHT -> EXECUTOR -> TESTS/EVIDENCE -> PR -> AUDIT -> APPROVED/CORRECTION REQUIRED/BLOCKED -> CHECKPOINT DELTA -> MERGE -> NEXT`.

Do not advance while the active increment has an unresolved HIGH/CRITICAL finding.

## Authority rules
- Git/code/tests/evidence beat conversation memory.
- Models/tools cannot mint approvals, permissions, trusted evidence or competence.
- Computer-use mutation must remain behind the approved Permission & Control Plane.
- New architecture/toolchain authority requires a governed decision/checkpoint.
- Never silently rewrite historical Decisions or Context Locks.

## Cross-chat continuation
If the user says `continue`, `continue do chat anterior`, or equivalent for Hive Coder:
1. Open GitHub Issue `#30` first.
2. Reconcile Issue #30 against canonical Checkpoint, Decisions Ledger, active Work Order/PR and exact-head CI/HEDS.
3. GitHub/canonical truth wins if Issue #30 is stale.
4. Continue autonomously from its `NEXT EXACT ACTIONS`; do not ask the user to restate recoverable context.

## Current promotion state
Active increment: `HCODER-WO-0015 — Desktop Shell Foundation & Safe Workspace Read Model`, PR `#32`, branch `feat/HCODER-WO-0015-desktop-shell`.

Technical reviewed head `9e212c6f8c959f3d3cb19cc5146485f39bd6c8fd` is green and HEDS review `5211566651` approved it for PROMOTION CANDIDATE. The next phase is documentation/governance promotion only. Until a later exact-head promotion review and APPROVED mutation complete, `HCODER-CP-0014` remains the latest canonical APPROVED checkpoint and `DEC-019`/`HCODER-CP-0015` remain CANDIDATE.

WO-0015 desktop authority remains read-only: one `get_desktop_snapshot` command scoped to `main`, zero Tauri plugin permissions, no generic command bridge, arbitrary filesystem mutation, computer-use mutation, provider credentials, skill activation, remote control or billing authority.

### NEXT EXACT ACTIONS
1. Commit the WO-0015 promotion documentation/evidence delta on PR #32.
2. Require exact-head Governance + Desktop Shell success on that promotion candidate.
3. Perform promotion HEDS; stop on any HIGH/CRITICAL finding.
4. If clean, mutate DEC-019 and CP-0015 to APPROVED, recording the exact promotion evidence; this approval mutation must independently pass exact-head Governance + Desktop Shell.
5. Perform final HEDS on the APPROVED head, mark PR ready, squash merge with expected-head protection, then require push-triggered Governance + Desktop Shell success on canonical `main`.
6. Update Issue #30 and close WO-0015/Issue #31 only after post-merge proof. Do not create WO-0016 before that source-check.
