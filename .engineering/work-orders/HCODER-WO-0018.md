# HCODER-WO-0018 — Cross-Runtime Status IPC Contract

**Status:** APPROVED FOR PROMOTION CANDIDATE  
**Risk:** ELEVATED  
**Task class:** T3  
**Context radius:** C4  
**Canonical base:** `HCODER-CP-0017` on `main` at `79e6eb60288c8e0adcb26bdcffdfe0ae21ef8db7`  
**Issue:** `#44`  
**PR:** `#45`  
**Technical reviewed head:** `9df7202835a47f2c18af77bbefa665afa5358b38`  
**HEDS technical review:** `5215646309`

## OBJECTIVE
Define and prove a versioned, bounded, one-request/one-response runtime-status protocol shared by the canonical Python runtime-status contract and desktop TypeScript presentation layer, without launching a runtime process or granting execution authority.

## CONTEXT
`HCODER-CP-0017` is canonical and establishes strict `RuntimeStatusSnapshot v1` presentation truth, canonical subsystem provenance, bounded counters/collections/strings, duplicate-key rejection, fail-closed states and a 32,768-byte snapshot ceiling. Historical PR #37 explored this IPC boundary before CP-0017 canonicalization but targets a pre-correction snapshot shape and divergent ancestry. It is supporting evidence only and must not be merged or replayed blindly.

WO-0018 freezes the protocol before any desktop process lifecycle exists, so a later supervisor cannot silently expand the transport into generic RPC or redefine status truth.

## SCOPE
- Add exact protocol `hive-runtime-status-ipc-v1`.
- Permit exactly one operation: `status.snapshot`.
- Add deterministic canonical JSON request/response wire encoding with sorted keys, compact separators and ASCII escaping.
- Bound request IDs, request bytes, snapshot bytes and response-envelope bytes.
- Reject unknown fields, protocol/schema drift, unknown operations, duplicate-key/non-canonical wire encodings and malformed UTF-8/JSON.
- Add strict Python request and response validation over canonical `RuntimeStatusSnapshot v1`.
- Add a pure one-shot stream handler that receives a prebuilt validated snapshot and performs no callback/provider/model/process/task/permission mutation.
- Add strict TypeScript request encoder plus raw response decoder/parser with the same protocol/schema/provenance/state/count/string/byte invariants.
- Add Python and TypeScript adversarial tests.

## OUT OF SCOPE
- Runtime subprocess launch, supervision, restart or shutdown lifecycle.
- Desktop Tauri IPC/process bridge changes.
- Provider/network calls or credential loading.
- Model execution or raw prompt/model-output transport.
- Generic RPC/JSON-RPC method space.
- Task pause/resume/cancel mutation.
- Permission approval/permit creation or private control-plane serialization.
- File/Git mutation, terminal execution or computer-use mutation.
- Remote control, billing/purchases or automatic skill activation.

## FILES / SOURCES TO READ
- `hive_runtime/runtime_status.py`
- `tests/runtime/test_runtime_status.py`
- `tests/runtime/test_runtime_status_hardening.py`
- `apps/desktop/src/contracts/desktopSnapshot.ts`
- `docs/project-brain/04-ARCHITECTURE.md`
- `docs/project-brain/05-SECURITY.md`
- `docs/project-brain/08-BACKLOG.md`
- `docs/project-brain/13-INTEGRATION-CONTRACTS.md`
- historical PR `#37` only as non-authoritative supporting evidence.

## REQUIREMENTS
1. Protocol, operation and request ID are strictly validated; only `status.snapshot` exists.
2. Request wire format is deterministic canonical JSON and bounded to 512 UTF-8 bytes.
3. Response wire format is deterministic canonical JSON. The canonical snapshot retains its 32,768-byte ceiling; response envelope total is bounded to `MAX_STATUS_BYTES + 256` bytes.
4. TypeScript validates the raw wire before presentation and re-enforces exact canonical runtime/provider/task/permission provenance.
5. Provider `READY` requires concrete observed models and still conveys no network/authentication or VERIFIED capability authority.
6. UNKNOWN/DISCONNECTED permission state cannot carry authoritative-looking counters.
7. Task counters remain internally consistent and bounded.
8. Unknown keys, duplicate/non-canonical JSON encodings, protocol/schema drift and malformed state fail closed.
9. No secret-bearing/free-form metadata field exists in the envelope.
10. The protocol handler performs no external call and accepts a prebuilt snapshot rather than an arbitrary observation callback.
11. CP-0005 through CP-0017 authority boundaries remain unchanged.

## ARCHITECTURE RULES
`RuntimeStatusSnapshot v1 -> canonical status IPC envelope -> strict raw desktop decoder -> presentation only`.

Transport data is never an authorization token, capability grant, model-capability verifier, permission decision or task command. A future supervisor may carry only this frozen status protocol unless a later governed Work Order explicitly approves another protocol. No generic dispatch namespace is introduced here.

## CONSTRAINTS
- Python stdlib and existing frontend toolchain only.
- No new dependency or Tauri permission.
- No WebSocket, TCP listener, HTTP server or generic JSON-RPC surface.
- No caller-controlled executable/path/command.
- No reflection over private authorization internals.
- Preserve existing runtime and desktop APIs/tests.

## ACCEPTANCE CRITERIA
- Python and TypeScript agree on protocol/schema/state/provenance names and all relevant ceilings.
- Canonical request and response round trips pass.
- Duplicate keys, non-canonical wire, unknown/extra fields, oversized messages, bad IDs, protocol/schema drift, fake READY providers, bad provenance and inconsistent counters fail closed.
- One-shot Python handler emits exactly one bounded response line from a prebuilt snapshot and performs no lifecycle/mutation action.
- Existing Governance and Desktop Shell suites remain green on the exact candidate head.
- HEDS finds no unresolved HIGH/CRITICAL issue.

## TESTS
- Python canonical request encode/parse and strict duplicate/shape/version/op/id/size rejection.
- Python canonical response encode/parse and `RuntimeStatusSnapshot v1` revalidation.
- Python one-shot framing including newline/CRLF/oversize behavior and exactly one response.
- TypeScript canonical request encoder.
- TypeScript raw response byte/canonical-wire validation.
- TypeScript exact runtime/provider/task/permission provenance validation.
- TypeScript fake readiness, duplicate provider/model, count consistency, permission-counter and schema/protocol drift adversarial cases.
- Full Governance regression.
- Full Desktop Shell regression.

## DELIVERABLES
- `hive_runtime/runtime_status_protocol.py`;
- `tests/runtime/test_runtime_status_protocol.py`;
- `apps/desktop/src/contracts/runtimeStatus.ts`;
- `apps/desktop/src/contracts/runtimeStatus.test.ts`;
- Context Lock;
- `HCODER-WO-0018-CR-001` correction record;
- evidence/checkpoint/ADR/contract promotion artifacts after objective proof.

## REVIEW FORMAT
HEDS_DELTA exact-head. Treat generic RPC expansion, secret passthrough, protocol ambiguity, fake readiness, provenance weakening, unbounded messages or authority-bearing fields as HIGH/CRITICAL.

## TECHNICAL PROOF
Exact technical head `9df7202835a47f2c18af77bbefa665afa5358b38` passed Governance #241 (**283/283 Python**, **56/56 Windows HIGH_ASSURANCE**) and Desktop Shell #77 (security gate PASS, **23/23 frontend**, npm audit 0, **11/11 Rust**, locked checks/audits, Windows release build and launch smoke). HEDS technical review `5215646309` reports unresolved HIGH/CRITICAL = 0. `HCODER-WO-0018-CR-001` MEDIUM is resolved.

## STOP CONDITION
Exact-head Governance + Desktop Shell green; adversarial protocol tests green; HEDS APPROVED with unresolved HIGH/CRITICAL = 0. No runtime process lifecycle or execution/mutation authority may be promoted under WO-0018. Squash merge only after all final gates pass; post-merge validation required before `HCODER-CP-0018` becomes canonical.
