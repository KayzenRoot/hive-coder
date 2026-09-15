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
Canonical `main` remains `HCODER-CP-0019` at `e4bc74d1ae6c4054cd98cd34b16e6357f911224c` until WO-0020 completes product merge, post-merge validation and canonical closeout.

Active increment: `HCODER-WO-0020 — Desktop Runtime Status Supervisor & System Truth Surface`, Issue `#51`, PR `#54`, branch `feat/HCODER-WO-0020-desktop-runtime-status-supervisor-canonical`.

Technical exact head `86c6e956985e0b51e0f56b3568a3fe9db61fef90` passed Governance #263 (**288/288 Ubuntu + 61/61 Windows HIGH_ASSURANCE**) and Desktop Shell #99 (security gate PASS, frontend **26/26**, npm audit 0, Rust **13/13**, locked RustSec/check, Windows release build and launch smoke). HEDS technical review `5216871217` is **APPROVED FOR PROMOTION CANDIDATE**, unresolved HIGH/CRITICAL `0`.

`HCODER-WO-0020-CR-001` MEDIUM and `HCODER-WO-0020-CR-002` MEDIUM are resolved. `HCODER-CP-0020` and `DEC-024 — Desktop Runtime Status Supervisor Boundary` are promotion candidates only, **NOT CANONICAL**.

Historical PR #39 / branch `feat/HCODER-WO-0020-desktop-runtime-status-bridge` is non-authoritative supporting evidence only and MUST NOT be merged or cherry-picked.

WO-0020 authority remains presentation-only: exactly one fixed child-process site, fixed sibling basename, fixed `--stdio-status-v1`, cleared child environment, canonical request/33,024-byte response ceiling, strict raw decoder, argument-free main-window Tauri command and read-only Runtime/Provider/Task/Permission System Truth. No generic process/shell capability, caller-controlled process input, provider/model execution, credential authority, task/permission/filesystem/Git/terminal/computer-use mutation, remote control, skill activation or billing/purchase authority exists.

### NEXT EXACT ACTIONS
1. Commit documentation/evidence-only CP-0020 promotion candidate.
2. Run exact-head Governance + Desktop Shell on the promotion head.
3. Perform HEDS promotion review; stop on unresolved HIGH/CRITICAL.
4. If approved, create a minimal final-approval state mutation without declaring CP-0020 canonical.
5. Run final exact-head Governance + Desktop Shell + HEDS.
6. Squash merge PR #54 with expected-head protection.
7. Require push-triggered Governance + Desktop Shell on the product merge SHA.
8. Create documentation-only canonical closeout, gate/HEDS it, squash merge, and require push validation.
9. Refresh Issue #30 at each major state transition.
10. Only after fully canonical CP-0020, run a fresh source-check for the next NECESSARY increment.
