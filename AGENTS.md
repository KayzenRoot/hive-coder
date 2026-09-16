# AGENTS.md — Hive Coder

## Source hierarchy
Read canonical truth in this order before implementation or review:
1. `docs/project-brain/11-CHECKPOINT.md`
2. `docs/project-brain/10-DECISIONS-LEDGER.md` plus approved ADRs under `docs/project-brain/adrs/`
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
2. Reconcile Issue #30 against canonical Checkpoint, Decisions Ledger/approved ADRs, active Work Order/PR and exact-head CI/HEDS.
3. GitHub/canonical truth wins if Issue #30 is stale.
4. Continue autonomously from its `NEXT EXACT ACTIONS`; do not ask the user to restate recoverable context.

## Current execution state
`HCODER-CP-0022 — Governed Existing-File Replacement Capability` is **APPROVED / CANONICAL**.

Canonical state:
- `HCODER-CP-0022` / `DEC-026 — Governed Existing-File Replacement Capability` is **CANONICAL**, promoted by closeout merge `795ed101eaf5d770f63a96db7f01a82369be34f1`.
- Canonical base `HCODER-CP-0021` / `9c2623f8b335cf29b63b5db5f43e694bfd77938e`.
- Product PR #62 squash-merged as `06c68611a42e07b85ae765145d94bb613110ac14`; post-merge Governance #324 and Desktop Shell #160 passed.
- CP-0022 closeout exact head `a777ac207b42059a33ce9d73d8287122ff43c0a9` passed Governance #325 and Desktop Shell #161 with HEDS closeout review `5222180870`, unresolved HIGH/CRITICAL `0/0`.
- `HCODER-WO-0022-CR-001` is resolved; the canonical guarantee is bounded-race atomic replacement, explicitly **not** strict CAS.
- Hive runtime has exactly two privileged workspace file mutation adapters: CP-0021 create-only `write_file_v1` and CP-0022 `replace_file_v1`, both under `Capability.FILESYSTEM_WRITE`, both mandatory trusted-approval gated, both permit-bound and single-use.

CP-0022 authority remains replacement-only: append, truncate-in-place, delete, arbitrary rename/move, recursive mutation, chmod/chown, Git mutation, generic filesystem mutation, shell/terminal/process execution, Tauri/desktop write commands, provider/model execution or credentials, Cua/computer-use mutation beyond prior governed boundaries, remote control, automatic skill activation and billing/purchase authority remain unapproved.

Earlier checkpoint receipts (CP-0020 and prior) remain historically recorded in their closeout evidence files under `.engineering/evidence/` and are not restated here.

### In-flight increments (not checkpoints, not canonical-complete)
- `HCODER-PLATFORM-001` (Issue #63) native validation matrix is on `main` at `22b56b0f3111158cbf50789b1647c5a578a171c1`, evidence ledger reconciled at `ccfed1f960c80dc58e4f45cb627451e77c7d5a79`. Its ledger is **PREBUILT / NATIVE MATRIX INCOMPLETE**: Linux and macOS native desktop/Tauri exact-head evidence is still required.
- `HCODER-WO-0023` (Issue #68, PR #69 Draft) governed Git staging is an active Work Order with its own Context Lock. It grants no Git mutation authority and is not promoted.

### NEXT EXACT ACTIONS
1. Continue the active Work Order from its own Context Lock and Work Order sources; do not infer scope from historical branches.
2. Complete `HCODER-PLATFORM-001` Linux and macOS native desktop/Tauri exact-head evidence, or explicitly record it as deferred.
3. Require exact-head Governance + Desktop Shell on every promotion head; any new head invalidates old exact-head evidence.
4. Perform HEDS with unresolved HIGH/CRITICAL `0/0` before promotion.
5. Refresh Issue #30 with fully sealed receipts once the active Work Order reaches a governed closeout.