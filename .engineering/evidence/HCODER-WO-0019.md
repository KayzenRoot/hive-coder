# Evidence Bundle — HCODER-WO-0019

**Work Order:** `HCODER-WO-0019 — Runtime Status Sidecar Helper`  
**Issue:** `#47`  
**PR:** `#48`  
**Canonical base:** `HCODER-CP-0018` / `c0a44d43546b9f176125b9e7099b8422d6b62ba3`  
**Technical exact head:** `ba10ba72f76316806cd820dc0d205e68105f61bb`  
**Technical HEDS:** `5216093993` — APPROVED FOR PROMOTION, H/C `0`  
**Promotion exact head:** `55975e7e97eb33d2b695d02e36ab6994fa7ae7b5`  
**Promotion HEDS:** `5216180277` — APPROVED FOR FINAL APPROVAL MUTATION, H/C `0`

## Scope receipt
WO-0019 was reconstructed directly on canonical CP-0018. Historical PR #38 / branch `feat/HCODER-WO-0019-runtime-status-sidecar` is non-authoritative evidence only and was not merged or cherry-picked.

The product implementation adds only the fixed Hive-owned Python helper `tools/runtime/status_sidecar.py` plus process-level tests. The helper accepts exactly `--stdio-status-v1`, constructs a prebuilt `disconnected_snapshot()`, delegates one request to canonical CP-0018 `serve_one(...)`, emits one canonical response and exits.

No desktop/Tauri launcher, daemon/listener, socket, generic RPC, dynamic command dispatch, provider/model call, credential lookup, task/permission mutation, filesystem/Git/terminal/computer-use mutation, remote control, automatic skill activation or billing/purchase path is added.

## Process-boundary proof
`tests/runtime/test_runtime_status_sidecar.py` proves through canonical `ManagedStdioProcess`:
- accepted wire is produced by `encode_request()` and admitted by `parse_response()`;
- two buffered canonical requests produce only the first response before process exit;
- successful default snapshot is truthful `DISCONNECTED`;
- missing, unknown and extra mode args exit `64` with empty stdout/stderr;
- malformed JSON, noncanonical JSON, duplicate keys, future protocol, unsupported operation, oversized request and missing newline exit `65` without fake snapshot or error-detail output;
- `OPENAI_API_KEY` is excluded by the allowlisted child environment and absent from sidecar output;
- child launch remains `shell=False` through `ManagedStdioProcess`;
- process/pipe cleanup remains ResourceWarning-clean.

## Corrections
- `HCODER-WO-0019-CR-001` LOW: process-boundary coverage gap. **RESOLVED** by test-only expansion; implementation/protocol unchanged.
- `HCODER-WO-0019-CR-002` LOW: Windows proof gap. **RESOLVED** by adding the same sidecar process suite to the existing Windows HIGH_ASSURANCE subset; product implementation unchanged.

## Technical exact-head receipt
Governance #250 (`35027148143`) on exact `ba10ba72f76316806cd820dc0d205e68105f61bb`: **SUCCESS**.
- Ubuntu source-pack: **288/288 PASS**, ResourceWarning fatal.
- Windows Server 2025 HIGH_ASSURANCE: **61/61 PASS**, including status-sidecar tests, ResourceWarning fatal.

Desktop Shell #86 (`35027148075`) on the same exact head: **SUCCESS**.
- desktop security gate PASS; capability permissions 0; generic process execution 0; filesystem mutation primitives 0;
- frontend **23/23 PASS**; typecheck/build PASS; npm audit **0 vulnerabilities**;
- locked RustSec audit/tests/check PASS;
- Tauri Windows release build + launch smoke PASS.

HEDS technical `5216093993`: **APPROVED FOR PROMOTION**, H/C 0.

## Promotion exact-head receipt
Promotion delta from the technical head was one documentation/evidence/governance-only commit touching 11 files and no runtime/product/workflow implementation.

Governance #251 (`35027937017`) on exact `55975e7e97eb33d2b695d02e36ab6994fa7ae7b5`: **SUCCESS**.
- Ubuntu **288/288 PASS**.
- Windows HIGH_ASSURANCE **61/61 PASS**, including sidecar tests.

Desktop Shell #87 (`35027937071`) on the same exact promotion head: **SUCCESS**, including desktop-web gates, locked Rust checks, Tauri Windows release build and launch smoke.

HEDS promotion `5216180277`: **APPROVED FOR FINAL APPROVAL MUTATION**, unresolved HIGH/CRITICAL 0.

## Residual boundary
Approval does not attest packaged/signed helper authenticity, desktop child-process launch/supervision, restart/shutdown/containment, a live trusted runtime observer, provider reachability/authentication, VERIFIED model capability or any new mutation/permission authority. The helper intentionally exports a truthful disconnected presentation snapshot only. Existing RustSec warning-class dependency debt and existing desktop hardening/release residuals remain unchanged.

## Final gate state
This evidence bundle is now staged for the final approval candidate. CP-0019 and DEC-023 remain **NOT CANONICAL** until the final branch head passes exact-head Governance + Desktop Shell and HEDS, PR #48 is squash-merged with expected-head protection, and the resulting `main` product SHA passes push validation followed by documentation-only canonical closeout.
