# Correction Delta — HCODER-WO-0009-CR-001

## Finding
**HIGH · restart budget broadening.** The first candidate kept global execution/failure ceilings only in constructor configuration. A resumed task could therefore be instantiated with larger limits without an authenticated, auditable checkpoint transition.

## Correction
- Active execution/failure ceilings are now persisted inside the HMAC-authenticated checkpoint payload.
- `resume()` requires runtime budget configuration to exactly match the authenticated persisted budget.
- Budget changes require explicit `extend_budget()` while the task is paused.
- Extensions are monotonic, bounded by `TaskBudget.validate()`, logged as `budget_extended`, and cannot occur while interrupted nodes await recovery.
- Scheduling/retry checks use persisted state ceilings rather than mutable constructor state.
- Added tests proving silent restart broadening is rejected and explicit extension is audited.

## Residual boundary
Budget extension is a trusted host operation and is not exposed to prompt/skill execution ports. Future UI/orchestrator policy may place additional human/policy approval around this host operation.
