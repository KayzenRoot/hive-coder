# Correction Delta — HCODER-WO-0009-CR-002

## Finding
**MEDIUM · in-flight pause overwrite.** The first candidate allowed `pause()` to set task status to PAUSED while an execution port was running, but the completion path then overwrote status with PENDING/FAILED unconditionally.

## Correction
- Completion now detects whether a scheduling pause was requested while the node was in flight.
- Successful or retryable node settlement preserves PAUSED and records the node result.
- Non-retryable failure remains terminal and may override pause with FAILED.
- Cancellation marks any in-flight node INTERRUPTED and remains terminal.
- Added a deterministic threaded test that pauses during a blocking prompt, releases the prompt, proves the node settles SUCCEEDED while the task remains PAUSED, then requires explicit continue.

## Semantics
Pause is a scheduling pause, not a forced kill of the current external call. Cancellation remains the cooperative interruption signal supplied to execution ports.
