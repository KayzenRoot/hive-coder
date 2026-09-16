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
`HCODER-CP-0020 — Desktop Runtime Status Supervisor & System Truth Surface` is **APPROVED / CANONICAL subject only to the documentation-only closeout seal**.

Product receipts:
- Issue #51 CLOSED / COMPLETED.
- Product PR #54 SQUASH MERGED with expected-head protection.
- Final reviewed head `344130199536e33a656d49a365e746610f89e245` passed Governance #265 (**288/288 Ubuntu + 61/61 Windows HIGH_ASSURANCE**) and Desktop Shell #101 (security gate, frontend **26/26**, npm audit 0, Rust **13/13**, locked RustSec/check, Windows release build and launch smoke).
- Final HEDS `5217039528`: APPROVED FOR SQUASH MERGE, unresolved HIGH/CRITICAL 0.
- GitHub-signed product merge `621732c00ba1f3325272dfa1631fddbbabf3dfc4` passed post-merge Governance #266 (**288/288 + 61/61**) and Desktop Shell #102, including release build and launch smoke.
- `DEC-024 — Desktop Runtime Status Supervisor Boundary` is APPROVED / CANONICAL subject only to closeout seal.
- `HCODER-WO-0020-CR-001` MEDIUM and `HCODER-WO-0020-CR-002` MEDIUM are RESOLVED.

CP-0020 authority remains presentation-only: exactly one fixed child-process site, fixed sibling basename, fixed `--stdio-status-v1`, cleared child environment, canonical request/33,024-byte response ceiling, strict raw decoder, argument-free main-window Tauri command and read-only Runtime/Provider/Task/Permission System Truth. No generic process/shell capability, caller-controlled process input, provider/model execution, credential authority, task/permission/filesystem/Git/terminal/computer-use mutation, remote control, skill activation or billing/purchase authority exists.

### NEXT EXACT ACTIONS
1. Complete the documentation-only CP-0020 closeout from product merge `621732c00ba1f3325272dfa1631fddbbabf3dfc4`.
2. Require exact-head Governance + Desktop Shell on the closeout head.
3. Perform closeout HEDS; stop on unresolved HIGH/CRITICAL.
4. Squash merge closeout with expected-head protection.
5. Require push-triggered Governance + Desktop Shell on the resulting `main` SHA.
6. Refresh Issue #30 with the fully sealed CP-0020 receipts.
7. Only then run a fresh canonical source-check and select the next NECESSARY increment. Do not infer it from historical branches.