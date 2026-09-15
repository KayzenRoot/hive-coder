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

## HEDS correction
CR-001 HIGH found caller-controlled evaluation/grant inputs in the first candidate. Corrected by moving evaluator and capability-authorizer authority to trusted host construction. Skill-facing activation can no longer submit a PASS or grant. Evaluation evidence binds exact skill identity/version/content digest.

## Exact-head deterministic evidence
Corrected head `a902c71a9669848493862eaceee45960b35766c0`:
- Governance run `34915868010`: SUCCESS.
- Ubuntu exact-head broad regression: **94/94 PASS** with ResourceWarning fatal.
- Windows Server 2025 exact-head HIGH_ASSURANCE regression: **56/56 PASS**.
- Foundation lock/doctor and compileall: PASS.

## HEDS verdict
**APPROVED** after CR-001. No unresolved HIGH/CRITICAL findings. Provider execution, automatic skill installation, remote control and new desktop mutation remain out of scope.
