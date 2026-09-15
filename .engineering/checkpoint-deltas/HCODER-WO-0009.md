# Checkpoint Delta — HCODER-WO-0009

## From
HCODER-CP-0008

## To
HCODER-CP-0009

## Added
- Deterministic sequential Agent Task Runtime and DAG validation.
- Atomic HMAC-authenticated task checkpoints bound to plan fingerprint.
- Immutable task snapshots and structured execution history.
- CP-0008 capability-aware model routing inside task execution.
- Trusted prompt/skill execution ports with no authority minting.
- Pause/continue/cancel, crash recovery and explicit interrupted-skill handling.
- Per-node attempt budgets plus authenticated global execution/failure ceilings.
- Explicit monotonic trusted-host budget extension while paused.

## Corrections
- CR-001 HIGH: closed restart budget-broadening path.
- CR-002 MEDIUM: preserved in-flight pause state after result settlement.

## Evidence
Implementation head `82266bf8087f526767878801259c47c644ffaa33`; Governance `34917858327`; Ubuntu 128/128 PASS; Windows HIGH_ASSURANCE 56/56 PASS; HEDS APPROVED.

## Still not approved
Remote Hive Control, real provider credentials, parallel/distributed scheduling, automatic skill installation/self-promotion, additional desktop mutation capabilities.
