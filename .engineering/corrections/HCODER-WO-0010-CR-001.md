# Correction Delta — HCODER-WO-0010-CR-001

## Findings
1. **HIGH · planner self-verification:** first candidate allowed planner output to mark an assumption VERIFIED merely by supplying an evidence reference.
2. **HIGH · council role self-identification:** first candidate accepted the reviewer role from council output, allowing an untrusted model response to impersonate an independent reviewer.
3. **HIGH · evidence self-trust:** first candidate accepted `trusted=true` inside an evidence record supplied by the producer.
4. **MEDIUM · snapshot identity too weak:** telemetry checked step IDs but not the CP-0009 TaskPlan fingerprint.
5. **MEDIUM · depth truncation ambiguity:** Change Radius could hit a depth ceiling while undiscovered downstream nodes remained without setting `truncated`.
6. **LOW · stale TaskSnapshot fixture:** new orchestration tests omitted the authenticated budget field added by WO-0009.

## Corrections
- VERIFIED assumptions now require a trusted-host `AssumptionEvidenceVerifier`; planner claims alone cannot promote confidence.
- Hive chooses each required Council role and calls the Council port with that role; model output returns role-less assessments and cannot impersonate another reviewer.
- `EvidenceRecord` has no trust flag. `EvidenceGraph` requires a trusted-host `EvidenceTrustVerifier` and stores trust separately from producer data.
- Evidence link validation is atomic before graph mutation.
- Orchestrator telemetry requires exact CP-0009 TaskPlan fingerprint plus exact step identity.
- Change Radius marks node or depth truncation explicitly and DeepPlan fails closed on truncation.
- ELEVATED planning now blocks MEDIUM/HIGH/CRITICAL Council findings.
- TaskSnapshot tests use the current CP-0009 budget-bearing contract.

## Residual boundary
`SelfCorrectionLedger` is intentionally session-bounded in WO-0010 and is not yet automatically replayed after restart. Future autonomous restart integration must persist correction budget/state through a trusted host mechanism before enabling automatic cross-restart self-correction.
