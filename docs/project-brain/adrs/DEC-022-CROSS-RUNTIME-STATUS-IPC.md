# DEC-022 — Cross-Runtime Status IPC Contract

**Status:** CANDIDATE — APPROVAL PENDING  
**Work Order:** `HCODER-WO-0018`  
**Source checkpoint:** `HCODER-CP-0017`  
**Target checkpoint:** `HCODER-CP-0018`  
**Technical head:** `9df7202835a47f2c18af77bbefa665afa5358b38`

## Decision
Hive Coder freezes `hive-runtime-status-ipc-v1` as a presentation-only cross-runtime status protocol with exactly one operation, `status.snapshot`.

The protocol carries only the canonical `RuntimeStatusSnapshot v1` presentation schema established by CP-0017. It does not create an execution channel, generic RPC namespace, authorization path, provider/model interface or desktop process-lifecycle authority.

## Canonical wire law
- Request IDs are bounded ASCII identifiers matching `[A-Za-z0-9_.:-]{1,64}`.
- Request wire is deterministic canonical JSON and is limited to 512 UTF-8 bytes.
- Snapshot serialization remains limited to 32,768 bytes.
- The complete response envelope is limited to 33,024 bytes.
- Canonical JSON uses sorted object keys, compact separators and ASCII escaping compatible between Python and TypeScript.
- Unknown/extra fields, duplicate/noncanonical JSON wire, malformed UTF-8/JSON, protocol/schema drift and invalid state fail closed.
- The desktop public response-admission API is raw-wire-only through `decodeRuntimeStatusEnvelope(raw)`.

## Semantic law
The desktop decoder independently revalidates the canonical CP-0017 operational states, subsystem provenance identities, collection/string/counter ceilings, provider readiness requirements, provider/model uniqueness, task counter consistency and permission unknown/disconnected counter rules.

Protocol status is presentation truth only. It can never grant a capability, create/consume a permit, approve a request, activate a skill, certify a model capability, mutate a task or Permission & Control Plane state, or authorize filesystem/Git/terminal/computer-use action.

## Server primitive
The Python `serve_one()` primitive receives a prebuilt validated `RuntimeStatusSnapshot`, reads one bounded newline-framed request and writes one response. It accepts no arbitrary callback and owns no runtime/provider/model/credential/task/permission lifecycle.

## Explicitly not approved
- desktop child-process launch, supervision, restart, shutdown or containment;
- sidecar/helper binary identity or authenticity;
- generic JSON-RPC, WebSocket, TCP or HTTP status service;
- provider/network/model execution or credential handling;
- task/permission mutation;
- Tauri capability expansion;
- filesystem/Git/terminal/computer-use mutation;
- remote control, billing/purchases or automatic skill activation.

## Evidence
Technical head `9df7202835a47f2c18af77bbefa665afa5358b38` passed Governance #241 (**283/283 Python**, **56/56 HIGH_ASSURANCE**) and Desktop Shell #77 (**23/23 frontend**, npm audit 0, **11/11 Rust**, locked checks/audits, Windows release build and launch smoke). HEDS review `5215646309` reports unresolved HIGH/CRITICAL findings **0**. `HCODER-WO-0018-CR-001` MEDIUM is resolved.

## Promotion condition
This decision remains CANDIDATE and has no canonical authority until the promotion/final approval heads pass exact-head gates and HEDS, PR #45 is squash-merged, and post-merge validation succeeds. Until then `HCODER-CP-0017` remains the canonical checkpoint.
