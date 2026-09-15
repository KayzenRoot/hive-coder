# Proposed Checkpoint Delta — HCODER-WO-0004

**Status:** PROPOSED · not canonical until HEDS approval.

If approved, promote only these truths:
- A Hive-owned Permission & Control Plane exists as a pure authorization boundary with no desktop executor.
- Capability/action/target policy is default-deny and explicit deny wins.
- High-risk mutation and critical capability classes require approval even if a policy attempts to disable it.
- Control sessions are bounded and carry a monotonically changing policy epoch.
- Approval grants and execution permits are HMAC-signed, request-bound, session-bound, policy/global-epoch-bound, expiring and single-use.
- Emergency stop, user takeover, cancellation and policy changes invalidate ephemeral authorization.
- Action request fingerprints bind executor-relevant arguments and targets while untrusted model/task context does not influence authorization.
- Audit events are redacted, hash chained and exposed without mutable stored detail objects.
- Ubuntu broad regression and Windows targeted control-plane validation are required evidence.

Do not promote any claim that Cua `tools/call`, real desktop actions, OS-global emergency hotkey, durable audit storage, UI or production deployment is proven.
