# Correction Delta — HCODER-WO-0005-CR-001

## Findings
1. **HIGH · argument surface too broad:** first candidate forwarded arbitrary argument maps for allowlisted tool names. A safe tool name alone is insufficient if optional arguments can alter semantics.
2. **HIGH · emergency stop did not interrupt blocking RPC:** cancellation set an event but `JsonRpcPeer.request()` could remain blocked until timeout and the OS action could continue.
3. **MEDIUM · Windows gate initially omitted executor tests.**
4. **MEDIUM · initial test fixture used a stale `ControlPolicy` constructor and failed broad regression.

## Corrections
- Add exact per-action argument schemas and bounds. `pointer.click` accepts only numeric `x/y`; `keyboard.type_text` accepts only bounded non-NUL `text`.
- Cancellation closes the Cua peer, waking the blocking JSON-RPC request and preventing subsequent dispatch. The Cua session is intentionally sacrificed on takeover/emergency stop.
- Windows HIGH_ASSURANCE gate now includes gated executor tests.
- Tests use canonical `ControlPolicy.build`/`CapabilityRule.build`.
- Add blocking-peer emergency-stop test, extra-argument rejection and oversized-text rejection.

## Residual boundary
This proves cancellation propagation at the Hive RPC boundary. It does **not** prove that every physical OS input already accepted by Cua can be rolled back. Physical Windows+Cua E2E remains a separate proof requirement before claiming full desktop cancellation semantics.
