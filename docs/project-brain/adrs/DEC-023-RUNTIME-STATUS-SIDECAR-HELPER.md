# DEC-023 — Runtime Status Sidecar Helper Boundary

**Status:** PROMOTION CANDIDATE / NOT CANONICAL  
**Work Order:** `HCODER-WO-0019`  
**Source checkpoint:** `HCODER-CP-0018`  
**Target checkpoint:** `HCODER-CP-0019`  
**Technical head:** `ba10ba72f76316806cd820dc0d205e68105f61bb`  
**HEDS technical review:** `5216093993`

## Decision
Hive Coder introduces a fixed, single-purpose Python runtime-status sidecar helper that exposes only the already-canonical CP-0018 `hive-runtime-status-ipc-v1` one-shot presentation protocol over stdio.

The helper is not a daemon, runtime host, generic process bridge, provider/model execution channel or authorization boundary. Its sole admitted mode is `--stdio-status-v1`.

## Process law
- Argument vector must be exactly `["--stdio-status-v1"]`; invalid/missing/extra mode returns exit `64` without protocol output.
- The helper constructs a validated `disconnected_snapshot()` before protocol service and passes the snapshot object to canonical CP-0018 `serve_one(...)`.
- Exactly one bounded canonical request is consumed, exactly one bounded canonical response may be emitted, and the process then exits.
- Invalid protocol input returns exit `65` without a fake snapshot or payload-derived stderr detail.
- Accepted request/response semantics and byte ceilings remain owned by CP-0018 and are not widened by this decision.
- The default snapshot is truthful `DISCONNECTED`; the sidecar does not infer or fabricate live runtime/provider readiness.

## Child-process law
Process-level proof uses Hive's canonical `ManagedStdioProcess`, which launches argument arrays with `shell=False` and a least-privilege allowlisted child environment. The WO-0019 sidecar `ProcessSpec` supplies no environment overrides. Representative ambient provider credential material is proven absent from the child environment and emitted response.

This decision does not yet approve a desktop launcher/supervisor. It only proves the helper contract itself can be launched safely by the existing test process boundary.

## Fail-closed law
At the executable boundary, tests prove rejection of:
- missing, unknown and extra mode arguments;
- malformed JSON;
- noncanonical JSON encoding;
- duplicate object keys;
- unsupported/future protocol identity;
- unsupported operation;
- oversized request input;
- missing newline framing.

A buffered second canonical request is left unserved because the helper exits after the first accepted request.

## Authority law
A valid sidecar response is presentation data only. It cannot:
- create, grant, approve, mint or consume Permission & Control Plane authority;
- launch providers/models or access credentials;
- mutate task/permission state;
- execute shell/terminal commands;
- mutate filesystem or Git state;
- inject desktop input or create computer-use authority;
- expose remote control;
- activate skills automatically;
- authorize billing or purchases.

## Explicitly not approved
- Tauri/desktop child-process spawn or generic process capability;
- helper packaging, signing, binary authenticity or update provenance;
- long-running helper daemon, listener, socket, HTTP/WebSocket or generic RPC service;
- automatic restart, shutdown, health-management or containment policy;
- live trusted runtime/provider/task/permission observation;
- provider reachability/authentication or VERIFIED model-capability claims;
- any new mutation authority.

## Evidence
Technical exact head `ba10ba72f76316806cd820dc0d205e68105f61bb` passed:
- Governance #250 (`35027148143`): Ubuntu source-pack **288/288 PASS** and Windows Server 2025 HIGH_ASSURANCE **61/61 PASS**, with the sidecar process suite included on Windows and `ResourceWarning` fatal.
- Desktop Shell #86 (`35027148075`): desktop security gate PASS, frontend **23/23 PASS**, npm audit 0 vulnerabilities, locked Rust audits/tests/check PASS, Tauri Windows release build PASS and launch smoke PASS.
- HEDS technical review `5216093993`: **APPROVED FOR PROMOTION**, unresolved HIGH/CRITICAL **0**.

`HCODER-WO-0019-CR-001` and `HCODER-WO-0019-CR-002` are resolved.

## Promotion rule
DEC-023 is a **promotion candidate only**. It becomes APPROVED / CANONICAL only after the promotion/final exact-head gates and HEDS pass, PR #48 is squash-merged with expected-head protection, and the resulting `main` product merge SHA passes push-triggered Governance + Desktop Shell validation. A separate closeout may then record the canonical seal.
