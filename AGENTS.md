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

## Current execution state
Canonical `main` remains `HCODER-CP-0018` at `c0a44d43546b9f176125b9e7099b8422d6b62ba3` until WO-0019 merges and passes post-merge validation.

Active increment: `HCODER-WO-0019 — Runtime Status Sidecar Helper`, Issue `#47`, PR `#48`, branch `feat/HCODER-WO-0019-runtime-status-sidecar-canonical`.

Technical exact head `ba10ba72f76316806cd820dc0d205e68105f61bb` passed Governance #250 (**288/288 Ubuntu**, **61/61 Windows HIGH_ASSURANCE**) and Desktop Shell #86 (security gate, frontend **23/23**, npm audit 0, locked Rust checks, Windows release build and launch smoke). HEDS technical review `5216093993` is **APPROVED FOR PROMOTION**, unresolved HIGH/CRITICAL `0`.

`HCODER-WO-0019-CR-001` LOW and `HCODER-WO-0019-CR-002` LOW are resolved. `HCODER-CP-0019` and `DEC-023 — Runtime Status Sidecar Helper Boundary` are promotion candidates only, **NOT CANONICAL**.

Historical PR #38 / branch `feat/HCODER-WO-0019-runtime-status-sidecar` is non-authoritative supporting evidence only. It MUST NOT be merged or cherry-picked.

WO-0019 authority remains presentation-only and one-shot: fixed `--stdio-status-v1`, canonical CP-0018 request/response, prebuilt truthful `DISCONNECTED` snapshot, no daemon/listener/generic RPC, no provider/model calls, no credential access, no Permission & Control Plane mutation, no filesystem/Git/computer-use mutation, no remote control and no billing/purchase authority. Desktop/Tauri process spawn is explicitly out of scope.

### NEXT EXACT ACTIONS
1. Validate the promotion candidate exact head with Governance + Desktop Shell.
2. Perform HEDS promotion review; stop on unresolved HIGH/CRITICAL.
3. If approved, create the minimum final-approval state mutation without declaring CP-0019 canonical.
4. Run final exact-head Governance + Desktop Shell and HEDS.
5. Mark PR #48 ready only after all final gates are green.
6. Squash merge using expected-head protection.
7. Require push-triggered Governance + Desktop Shell success on the product merge SHA.
8. Create documentation-only canonical closeout, gate/HEDS it, squash merge, and require push validation before CP-0019 is fully sealed.
9. Only after canonical CP-0019, source-check and reconstruct WO-0020; never merge its historical stacked ancestry directly.
10. Refresh Issue #30 at each major state transition.
