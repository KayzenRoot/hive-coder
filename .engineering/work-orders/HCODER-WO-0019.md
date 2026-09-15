# HCODER-WO-0019 — Runtime Status Sidecar Helper

**Status:** APPROVED FOR EXECUTION — STACKED  
**Risk:** ELEVATED  
**Task class:** T3  
**Context radius:** C3  
**Stacked base:** `HCODER-WO-0018`  
**Canonical dependency:** CP-0018 must be canonical before promotion.

## OBJECTIVE
Create the fixed Hive-owned runtime-status sidecar process contract that serves exactly the WO-0018 one-shot status protocol and exits, without provider calls, model execution, credentials, permission/task mutation or desktop authority.

## CONTEXT
WO-0017 defines the bounded status model and WO-0018 freezes the message protocol. The next safe increment is the helper executable/script contract itself, independently of the Tauri desktop launcher.

## SCOPE
- Add a single-purpose sidecar entrypoint accepting exactly `--stdio-status-v1`.
- Read exactly one bounded request from stdin, emit exactly one bounded response to stdout, then exit.
- Use the existing safe runtime status/protocol code.
- Default to truthful DISCONNECTED state until a separately governed live host observer is connected.
- Add process-level tests using Hive's shell-free `ManagedStdioProcess`.

## OUT OF SCOPE
Desktop process spawn, generic process launcher, provider/network/model calls, credentials, prompt/model output, task/permission mutation, filesystem/Git mutation, terminal/Cua/remote control/billing.

## FILES / SOURCES TO READ
- `hive_runtime/process.py`
- `hive_runtime/runtime_status.py`
- `hive_runtime/runtime_status_protocol.py`
- `tests/runtime/test_runtime_bridge.py`

## REQUIREMENTS
1. Exact fixed mode flag; extra/unknown args fail with a stable nonzero exit code.
2. No shell and no dynamic executable/command dispatch is introduced.
3. The helper emits no stderr detail derived from status payloads or secrets.
4. One invocation handles one request only and exits.
5. Ambient provider credentials are neither required nor observed.
6. Malformed/oversized protocol input fails closed without returning a fake snapshot.
7. Default status remains DISCONNECTED, not READY.

## ARCHITECTURE RULES
`future trusted desktop supervisor -> fixed Hive sidecar -> WO-0018 one-shot protocol -> WO-0017 presentation snapshot`. The sidecar transports presentation state only and cannot authorize execution.

## CONSTRAINTS
Python stdlib + existing Hive runtime only. No daemon/listener, no port binding, no generic RPC, no provider SDK/network, no credential environment lookup.

## ACCEPTANCE CRITERIA
Valid process roundtrip returns one disconnected envelope; invalid mode/request exits nonzero; ambient secret fixture does not appear in output; existing Governance/Desktop suites green; HEDS no unresolved HIGH/CRITICAL.

## TESTS
Process roundtrip, exact mode rejection, malformed request rejection, ambient-secret non-observation, existing full suites.

## DELIVERABLES
Sidecar entrypoint, process-level tests, Context Lock and evidence after proof.

## REVIEW FORMAT
HEDS_DELTA exact-head. Provider/model invocation, credential read, long-running listener, generic dispatch or secret/status leakage is HIGH/CRITICAL.

## STOP CONDITION
Exact-head Governance + Desktop Shell green and HEDS approved. Promotion BLOCKED until CP-0018 canonical. No desktop launcher or process capability is promoted under WO-0019.
