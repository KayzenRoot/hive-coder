# Evidence Bundle — HCODER-WO-0007

**Risk:** ELEVATED  
**Base:** `91e0265a215d4edb179d6fcdafbbf3a05409e244`

## Security invariants
- Unknown/unverified model capability fails closed.
- Model name/prose cannot imply capability.
- MCP skill text is untrusted content.
- Skills cannot activate before deterministic evaluation.
- Skills cannot expand an existing permission grant.
- Digest mismatch and duplicate versions fail closed.
- No network/provider credential/desktop mutation surface added.

## Deterministic evidence target
Governance exact-head broad regression plus new intelligence/skills tests. Existing Windows HIGH_ASSURANCE control-plane suite remains unchanged.

## HEDS review target
Audit registry truth source, skill lifecycle state transitions, capability non-escalation, malicious content handling and regression evidence. UNKNOWN is not PASS.
