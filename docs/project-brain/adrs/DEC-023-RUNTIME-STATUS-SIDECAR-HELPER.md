# DEC-023 — Runtime Status Sidecar Helper Boundary

**Status:** APPROVED / CANONICAL — CLOSEOUT SEAL PENDING  
**Work Order:** `HCODER-WO-0019`  
**Source checkpoint:** `HCODER-CP-0018`  
**Target checkpoint:** `HCODER-CP-0019`  
**Technical head:** `ba10ba72f76316806cd820dc0d205e68105f61bb`  
**HEDS technical:** `5216093993`  
**Promotion head:** `55975e7e97eb33d2b695d02e36ab6994fa7ae7b5`  
**HEDS promotion:** `5216180277`  
**Final reviewed product head:** `abe7b29cf59d3fd2e464e3ea69a7e585ba75e6dd`  
**HEDS final product:** `5216313496`  
**Product merge SHA:** `2ed4222556916cf524e31f65c4c417d27b7e6fd9`

## Decision
Hive Coder canonicalizes a fixed, single-purpose Python runtime-status sidecar helper that exposes only the already-canonical CP-0018 `hive-runtime-status-ipc-v1` one-shot presentation protocol over stdio.

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

This decision does not approve a desktop launcher/supervisor. It proves only the helper contract itself through the existing test process boundary.

## Fail-closed law
At the executable boundary, tests prove rejection of missing/unknown/extra mode, malformed JSON, noncanonical encoding, duplicate keys, future protocol, unsupported operation, oversized input and missing newline. A buffered second canonical request is left unserved because the helper exits after the first accepted request.

## Authority law
A valid sidecar response is presentation data only. It cannot grant Permission & Control Plane authority; launch providers/models; access credentials; mutate task/permission/filesystem/Git state; execute terminal/computer-use action; expose remote control; activate skills; or authorize billing/purchases.

## Explicitly not approved
- Tauri/desktop child-process spawn or generic process capability;
- helper packaging, signing, binary authenticity or update provenance;
- long-running daemon/listener/socket/HTTP/WebSocket/generic RPC;
- automatic restart, shutdown, health management or containment policy;
- live trusted runtime/provider/task/permission observation;
- provider reachability/authentication or VERIFIED model-capability claims;
- any new mutation authority.

## Evidence
Technical exact head `ba10ba72f76316806cd820dc0d205e68105f61bb` passed Governance #250 (**288/288 Ubuntu**, **61/61 Windows HIGH_ASSURANCE**) and Desktop Shell #86; HEDS `5216093993` approved promotion with H/C 0.

Promotion exact head `55975e7e97eb33d2b695d02e36ab6994fa7ae7b5` passed Governance #251 (**288/288 Ubuntu**, **61/61 Windows HIGH_ASSURANCE**) and Desktop Shell #87; HEDS `5216180277` approved the final approval mutation with H/C 0.

Final product head `abe7b29cf59d3fd2e464e3ea69a7e585ba75e6dd` passed Governance #252 and Desktop Shell #88; HEDS final review `5216313496` approved squash merge with H/C 0.

Product PR #48 was squash-merged using expected-head protection as GitHub-signed SHA `2ed4222556916cf524e31f65c4c417d27b7e6fd9`. That exact merge SHA passed push Governance #253 (**288/288 Ubuntu**, **61/61 Windows HIGH_ASSURANCE**) and Desktop Shell #89 including Windows release build and launch smoke.

`HCODER-WO-0019-CR-001` and `HCODER-WO-0019-CR-002` are resolved.

## Canonicalization result
`DEC-023` is **APPROVED / CANONICAL** as the decision recorded by CP-0019, subject only to this documentation-only closeout receiving its own exact-head Governance + Desktop Shell + HEDS, squash merge and push validation seal.

The decision canonicalizes no desktop supervisor, generic process dispatch or mutation authority. The next separately governed increment is the fresh CP-0019-based reconstruction of WO-0020.
