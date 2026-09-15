# HCODER-WO-0017-CR-001 — Complete strict status-contract validation semantics

**Status:** RESOLVED IN CANDIDATE  
**Severity:** MEDIUM  
**Detected by:** HEDS semantic pre-review of canonical replay PR #42  
**Affected implementation head:** `3053d6ee83483a41a5809f9fa52be40f2e28a04b`  
**Correction implementation head:** `0b41f6a5b8c97867dbd4f5306c0a0a90e67413b3`

## Finding
The replayed WO-0017 candidate passed all mechanical CI gates but did not fully satisfy its own frozen semantic contract in related validation areas:

1. only the runtime signal carried explicit provenance; provider/task/permission presentation records did not;
2. the Work Order required an encoder/decoder validation boundary, but only validated encoding existed;
3. Python `bool` values were accepted by `isinstance(value, int)` counter checks, allowing boolean JSON values to masquerade as numeric counters;
4. runtime type hints alone did not prevent callers from constructing string states such as `"READY"` instead of the governed `StatusState` enum;
5. provenance was initially only bounded text, which would permit caller-defined labels to masquerade as trusted subsystem provenance.

The missing strict decoder also meant unknown/duplicate object fields were not independently proven to fail closed before WO-0018 freezes the cross-runtime IPC parser.

## Resolution
- provider, task and permission presentation records now carry explicit provenance;
- provenance is canonical per subsystem (`hive-runtime-status`, provider catalog, task runtime, permission control plane) rather than caller-defined free text;
- in-memory status objects require the typed `StatusState` enum before serialization;
- `RuntimeStatusSnapshot.from_json()` implements a strict bounded UTF-8/JSON decoder with exact object shapes, duplicate-key rejection and the same semantic validation as encoding;
- numeric counters reject booleans and enforce deterministic upper bounds;
- unobserved permission state remains `UNKNOWN`/`DISCONNECTED`; no private Permission & Control Plane internals are serialized;
- fixed `DEGRADED` encode/decode fail-closed helpers convert rejected observation data into non-secret presentation state without reflecting exception details;
- adversarial tests cover provenance, canonical provenance rejection, typed states, strict round-trip parsing, unknown/duplicate fields, fake READY providers, boolean counters and DEGRADED fallback.

## Authority impact
None. The correction narrows and validates the presentation boundary only. It adds no provider call, model execution, credential access, permission/task mutation, process execution, filesystem/Git mutation or computer-use authority.

## Closure gate
This correction is not independently approved by this record. The final PR head containing this record must pass exact-head Governance + Desktop Shell and HEDS with unresolved HIGH/CRITICAL findings = 0 before WO-0017 may advance.
