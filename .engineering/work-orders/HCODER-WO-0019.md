# HCODER-WO-0019 — Runtime Status Sidecar Helper

**Status:** FINAL APPROVAL CANDIDATE / FINAL GATES PENDING — NOT CANONICAL  
**Risk:** ELEVATED  
**Task class:** T3  
**Context radius:** C3  
**Canonical base:** `HCODER-CP-0018` on `main` at `c0a44d43546b9f176125b9e7099b8422d6b62ba3`  
**Issue:** `#47`  
**PR:** `#48` — DRAFT  
**Technical exact head:** `ba10ba72f76316806cd820dc0d205e68105f61bb`  
**HEDS technical:** `5216093993` — APPROVED FOR PROMOTION, H/C 0  
**Promotion exact head:** `55975e7e97eb33d2b695d02e36ab6994fa7ae7b5`  
**HEDS promotion:** `5216180277` — APPROVED FOR FINAL APPROVAL MUTATION, H/C 0  
**Historical evidence only:** PR `#38` / branch `feat/HCODER-WO-0019-runtime-status-sidecar` MUST NOT be merged or cherry-picked.

## OBJECTIVE
Create the fixed Hive-owned runtime-status sidecar process contract that serves exactly one canonical CP-0018 status request over stdio, emits exactly one canonical response, and exits without provider calls, model execution, credentials, permission/task mutation or desktop authority.

## CONTEXT
CP-0017 canonicalized the bounded non-authoritative runtime status model. CP-0018 canonicalized the strict `hive-runtime-status-ipc-v1` one-shot wire protocol with sole `status.snapshot` operation. WO-0019 adds only the helper process boundary, independently of any Tauri/desktop process launcher.

Historical PR #38 predates final CP-0018 hardening and remains supporting evidence only. The canonical reconstruction uses a prebuilt `disconnected_snapshot()` for `serve_one(...)` and canonical `encode_request(...)`/`parse_response(...)` process wire.

## SCOPE
- Single-purpose sidecar entrypoint accepting exactly `--stdio-status-v1`.
- Exactly one bounded canonical stdin request.
- Exactly one bounded canonical stdout response.
- Exit after one request.
- Reuse canonical runtime status/protocol implementation.
- Truthful default `DISCONNECTED` state via prebuilt `disconnected_snapshot()`.
- Process-level tests through shell-free `ManagedStdioProcess`.
- Cross-platform HIGH_ASSURANCE process proof.
- Governed evidence/checkpoint/ADR promotion.

## OUT OF SCOPE
Desktop/Tauri process spawn, generic process launcher, daemon/service lifecycle, sockets, HTTP/WebSocket/listeners, provider/network/model calls, credentials, prompt/model output, task/permission mutation, filesystem/Git mutation, terminal/Cua/remote-control/billing/purchase authority, installer/signing/release packaging.

## REQUIREMENTS
1. Exact mode flag only; missing/unknown/extra args return usage exit `64`, no protocol output.
2. Construct `disconnected_snapshot()` before protocol service and pass the object to `serve_one(...)`.
3. One request, one response, exit `0`.
4. Malformed, duplicate-key, noncanonical, unsupported/future, missing-newline or oversized input fails closed with protocol exit `65` and no fake snapshot.
5. No shell, generic dispatch, dynamic executable selection, listener, socket or generic RPC namespace.
6. Expected invalid input emits no payload/status/secret detail to stderr.
7. Process tests use canonical `ManagedStdioProcess`, preserving `shell=False` and its allowlisted child environment.
8. Ambient provider/API credentials are neither required nor inherited; representative secret exclusion is proven.
9. Valid tests use canonical `encode_request(...)`; response wire passes canonical `parse_response(...)`.
10. Default status remains `DISCONNECTED` and cannot authorize execution or mint/consume CP permits.

## ARCHITECTURE RULE
`future trusted desktop supervisor -> fixed Hive sidecar -> CP-0018 one-shot protocol -> CP-0017 presentation snapshot`.

The sidecar transports presentation state only. It is not an authority boundary and does not launch providers/models or create execution authority.

## ACCEPTANCE / PROOF
Technical exact head `ba10ba72f76316806cd820dc0d205e68105f61bb`:
- Governance #250: **288/288 Ubuntu PASS**, **61/61 Windows HIGH_ASSURANCE PASS** including sidecar; ResourceWarning fatal.
- Desktop Shell #86: SUCCESS, security gate, **23/23 frontend**, npm audit 0, locked Rust audit/tests/check, Windows release build/smoke.
- HEDS technical `5216093993`: APPROVED FOR PROMOTION, H/C 0.

Promotion exact head `55975e7e97eb33d2b695d02e36ab6994fa7ae7b5`:
- Governance #251: **288/288 Ubuntu PASS**, **61/61 Windows HIGH_ASSURANCE PASS**.
- Desktop Shell #87: SUCCESS including Windows release build/smoke.
- HEDS promotion `5216180277`: APPROVED FOR FINAL APPROVAL MUTATION, H/C 0.

## CORRECTIONS
- `HCODER-WO-0019-CR-001` LOW — RESOLVED: process-level one-shot/adversarial coverage.
- `HCODER-WO-0019-CR-002` LOW — RESOLVED: Windows HIGH_ASSURANCE sidecar proof.

Neither correction changed CP-0018 protocol semantics or expanded authority.

## DELIVERABLES
Work Order, Context Lock, fixed sidecar, process-level tests, resolved Correction Deltas, Evidence Bundle, Checkpoint Delta, DEC-023 candidate, Project Brain promotion reconciliation and continuation handoff.

## REVIEW FORMAT
HEDS_DELTA exact-head. Provider/model invocation, credential inheritance/read, long-running listener, generic dispatch/RPC, unexpected mutation authority or secret/status leakage is HIGH/CRITICAL.

## STOP CONDITION
Final exact-head Governance + Desktop Shell green, final HEDS with unresolved HIGH/CRITICAL 0, PR #48 ready only after those proofs, squash merge with expected-head protection, then push-triggered Governance + Desktop Shell green on `main`. CP-0019 is not canonical before post-merge proof and documentation-only canonical closeout. No desktop launcher/process capability is promoted under WO-0019.
