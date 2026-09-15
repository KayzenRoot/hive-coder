# Correction Delta — HCODER-WO-0004-CR-004

## Finding
**HIGH · EMERGENCY-STOP RESPONSIVENESS.** Cancellation callbacks in the first candidate ran while the control-plane lock was held. A blocked or faulty adapter callback could therefore delay the emergency-stop call and stall unrelated authorization operations.

## Correction
Session state, epoch rotation and token invalidation happen synchronously under the lock, then cancellation callbacks are dispatched on isolated daemon threads outside the critical execution path. Callback exceptions are contained and audited. This preserves immediate fail-closed authorization while preventing a hung callback from holding the control-plane lock.

## Regression proof required
A blocking callback test must prove `emergency_stop()` returns while the callback is still blocked, session state is already `EMERGENCY_STOPPED`, and callback failures remain contained/audited.
