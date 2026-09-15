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
- Per-node attempts and authenticated global execution/failure budgets are bounded.
- Budget broadening requires an explicit monotonic trusted-host transition while paused.
- Cancellation/pause/terminal state prevents unintended future scheduling.

## HEDS corrections
- **CR-001 HIGH:** initial global budgets were constructor-only and could be silently broadened at restart. Fixed by persisting ceilings inside the HMAC-authenticated checkpoint, requiring exact resume match, and adding explicit audited `extend_budget()`.
- **CR-002 MEDIUM:** an in-flight `pause()` could be overwritten when a call settled. Fixed so successful/retryable settlement preserves PAUSED; terminal failure may still win and cancellation remains terminal.

## Exact-head deterministic evidence
Corrected implementation head `82266bf8087f526767878801259c47c644ffaa33` passed Governance run `34917858327`:
- Ubuntu exact-head broad regression: **128/128 PASS**, ResourceWarning fatal.
- Windows Server 2025 exact-head HIGH_ASSURANCE regression: **56/56 PASS**.
- Foundation lock/doctor and compileall: PASS.
- Exact-head checkout guard: PASS on both Linux and Windows.

## HEDS verdict
**APPROVED** after CR-001 and CR-002. No unresolved HIGH/CRITICAL findings.

## Residual boundary
An older, otherwise valid authenticated checkpoint can theoretically be restored by storage rollback; because checkpoints mint no permission/permit authority this is not treated as authorization replay. Future side-effecting skill ports should maintain idempotency/operation ledgers as their mutation surface expands.
