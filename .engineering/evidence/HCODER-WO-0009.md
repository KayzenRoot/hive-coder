# Evidence Bundle — HCODER-WO-0009

**Risk:** ELEVATED  
**Base:** `21b11482015ff2704a56af7ea71921e74e11c61a`

## Security/runtime invariants
- Checkpoints are workflow state, never permission/approval/permit authority.
- HMAC key is host-owned and never persisted in checkpoint payload.
- Raw prompts, credentials, skill content, model output and exception messages are excluded from checkpoint state.
- Task plans are fingerprint-bound and malformed/tampered/mismatched checkpoints fail closed.
- Model nodes use CP-0008 verified-capability routing.
- Skill nodes execute only through the trusted host skill port.
- Interrupted skills do not auto-replay after crash.
- Per-node attempts and global execution/failure budgets are bounded.
- Cancellation/pause/terminal state prevents further scheduling.

## Deterministic evidence target
DAG order/cycle tests; capability routing failure; retry and budget tests; cancellation/pause; immutable snapshots; invalid/malicious port results; secret-safe checkpoint; crash/restart; interrupted-skill recovery; HMAC tamper and plan mismatch; broad Linux/Windows regression.

## HEDS target
Audit workflow-state authority, crash replay semantics, checkpoint integrity/secret leakage, retry/budget bypasses, external port boundaries and historical canonical-document preservation. UNKNOWN is not PASS.
