# Evidence Bundle — HCODER-WO-0004

## Identity
- Base: `f05154b3494c9ed67c93a0ae6374a49713d343c3`
- Branch: `feat/HCODER-WO-0004-control-plane`
- Issue: #8
- PR: #9
- Risk: HIGH_ASSURANCE

## First-candidate proof
Candidate `9c83d498a6284f7869d918ac2926858c0926525f` passed Governance run `34911907919`.
- Ubuntu exact-head broad suite: 55/55 PASS.
- Windows Server 2025 exact-head targeted suite: 29/29 PASS.

## HEDS correction cycle
- CR-001 HIGH: wall-clock security expiry -> monotonic security clock, strict/bounded token decode, record cross-check, 256-bit HMAC key floor.
- CR-002 HIGH: mutable approval/request representation -> canonical per-operation request snapshot + canonical JSON/copy-on-read challenge presentation.
- CR-003 MEDIUM: public appendable audit surface + narrow redaction -> private audit surface + broader secret redaction.
- CR-004 HIGH: callbacks under critical lock -> synchronous invalidation followed by isolated asynchronous cancellation callbacks.

## Corrected implementation proof
Corrected head `470ab2e25c4b838d8b6d59cd38f0b43186606063` passed Governance run `34912342323`.
- Ubuntu `EXACT_HEAD_OK=470ab2e25c4b838d8b6d59cd38f0b43186606063`; broad suite **62/62 PASS** with `ResourceWarning` fatal.
- Windows Server 2025 `EXACT_HEAD_OK=470ab2e25c4b838d8b6d59cd38f0b43186606063`; targeted control-plane suite **36/36 PASS** with `ResourceWarning` fatal.
- Surface regression proves `CuaAdapter` still exposes no `call_tool`.

## HEDS
Technical verdict: **APPROVED** on corrected implementation head `470ab2e25c4b838d8b6d59cd38f0b43186606063`; review record `5204200607`. GitHub rejected account-level `APPROVE` because the connected account is also the PR author, so the verdict is intentionally recorded as a review comment rather than falsely represented.

No unresolved CRITICAL/HIGH finding remains inside WO-0004 scope.

## Residual boundary
The control plane performs no OS action. Stopping a real action already in flight, live target revalidation, and Cua `tools/call` execution are not proven here and remain mandatory evidence for a later HIGH_ASSURANCE executor integration.

## Final gate
`DEC-007` and `HCODER-CP-0004` are promoted in the final candidate. A fresh exact-head Ubuntu + Windows Governance run on that promotion SHA is mandatory before merge.
