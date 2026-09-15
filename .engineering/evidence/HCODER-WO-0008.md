# Evidence Bundle — HCODER-WO-0008

**Risk:** ELEVATED  
**Base:** `5af12a77106467bd6838eb545ef2b94ac4265fc5`

## Invariants
- Provider/model names do not grant capability.
- Raw provider observations cannot self-promote to VERIFIED; trusted host verifier owns promotion authority.
- Routing fails closed when no verified model qualifies.
- Credential representation is redacted; no real credential fixture is committed.
- ACP prompt lifecycle does not create desktop permissions or Cua action grants.
- No remote-control, billing, automatic install or new desktop mutation surface is added.

## HEDS corrections
- CR-001 HIGH: removed provider-controlled `verified` flag; trusted host verifier now owns verification.
- CR-002 MEDIUM: restored immutable historical DEC-009/010/011 and appended DEC-012 only.

## Exact-head deterministic evidence
Corrected implementation head `263a920cd1ced4c24955f29ed97e29c0fe3f2d93` passed Governance `34916503775`:
- Ubuntu exact-head broad regression: **105/105 PASS**, ResourceWarning fatal.
- Windows Server 2025 exact-head HIGH_ASSURANCE regression: **56/56 PASS**.
- Foundation lock/doctor and compileall: PASS.

## HEDS verdict
**APPROVED** after CR-001 and CR-002. No unresolved HIGH/CRITICAL findings. Live OpenCode Go authentication/probing is not claimed; remote control and new desktop mutation remain out of scope.
