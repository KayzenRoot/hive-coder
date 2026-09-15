# Checkpoint Delta — HCODER-WO-0019

**Source checkpoint:** `HCODER-CP-0018` — APPROVED / CANONICAL  
**Proposed checkpoint:** `HCODER-CP-0019` — PROMOTION CANDIDATE / NOT CANONICAL  
**Technical exact head:** `ba10ba72f76316806cd820dc0d205e68105f61bb`  
**HEDS technical:** `5216093993` — APPROVED FOR PROMOTION, unresolved HIGH/CRITICAL `0`

## Delta
- Add a fixed Hive-owned runtime-status sidecar entrypoint with sole mode `--stdio-status-v1`.
- Sidecar constructs canonical `disconnected_snapshot()` before entering CP-0018 `serve_one(...)`.
- One process invocation handles one bounded canonical request, emits one canonical response and exits.
- Stable expected-failure exit codes are `64` for invalid mode arguments and `65` for invalid protocol input.
- Process-level acceptance is proven through canonical `ManagedStdioProcess`, preserving `shell=False` and the allowlisted child environment.
- Representative ambient provider credential material is proven not inherited or emitted.
- Windows HIGH_ASSURANCE now includes the status-sidecar process suite.

## Corrections resolved
- `HCODER-WO-0019-CR-001` LOW — process-level adversarial/one-shot coverage.
- `HCODER-WO-0019-CR-002` LOW — Windows HIGH_ASSURANCE inclusion.

## Unchanged authority
CP-0019 candidate adds no desktop process launcher/supervisor, provider/model execution, credential authority, task/permission mutation, filesystem/Git/terminal/computer-use mutation, remote control, automatic skill activation or billing/purchase authority. Status remains presentation-only and cannot mint/consume Permission & Control Plane permits.

## Evidence
- Governance #250 (`35027148143`): **288/288 Ubuntu PASS**, **61/61 Windows HIGH_ASSURANCE PASS** on exact technical head.
- Desktop Shell #86 (`35027148075`): security gate PASS, frontend **23/23 PASS**, npm audit 0, locked Rust checks/audits PASS, Windows release build + launch smoke PASS.
- HEDS technical review `5216093993`: **APPROVED FOR PROMOTION**, H/C 0.

## Promotion conditions
`HCODER-CP-0019` remains **NOT CANONICAL** until promotion/final exact-head Governance + Desktop Shell gates, HEDS with unresolved HIGH/CRITICAL 0, squash merge with expected-head protection, and post-merge push validation on `main` complete successfully.
