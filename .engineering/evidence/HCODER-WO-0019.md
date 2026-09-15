# Evidence Bundle — HCODER-WO-0019

**Work Order:** `HCODER-WO-0019 — Runtime Status Sidecar Helper`  
**Issue:** `#47`  
**PR:** `#48`  
**Canonical base:** `HCODER-CP-0018` / `c0a44d43546b9f176125b9e7099b8422d6b62ba3`  
**Technical exact head:** `ba10ba72f76316806cd820dc0d205e68105f61bb`  
**HEDS technical review:** `5216093993` — APPROVED FOR PROMOTION, unresolved HIGH/CRITICAL `0`

## Scope receipt
The technical delta reconstructs WO-0019 directly on canonical CP-0018. Historical PR #38 / branch `feat/HCODER-WO-0019-runtime-status-sidecar` is non-authoritative supporting evidence only and was not merged or cherry-picked.

The product implementation adds only a fixed Hive-owned Python helper at `tools/runtime/status_sidecar.py` plus process-level tests. The helper accepts exactly `--stdio-status-v1`, constructs a prebuilt `disconnected_snapshot()`, delegates one request to canonical CP-0018 `serve_one(...)`, emits one canonical response and exits.

No desktop/Tauri launcher, daemon/listener, socket, generic RPC, dynamic command dispatch, provider/model call, credential lookup, task/permission mutation, filesystem/Git/terminal/computer-use mutation, remote control, automatic skill activation or billing/purchase path is added.

## Process-boundary proof
`tests/runtime/test_runtime_status_sidecar.py` proves through canonical `ManagedStdioProcess`:
- accepted wire is produced by `encode_request()` and admitted by `parse_response()`;
- two buffered canonical requests produce only the first response before process exit;
- successful default snapshot is truthful `DISCONNECTED`;
- missing, unknown and extra mode args exit `64` with empty stdout/stderr;
- malformed JSON, noncanonical JSON, duplicate keys, future protocol, unsupported operation, oversized request and missing newline exit `65` without a fake snapshot or error-detail output;
- `OPENAI_API_KEY` is excluded by the allowlisted child environment and absent from sidecar output;
- child launch remains `shell=False` through `ManagedStdioProcess`;
- process/pipe cleanup remains ResourceWarning-clean.

## Corrections
- `HCODER-WO-0019-CR-001` LOW: process-boundary coverage gap. **RESOLVED** by test-only expansion; implementation/protocol unchanged.
- `HCODER-WO-0019-CR-002` LOW: Windows proof gap. **RESOLVED** by adding the same sidecar process suite to the existing Windows HIGH_ASSURANCE subset; product implementation unchanged.

## Exact-head Governance receipt
Governance #250, run `35027148143`, on exact `ba10ba72f76316806cd820dc0d205e68105f61bb`: **SUCCESS**.
- Ubuntu source-pack: **288/288 PASS** with `PYTHONWARNINGS=error::ResourceWarning`.
- Windows Server 2025 HIGH_ASSURANCE: **61/61 PASS** with `PYTHONWARNINGS=error::ResourceWarning`; the expanded subset includes `tests.runtime.test_runtime_status_sidecar`.
- Exact-head checkout was verified in both jobs.

## Exact-head Desktop receipt
Desktop Shell #86, run `35027148075`, on exact `ba10ba72f76316806cd820dc0d205e68105f61bb`: **SUCCESS**.
- Desktop security gate: **PASS**.
- `CAPABILITY_PERMISSIONS=0`.
- `GENERIC_PROCESS_EXECUTION=0`.
- `FILESYSTEM_MUTATION_PRIMITIVES=0`.
- Frontend component/contract tests: **23/23 PASS**.
- TypeScript typecheck: PASS.
- Vite production build: PASS.
- npm audit: **0 vulnerabilities**.
- locked RustSec audit, Rust tests and `cargo check --locked`: PASS.
- Tauri Windows release build: PASS.
- `DESKTOP_LAUNCH_SMOKE=PASS`.

## HEDS receipt
Technical HEDS review `5216093993` audited the exact technical head after all mandatory gates and returned **APPROVED FOR PROMOTION** with unresolved HIGH/CRITICAL findings **0**.

## Residual boundary
Technical approval does not attest:
- a packaged/signed/authenticated production helper binary;
- desktop child-process launch, supervision, restart, shutdown or containment policy;
- a trusted live runtime observer or live provider connectivity;
- provider reachability/authentication or VERIFIED model capability;
- any new Permission & Control Plane or mutation authority.

The helper currently exports a truthful disconnected presentation snapshot only. CP-0019 promotion must preserve these limits. Existing RustSec warning-class transitive dependency debt is unchanged.
