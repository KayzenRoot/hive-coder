# Evidence Bundle — HCODER-WO-0008

**Risk:** ELEVATED  
**Base:** `5af12a77106467bd6838eb545ef2b94ac4265fc5`

## Invariants
- Provider/model names do not grant capability.
- Only CP-0007 verified evidence satisfies required model capabilities.
- Routing fails closed when no verified model qualifies.
- Credential representation is redacted; no real credential fixture is committed.
- ACP prompt lifecycle does not create desktop permissions or Cua action grants.
- No remote-control, billing, automatic install or new desktop mutation surface is added.

## Deterministic evidence target
Provider catalog/probe/router/credential tests, ACP prompt lifecycle tests and broad Linux/Windows Governance regression.

## HEDS target
Audit secret handling, capability truth source, routing downgrade behavior, ACP prompt request/response validation and regression evidence. UNKNOWN is not PASS.
