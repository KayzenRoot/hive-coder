# HCODER-WO-0018 — Cross-Runtime Status IPC Contract

**Status:** APPROVED FOR EXECUTION — STACKED  
**Risk:** ELEVATED  
**Task class:** T3  
**Context radius:** C4  
**Stacked base:** `HCODER-WO-0017` technical branch  
**Canonical dependency:** CP-0017 must be canonical before promotion.

## OBJECTIVE
Define and prove a versioned, bounded, one-request/one-response runtime-status protocol shared by the Python runtime and desktop TypeScript layer, without launching a runtime process or granting execution authority.

## CONTEXT
WO-0017 introduces `RuntimeStatusSnapshot v1` as non-authoritative presentation state. Before the desktop gains a supervisor/process lifecycle, the message format and parser must be frozen independently so transport authority cannot silently redefine the payload contract.

## SCOPE
- Add `hive-runtime-status-ipc-v1` request/response envelopes.
- Permit exactly one operation: `status.snapshot`.
- Bound request IDs, request bytes, response bytes, provider/model/task strings and collections.
- Reject unknown fields, unknown protocol versions and unknown operations.
- Add a Python one-shot stream handler that performs no provider/model/permission/task mutation.
- Add a strict TypeScript envelope/parser contract using the same limits and truth semantics.
- Add Python and TypeScript adversarial tests.

## OUT OF SCOPE
Runtime subprocess launch, desktop IPC lifecycle, provider calls, model execution, credentials, permit/approval mutation, task mutation, file/Git mutation, terminal, computer-use, remote control, billing/purchases.

## FILES / SOURCES TO READ
- `hive_runtime/runtime_status.py`
- `apps/desktop/src/contracts/desktopSnapshot.ts`
- `apps/desktop/src/lib/desktopBridge.ts`
- `docs/project-brain/13-INTEGRATION-CONTRACTS.md`

## REQUIREMENTS
1. Protocol/version/op/requestId are strictly validated.
2. Unknown keys or oversized messages fail closed.
3. Response snapshots must pass WO-0017 validation before encoding.
4. READY remains evidence-backed presentation only and conveys no authority.
5. No secret-bearing free-form metadata field exists.
6. The protocol handler performs no external call or state mutation.
7. TypeScript rejects malformed, oversized, fake-ready or counter-inconsistent payloads.

## ARCHITECTURE RULES
`RuntimeStatusSnapshot -> status IPC envelope -> strict desktop parser -> presentation only`. Transport data is never an authorization token. The future supervisor may only carry this frozen protocol, not generic RPC.

## CONSTRAINTS
Stdlib Python and existing frontend toolchain only. No WebSocket/server/listener, no generic JSON-RPC method space, no caller-controlled executable/path, no new Tauri permission.

## ACCEPTANCE CRITERIA
Python and TypeScript agree on protocol/schema/state names and bounds; one-shot fixture roundtrip passes; malformed/extra/oversized messages fail; existing Governance/Desktop tests remain green; HEDS has no unresolved HIGH/CRITICAL.

## TESTS
Python protocol parse/encode/one-shot tests; TypeScript contract tests; existing full Governance and Desktop Shell suites.

## DELIVERABLES
Protocol implementation, strict TS parser, tests, Context Lock and evidence after proof.

## REVIEW FORMAT
HEDS_DELTA exact-head. Generic RPC expansion, secret passthrough, fake readiness, unbounded messages or authority-bearing fields are HIGH/CRITICAL.

## STOP CONDITION
Exact-head Governance + Desktop Shell green and HEDS approved. Promotion BLOCKED until CP-0017 is canonical. No process lifecycle or execution authority under WO-0018.
