# Checkpoint — Hive Coder

**Checkpoint:** `HCODER-CP-0019`  
**Status:** PROMOTION CANDIDATE / NOT CANONICAL  
**Date:** 2026-09-15  
**Repository:** `KayzenRoot/hive-coder`  
**Work Order:** `HCODER-WO-0019` — TECHNICALLY APPROVED / PROMOTION CANDIDATE  
**Issue:** `#47` — OPEN  
**PR:** `#48` — DRAFT  
**Base checkpoint:** `HCODER-CP-0018` — APPROVED / CANONICAL  
**Canonical base main SHA:** `c0a44d43546b9f176125b9e7099b8422d6b62ba3`  
**Technical exact head:** `ba10ba72f76316806cd820dc0d205e68105f61bb`  
**Technical HEDS:** `5216093993`

> This checkpoint is a promotion candidate only. Canonical project truth on `main` remains CP-0018 until WO-0019 is merged and post-merge validated.

## Candidate product state
- All CP-0005 through CP-0018 permission/security/status boundaries remain authoritative and unchanged.
- Hive owns a fixed Python status-sidecar helper at `tools/runtime/status_sidecar.py`.
- The helper admits exactly one mode, `--stdio-status-v1`.
- A valid invocation constructs a prebuilt canonical `disconnected_snapshot()`, passes it to CP-0018 `serve_one(...)`, consumes one canonical newline-framed request, emits one canonical response and exits.
- Invalid/missing/extra mode arguments return stable exit `64` with no protocol output.
- Invalid protocol input returns stable exit `65` with no fake snapshot or payload-derived stderr detail.
- Accepted status wire remains exactly `hive-runtime-status-ipc-v1` / `status.snapshot`; CP-0019 does not add or widen RPC operations.
- Default runtime/provider/task/permission truth remains disconnected/empty as defined by the canonical snapshot. The helper does not claim a live runtime connection.
- Process-level tests launch through canonical `ManagedStdioProcess`, which keeps `shell=False` and a least-privilege allowlisted child environment.
- The WO-0019 sidecar process spec supplies no environment overrides; representative ambient `OPENAI_API_KEY` is proven excluded and absent from response output.
- Windows HIGH_ASSURANCE now executes the sidecar process suite in addition to the existing control-plane/Cua contracts.

## One-shot and fail-closed proof
Exact process-level tests prove:
- two buffered canonical requests yield only the first response before process exit;
- accepted request uses canonical `encode_request()` and response passes canonical `parse_response()`;
- malformed, noncanonical, duplicate-key, future-protocol, unsupported-operation, oversized and missing-newline input is rejected at the executable boundary;
- no expected invalid case emits protocol stdout or payload/secret stderr;
- process resources are ResourceWarning-clean on Ubuntu and Windows.

## Corrections
- `HCODER-WO-0019-CR-001` LOW — **RESOLVED**: expanded process-level adversarial rejection and explicit buffered-second-request one-shot proof.
- `HCODER-WO-0019-CR-002` LOW — **RESOLVED**: sidecar suite added to Windows HIGH_ASSURANCE exact-head validation.

Neither correction altered the frozen CP-0018 protocol or expanded product authority.

## Technical exact-head proof
On exact `ba10ba72f76316806cd820dc0d205e68105f61bb`:
- Governance #250 (`35027148143`): **SUCCESS**.
  - Ubuntu source-pack: **288/288 PASS**, ResourceWarning fatal.
  - Windows Server 2025 HIGH_ASSURANCE: **61/61 PASS**, ResourceWarning fatal, including sidecar process tests.
- Desktop Shell #86 (`35027148075`): **SUCCESS**.
  - desktop security gate PASS;
  - frontend **23/23 PASS**;
  - npm audit **0 vulnerabilities**;
  - locked RustSec audit/tests/check PASS;
  - Tauri Windows release build PASS;
  - `DESKTOP_LAUNCH_SMOKE=PASS`.
- HEDS technical review `5216093993`: **APPROVED FOR PROMOTION**, unresolved HIGH/CRITICAL **0**.

## Candidate decision
`DEC-023 — Runtime Status Sidecar Helper Boundary` is staged as **PROMOTION CANDIDATE / NOT CANONICAL**. It defines only the fixed one-shot helper/process contract and preserves CP-0018 presentation-only authority.

## Explicit residual boundaries
- No Tauri/desktop child-process launcher or supervisor is approved by WO-0019.
- No generic process capability or caller-selected executable/argument dispatch is approved.
- Helper packaging/signing/binary authenticity/update provenance is unproven.
- Automatic restart/shutdown/health supervision and containment policy remain unproven.
- No live trusted runtime/provider/task/permission observer is connected; the helper truth is intentionally `DISCONNECTED`.
- Provider READY/reachability/authentication and VERIFIED model capability remain separate concerns.
- No new Permission & Control Plane, filesystem/Git/terminal/computer-use, remote-control, skill-activation or billing/purchase authority exists.
- Existing seven RustSec warning-class transitive advisories remain dependency debt.
- Existing desktop CSP, native/full interaction E2E, visual/accessibility, privileged capability-I/O, installer/signing/updater and final-license residuals remain unchanged.

## Promotion / canonicalization gate
CP-0019 remains **NOT CANONICAL** until:
1. this promotion candidate passes exact-head Governance + Desktop Shell;
2. HEDS promotion reports unresolved HIGH/CRITICAL 0;
3. any final approval mutation passes its own exact-head gates and final HEDS;
4. PR #48 is marked ready only after those gates;
5. squash merge uses expected-head protection;
6. push-triggered Governance + Desktop Shell pass on the resulting `main` merge SHA;
7. canonical closeout records the merge/post-merge receipts without expanding authority.

## Next NECESSARY governed increment after canonical CP-0019
`HCODER-WO-0020 — Desktop Runtime Status Supervisor & System Truth Surface` remains blocked until CP-0019 becomes canonical. Historical stacked WO-0020 work, if present, is supporting evidence only and must be reconstructed against the canonical predecessor rather than merged directly.
