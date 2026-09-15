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
Canonical checkpoint: `HCODER-CP-0018` on `main` at `c0a44d43546b9f176125b9e7099b8422d6b62ba3`.

CP-0018 closeout is sealed: product PR #45 and closeout PR #46 were squash-merged; final closeout HEDS review `5215922407` had unresolved HIGH/CRITICAL `0`; push Governance #246 and Desktop Shell #82 passed on the canonical main SHA, including Tauri Windows release build and launch smoke.

Active increment: `HCODER-WO-0019 — Runtime Status Sidecar Helper`, Issue `#47`, canonical branch `feat/HCODER-WO-0019-runtime-status-sidecar-canonical`.

Historical PR #38 / branch `feat/HCODER-WO-0019-runtime-status-sidecar` is non-authoritative supporting evidence only. It MUST NOT be merged or cherry-picked because it predates final CP-0018 protocol hardening.

WO-0019 authority remains presentation-only and one-shot: fixed `--stdio-status-v1`, canonical CP-0018 request/response, truthful default `DISCONNECTED`, no daemon/listener/generic RPC, no provider/model calls, no credential access, no Permission & Control Plane mutation, no filesystem/Git/computer-use mutation, no remote control and no billing/purchase authority. Desktop/Tauri process spawn is explicitly out of scope.

### NEXT EXACT ACTIONS
1. Materialize the reconstructed WO-0019 Work Order, Context Lock, sidecar and process-level tests on the canonical branch.
2. Open a draft PR against `main` and require exact-head Governance + Desktop Shell success.
3. Produce evidence and perform HEDS exact-head review; stop on unresolved HIGH/CRITICAL findings.
4. Apply any correction delta on the same Work Order and repeat exact-head gates.
5. Promote CP-0019/decision documentation only after technical proof if warranted.
6. Squash merge using expected-head protection.
7. Require push-triggered Governance + Desktop Shell success on canonical `main` before CP-0019 closeout.
8. Refresh Issue #30 at each major state transition.
