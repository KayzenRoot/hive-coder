# Correction Delta — HCODER-WO-0010-CR-003

## Findings
1. **HIGH · stale Project Digital Twin replay:** a correctly sealed MasterPlan could remain executable even if the current project dependency map changed after planning.
2. **MEDIUM · constraint completion evidence gap:** objective constraints were required to appear in the plan but STOP Intelligence did not require trusted evidence that those constraints remained satisfied.

## Corrections
- `ProjectDigitalTwin` now has a deterministic SHA-256 fingerprint over canonical component kind/dependency state.
- The twin fingerprint is included in the sealed MasterPlan identity.
- `PlanGraphCompiler`, `AgentOrchestrator` and `SelfCorrectionLedger` require the current twin fingerprint to match the approved MasterPlan before proceeding.
- `EvidenceGraph` now links trusted evidence separately to objective constraints as well as acceptance criteria and STOP conditions.
- `StopIntelligence` exposes `missing_constraints` and cannot complete until every objective constraint has trusted evidence.
- Added adversarial tests proving a changed twin invalidates compilation/orchestration and complete tests/reviews without constraint evidence still cannot satisfy STOP.

## Residual boundary
The WO-0010 Digital Twin is a host-supplied structural snapshot, not yet the future Code Truth Map. Automated repository extraction, provenance-backed twin refresh and architectural invariant mining remain later governed increments.
