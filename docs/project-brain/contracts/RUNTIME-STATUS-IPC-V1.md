# Runtime Status IPC Contract v1

**Contract ID:** `hive-runtime-status-ipc-v1`  
**Owner:** Hive Coder  
**Governed by:** `HCODER-WO-0018` / `DEC-022`  
**Status:** CANDIDATE  
**Payload schema:** `hive-runtime-status-v1`

## Purpose
Provide one bounded cross-runtime transport for non-authoritative runtime status presentation. This contract deliberately stops before process lifecycle and execution authority.

## Operation
Exactly one operation exists:

`status.snapshot`

No generic method namespace, extensible command dispatcher or execution request is part of v1.

## Request
Canonical semantic shape:

```json
{"op":"status.snapshot","protocol":"hive-runtime-status-ipc-v1","requestId":"r-1"}
```

Rules:
- exact object keys only: `op`, `protocol`, `requestId`;
- protocol must equal `hive-runtime-status-ipc-v1`;
- operation must equal `status.snapshot`;
- request ID matches `[A-Za-z0-9_.:-]{1,64}`;
- request size <= 512 UTF-8 bytes;
- canonical JSON only: sorted keys, compact separators, ASCII escaping;
- duplicate keys and noncanonical wire fail closed.

## Response
Exact envelope keys:
- `ok` = literal `true`;
- `protocol` = `hive-runtime-status-ipc-v1`;
- `requestId` = validated request ID;
- `snapshot` = canonical `RuntimeStatusSnapshot v1`.

Ceilings:
- snapshot canonical bytes <= 32,768;
- response envelope bytes <= 33,024.

The snapshot must satisfy the canonical CP-0017 contract, including exact provenance:
- runtime: `hive-runtime-status`;
- provider: `hive-provider-catalog`;
- task: `hive-agent-task-runtime`;
- permission: `hive-permission-control-plane`.

Operational states are only `READY`, `UNKNOWN`, `DISCONNECTED`, `DEGRADED`.

## Canonical JSON
Python produces canonical wire using sorted object keys, compact separators and ASCII escaping. The TypeScript contract normalizes to the same ordering/escaping and requires the raw response string to equal its canonical reserialization after semantic validation.

This raw equality is part of admission. Therefore whitespace/order variants, duplicate-key collapse and normalization drift are rejected rather than silently accepted.

## Framing
The Python one-shot server primitive reads exactly one newline-terminated bounded request and writes exactly one newline-terminated response. CRLF request termination is accepted and normalized before parsing.

The server receives a prebuilt validated snapshot. It does not execute a callback or own provider/model/task/permission/process lifecycle.

## Desktop admission
The public response-admission API is:

`decodeRuntimeStatusEnvelope(raw)`

The lower-level semantic object parser is private. A future desktop supervisor must not bypass raw-wire validation.

## Authority statement
This protocol is presentation-only. A valid response is not:
- a Permission & Control Plane authorization;
- a permit or approval;
- VERIFIED model capability evidence;
- a task-control command;
- provider/model execution authority;
- filesystem/Git/terminal/computer-use authority.

## Versioning law
Any new operation, mutable action, generic RPC namespace, error-command channel, process-lifecycle command, expanded envelope field or relaxed bound/schema requires a later governed Work Order and review. Unknown protocol/schema/version/field input fails closed under v1.
