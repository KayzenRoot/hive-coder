# Hive Permission & Control Plane

`PermissionControlPlane` is the trusted authorization state machine that must sit between Hive orchestration and any future privileged adapter executor.

## Invariants
- default deny;
- explicit deny beats allow;
- unknown capability, session, target or authorization state denies;
- model/task text is untrusted context and cannot grant permissions;
- high-risk mutation and critical capabilities have mandatory approval floors;
- approvals and execution permits are HMAC-SHA256 signed, short-lived and single-use;
- signed claims bind session, request fingerprint, policy epoch, global emergency epoch and expiry;
- request fingerprints bind capability, action, target and canonical executor arguments;
- target allowlists cover application, window, workspace root and resource;
- emergency stop, user takeover, cancellation and policy updates invalidate outstanding challenges/tokens/permits;
- cancellation callbacks are invoked after state invalidation, and callback exceptions are contained/audited;
- audit details are redacted and hash chained.

## Two-stage authorization
1. Policy evaluation returns `DENY`, `ALLOW` or `REQUIRE_APPROVAL`.
2. For approval-required requests, trusted UI/orchestrator code creates and resolves a request-bound challenge. Untrusted model/tool surfaces must never receive the approval method.
3. `authorize()` consumes the approval when required and issues a very short-lived execution permit.
4. A future executor must call `consume_execution_permit()` against the exact same request immediately before the action.

This Work Order intentionally contains no executor and no Cua `tools/call`. The future executor integration must revalidate live target identity immediately before mutation to address TOCTOU/window-switch risk.
