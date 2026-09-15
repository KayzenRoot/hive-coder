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
Canonical `main` is `HCODER-CP-0019` at `e4bc74d1ae6c4054cd98cd34b16e6357f911224c` until WO-0020 is fully promoted and closed out.

Active increment: `HCODER-WO-0020 — Desktop Runtime Status Supervisor & System Truth Surface`, Issue `#51`, branch `feat/HCODER-WO-0020-desktop-runtime-status-supervisor-canonical`.

Historical PR #39 / branch `feat/HCODER-WO-0020-desktop-runtime-status-bridge` is non-authoritative supporting evidence only and MUST NOT be merged or cherry-picked.

WO-0020 authority is presentation-only: exactly one fixed sidecar supervisor process site, fixed sibling basename, fixed `--stdio-status-v1`, cleared child environment, canonical CP-0018 request, bounded output, strict raw-wire decoder, argument-free Tauri command, and read-only Runtime/Provider/Task/Permission System Truth. No generic process/shell capability, caller-controlled process path/args/env, provider/model execution, credential authority, task/permission mutation, filesystem/Git/terminal/computer-use mutation, remote control, skill activation or billing/purchase authority is allowed.

### NEXT EXACT ACTIONS
1. Validate the exact technical head with Governance + Desktop Shell.
2. Perform HEDS technical review; stop on unresolved HIGH/CRITICAL.
3. Same-WO corrections only if findings exist.
4. If approved, create Evidence Bundle + governed promotion candidate without declaring CP-0020 canonical.
5. Run promotion and final exact-head gates/HEDS.
6. Squash merge with expected-head protection, require post-merge Governance + Desktop Shell, then documentation-only canonical closeout and push validation.
7. Refresh Issue #30 at each major state transition.
