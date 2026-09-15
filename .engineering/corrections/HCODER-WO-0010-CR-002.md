# Correction Delta — HCODER-WO-0010-CR-002

## Findings
1. **HIGH · direct MasterPlan forgery:** a caller could construct a public `MasterPlan` and reach compiler/orchestrator paths without proving it passed DeepPlan and Council.
2. **HIGH · stale/cross-plan evidence and false STOP:** trusted evidence was not cryptographically bound to the current MasterPlan, and evidence-only STOP could become true while runtime steps were still pending.
3. **MEDIUM · objective constraints lacked deterministic plan coverage:** acceptance criteria were mapped but constraints could be silently omitted by the plan.
4. **MEDIUM · MasterPlan fingerprint omitted semantic fields:** assumption statements and step titles were not represented in the plan identity.

## Corrections
- Added trusted-host `PlanApprovalAuthority` using HMAC-SHA256 with a minimum 256-bit key.
- DeepPlan returns a sealed MasterPlan; `PlanGraphCompiler`, `AgentOrchestrator` and `SelfCorrectionLedger` reject missing/invalid seals.
- MasterPlan fingerprint now binds step title, instruction digest, requirements, constraints, change targets, capabilities, dependency graph, assumption statement digest/confidence/evidence refs, Council findings and Change Radius.
- `EvidenceRecord` is bound to `subject_fingerprint`; `EvidenceGraph` rejects evidence from any other MasterPlan.
- Orchestrator STOP now requires both 100% runtime step success and evidence-complete STOP Intelligence.
- Every objective constraint must be mapped by at least one approved PlanStep.
- Added adversarial tests for plan tampering, unsealed plans, stale evidence reuse, incomplete-runtime false completion and constraint omission.

## Residual boundary
Self-correction remains deliberately session-bounded. Automatic cross-restart self-correction stays disabled until correction state/budgets have their own trusted persistence contract.
