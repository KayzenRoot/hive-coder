# HCODER-WO-0019 — Runtime Status Sidecar Helper

**Status:** APPROVED FOR EXECUTION  
**Risk:** ELEVATED  
**Task class:** T3  
**Context radius:** C3  
**Canonical base:** `HCODER-CP-0018` on `main` at `c0a44d43546b9f176125b9e7099b8422d6b62ba3`  
**Issue:** `#47`  
**Historical evidence only:** PR `#38` / branch `feat/HCODER-WO-0019-runtime-status-sidecar` MUST NOT be merged or cherry-picked.

## OBJECTIVE
Create the fixed Hive-owned runtime-status sidecar process contract that serves exactly one canonical CP-0018 status request over stdio, emits exactly one canonical response, and exits without provider calls, model execution, credentials, permission/task mutation or desktop authority.

## CONTEXT
CP-0017 canonicalized the bounded non-authoritative runtime status model. CP-0018 canonicalized the strict `hive-runtime-status-ipc-v1` one-shot wire protocol with sole `status.snapshot` operation. The next NECESSARY increment is the helper process boundary itself, independently of any Tauri/desktop process launcher.

The historical stacked implementation in PR #38 predates final CP-0018 hardening and is supporting evidence only. Reconstruction on canonical CP-0018 MUST correct two incompatibilities: `serve_one(...)` now receives a prebuilt `RuntimeStatusSnapshot`, and valid process requests MUST use canonical `encode_request(...)` bytes rather than ad-hoc JSON encoding.

## SCOPE
- Add a single-purpose sidecar entrypoint accepting exactly `--stdio-status-v1`.
- Read exactly one bounded canonical request from stdin.
- Emit exactly one bounded canonical response to stdout.
- Exit after one request.
- Reuse the canonical runtime status and runtime status protocol implementation.
- Default to truthful `DISCONNECTED` state using a prebuilt `disconnected_snapshot()`.
- Add process-level tests using Hive's shell-free `ManagedStdioProcess`.
- Reconcile stale cross-chat execution state in `AGENTS.md`.

## OUT OF SCOPE
Desktop/Tauri process spawn, generic process launcher, daemon/service lifecycle, sockets, HTTP/WebSocket/listeners, provider/network/model calls, credentials, prompt/model output, task/permission mutation, filesystem/Git mutation, terminal/Cua/remote-control/billing/purchase authority, installer/signing/release packaging.

## FILES / SOURCES TO READ
- `docs/project-brain/11-CHECKPOINT.md`
- `docs/project-brain/10-DECISIONS-LEDGER.md`
- `docs/project-brain/04-ARCHITECTURE.md`
- `docs/project-brain/05-SECURITY.md`
- `docs/project-brain/13-INTEGRATION-CONTRACTS.md`
- `docs/project-brain/contracts/RUNTIME-STATUS-IPC-V1.md`
- `hive_runtime/process.py`
- `hive_runtime/runtime_status.py`
- `hive_runtime/runtime_status_protocol.py`
- historical PR #38 files only as non-authoritative evidence

## REQUIREMENTS
1. Accept exactly one mode flag: `--stdio-status-v1`. Missing, unknown or extra args return stable usage exit code `64` with no protocol output.
2. Construct the truthful presentation snapshot before protocol service using `disconnected_snapshot()` and pass that object to `serve_one(...)`.
3. Handle one request only, emit one response only, then exit `0`.
4. Malformed, duplicate-key, non-canonical, unsupported, missing-newline or oversized input fails closed with stable protocol exit code `65` and no fake snapshot.
5. Do not introduce shell invocation, generic command dispatch, dynamic executable selection, listener, socket or generic RPC namespace.
6. Expected invalid input must not echo payload details, status data, secrets or environment values to stderr.
7. Process-level tests must launch through canonical `ManagedStdioProcess`, preserving `shell=False` and its allowlisted child environment.
8. Ambient provider/API credentials are neither required nor inherited by the managed child environment; tests must prove representative secret keys are excluded from that environment and absent from sidecar output.
9. Valid tests MUST use canonical `encode_request(...)`; returned wire MUST pass canonical `parse_response(...)`.
10. Default status remains `DISCONNECTED`, never fabricated `READY`; presentation state cannot authorize execution or mint/consume Permission & Control Plane permits.

## ARCHITECTURE RULES
`future trusted desktop supervisor -> fixed Hive sidecar -> CP-0018 one-shot protocol -> CP-0017 presentation snapshot`.

The sidecar transports presentation state only. It is not an authority boundary, does not launch providers/models, and cannot create execution authority.

## CONSTRAINTS
Python stdlib + existing Hive runtime only. No new dependency, daemon/listener, port binding, generic RPC, provider SDK/network, credential environment lookup, desktop capability or mutation surface.

## ACCEPTANCE CRITERIA
- Valid canonical process roundtrip returns one `DISCONNECTED` envelope, produces no second response, no stderr, and exits `0`.
- Missing/unknown/extra mode is rejected with `64`, no stdout and no stderr.
- Malformed, non-canonical and oversized requests are rejected with `65`, no snapshot/stdout and no stderr.
- Representative ambient API secret is excluded by `safe_child_environment()` and absent from process output.
- Existing Governance and Desktop Shell suites remain green on the exact head.
- HEDS has no unresolved HIGH/CRITICAL findings.

## TESTS
- Canonical process roundtrip + canonical response parse.
- One-shot/no-second-output proof.
- Missing/unknown/extra mode rejection.
- Malformed request rejection.
- Non-canonical request rejection.
- Oversized request rejection.
- Ambient-secret environment exclusion and output non-observation.
- Existing full Governance/Desktop suites.

## DELIVERABLES
- `.engineering/work-orders/HCODER-WO-0019.md`
- `.engineering/context-locks/HCODER-WO-0019.json`
- `tools/runtime/status_sidecar.py`
- `tests/runtime/test_runtime_status_sidecar.py`
- reconciled `AGENTS.md`
- evidence/correction/checkpoint artifacts after exact-head proof

## REVIEW FORMAT
HEDS_DELTA exact-head. Provider/model invocation, credential inheritance/read, long-running listener, generic dispatch/RPC, unexpected mutation authority or secret/status leakage is HIGH/CRITICAL.

## STOP CONDITION
Exact-head Governance + Desktop Shell green, HEDS approved with unresolved HIGH/CRITICAL = 0, evidence/checkpoint delta accurate, squash merge with expected-head protection, then push-triggered Governance + Desktop Shell green on `main`. CP-0019 is not canonical before post-merge proof. No desktop launcher/process capability is promoted under WO-0019.
