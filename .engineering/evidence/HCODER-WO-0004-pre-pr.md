# Evidence Bundle — HCODER-WO-0004 (candidate)

## Identity
- Base: `f05154b3494c9ed67c93a0ae6374a49713d343c3`
- Branch: `feat/HCODER-WO-0004-control-plane`
- Issue: #8
- PR: #9
- Risk: HIGH_ASSURANCE

## First-candidate proof
Candidate `9c83d498a6284f7869d918ac2926858c0926525f` passed Governance run `34911907919`.
- Ubuntu exact-head: `EXACT_HEAD_OK=9c83d498a6284f7869d918ac2926858c0926525f`; broad suite 55/55 PASS with ResourceWarning fatal.
- Windows Server 2025 exact-head: same SHA; targeted control-plane suite 29/29 PASS with ResourceWarning fatal.

## HEDS corrections after first green candidate
- CR-001 HIGH: wall-clock security expiry -> monotonic security clock + stronger token validation/key floor.
- CR-002 HIGH: mutable approval/request representation -> canonical one-operation snapshots + copy-on-read challenge views.
- CR-003 MEDIUM: public appendable audit surface + narrow inline redaction -> private audit surface + broader redaction.
- CR-004 HIGH: callbacks under critical lock -> post-invalidation asynchronous callback dispatch.

## Safety evidence
- No Cua adapter action method is added or changed.
- No Open Interpreter prompt method is added.
- The control plane performs no OS action itself.
- Free-form `untrusted_context` is excluded from authorization semantics and reduced to a safe hash for audit.

## Pending
The corrected head must pass fresh exact-head Ubuntu broad regression, Windows targeted tests and final HEDS before canonical promotion.
