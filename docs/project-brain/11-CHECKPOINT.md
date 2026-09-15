# Checkpoint — Hive Coder

**Checkpoint:** `HCODER-CP-0020`  
**Status:** FINAL APPROVAL CANDIDATE / NOT CANONICAL  
**Date:** 2026-09-15  
**Repository:** `KayzenRoot/hive-coder`  
**Work Order:** `HCODER-WO-0020 — Desktop Runtime Status Supervisor & System Truth Surface` — APPROVED FOR SQUASH MERGE / NOT CANONICAL  
**Issue:** `#51` — OPEN  
**PR:** `#54` — DRAFT UNTIL FINAL GATES  
**Base checkpoint:** `HCODER-CP-0019` — APPROVED / CANONICAL  
**Canonical base main SHA:** `e4bc74d1ae6c4054cd98cd34b16e6357f911224c`  
**Technical head:** `86c6e956985e0b51e0f56b3568a3fe9db61fef90`  
**Technical HEDS:** `5216871217`  
**Promotion head:** `bf76c2a451763d7bc361437028e819d2df5f97ba`  
**Promotion HEDS:** `5216925860`

> CP-0020 is approved only for the final pre-merge validation path. Canonical project truth remains CP-0019 until product merge, post-merge validation and canonical closeout all complete.

## Candidate product state
- All CP-0005 through CP-0019 permission/security/status boundaries remain authoritative and unchanged.
- Hive desktop adds one fixed Rust runtime-status supervisor process site only.
- Helper identity is derived from the current desktop executable sibling plus a fixed platform basename; symlink/reparse/non-file targets fail closed.
- Sole helper mode is `--stdio-status-v1`; frontend/model/task text supplies no process identity, path, args or environment.
- Child environment is cleared. stdin/stdout are piped, stderr discarded, timeout is bounded and post-spawn failures terminate/wait the child.
- Request is exact canonical CP-0018 `status.snapshot` for request id `desktop-runtime`; response ceiling is exactly `33,024` bytes.
- One argument-free Tauri command `get_runtime_status_envelope` is authorized only for the existing `main` window.
- Frontend admits raw status only through `decodeRuntimeStatusEnvelope(raw)`; semantic or `JSON.parse(raw)` bypass is rejected by the security gate.
- Runtime/Provider/Task/Permission System Truth remains read-only presentation state. Mutation controls remain unavailable.

## Security-gate truth
Exact technical head reports:
- `TAURI_COMMANDS=choose_workspace,get_desktop_snapshot,get_runtime_status_envelope`
- `FRONTEND_INVOKES=3`
- `CAPABILITY_PERMISSIONS=0`
- `RUNTIME_STATUS_ARGS=0`
- `RUNTIME_STATUS_RAW_DECODER=STRICT`
- `FILESYSTEM_MUTATION_PRIMITIVES=0`
- `GENERIC_PROCESS_EXECUTION=0`
- `FIXED_RUNTIME_SIDECAR_PROCESS=1`

## Corrections
- `HCODER-WO-0020-CR-001` MEDIUM — **RESOLVED**: unknown permission counters are not rendered as observed zeroes; canonical subsystem provenance is preserved.
- `HCODER-WO-0020-CR-002` MEDIUM — **RESOLVED**: the single fixed process boundary and raw decoder invariants are statically enforced.

## Technical proof
Exact `86c6e956985e0b51e0f56b3568a3fe9db61fef90`:
- Governance #263 (`35035152518`): **SUCCESS** — Ubuntu **288/288 PASS**, Windows HIGH_ASSURANCE **61/61 PASS**.
- Desktop Shell #99 (`35035152526`): **SUCCESS** — security gate PASS, frontend **26/26 PASS**, npm audit 0, RustSec locked audit executed over 432 dependencies, Rust **13/13 PASS**, `cargo check --locked` PASS, Windows release build PASS and `DESKTOP_LAUNCH_SMOKE=PASS`.
- HEDS technical `5216871217`: **APPROVED FOR PROMOTION CANDIDATE**, unresolved HIGH/CRITICAL **0**.

## Promotion proof
Exact `bf76c2a451763d7bc361437028e819d2df5f97ba`:
- promotion delta from technical head: exactly 7 documentation/evidence/governance files and no product/runtime/workflow/dependency/capability change;
- Governance #264 (`35035821821`): **SUCCESS** — Ubuntu **288/288 PASS**, Windows HIGH_ASSURANCE **61/61 PASS**;
- Desktop Shell #100 (`35035821714`): **SUCCESS** — strict security gate PASS, frontend **26/26 PASS**, locked Rust audit/tests/check PASS, Windows release build and launch smoke PASS;
- HEDS promotion `5216925860`: **APPROVED FOR FINAL APPROVAL MUTATION**, unresolved HIGH/CRITICAL **0**.

## Candidate decision
`DEC-024 — Desktop Runtime Status Supervisor Boundary` is **APPROVED FOR SQUASH MERGE / NOT CANONICAL**. It authorizes no generic process capability and no mutation authority.

## Explicit residual boundaries
- Sidecar packaging/signing/binary attestation/update provenance is not proven.
- Hosted launch smoke proves desktop startup/fail-closed behavior, not a packaged live sidecar session.
- No automatic polling daemon, restart/health manager or generic process supervisor is approved.
- Provider reachability/authentication and VERIFIED model capability remain separate evidence domains.
- No new Permission & Control Plane, task mutation, filesystem/Git/terminal/computer-use, remote-control, skill-activation or billing/purchase authority exists.
- Seven RustSec warning-class dependency advisories remain explicit debt.
- Existing CSP, native/full E2E, visual/accessibility, installer/signing/updater and final-license residuals remain unchanged.

## Final merge gate
CP-0020 remains **NOT CANONICAL** until:
1. this final approval head passes exact-head Governance + Desktop Shell;
2. final HEDS reports unresolved HIGH/CRITICAL 0;
3. PR #54 is squash-merged with expected-head protection;
4. the product merge SHA passes push Governance + Desktop Shell;
5. a documentation-only canonical closeout records those receipts, passes its own exact-head Governance + Desktop Shell + HEDS, is squash-merged, and the resulting `main` SHA passes push validation.

## Next governed increment
Do not select the next product increment until CP-0020 is fully canonical. Source-check must run again after closeout rather than inferring the next Work Order from historical branches.