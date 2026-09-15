# Evidence Bundle — HCODER-WO-0004 (pre-PR candidate)

## Identity
- Base: `f05154b3494c9ed67c93a0ae6374a49713d343c3`
- Branch: `feat/HCODER-WO-0004-control-plane`
- Issue: #8
- Risk: HIGH_ASSURANCE

## Local deterministic evidence
- `PYTHONNOUSERSITE=1 python3 -m unittest discover -s tests -p 'test_*.py'`: PASS for the isolated control-plane candidate, 28/28 tests.
- Local tests cover default deny, explicit deny precedence, wrong application/window/workspace/resource, unknown capability, prompt-injection-shaped context, invalid request shape, approval/permit tamper and replay, target/argument binding, expiry, policy epoch invalidation, emergency stop, user takeover, callback failure containment, redaction and audit-chain verification.
- GitHub broad regression + Windows platform proof are still mandatory and will supersede this local pre-PR evidence.

## Safety evidence
- No Cua adapter action method is added or changed by the candidate.
- No Open Interpreter prompt method is added.
- The control plane produces only signed execution permits; it performs no OS action itself.
- Free-form `untrusted_context` is excluded from the authorization fingerprint/decision surface and is represented in audit only by SHA-256.
- Approval display arguments are recursively redacted; the cryptographic request fingerprint remains bound to the actual canonical arguments.

## Pending
Exact-head PR Governance, Windows targeted suite, HEDS adversarial audit, any same-WO correction deltas, and final canonical promotion.
