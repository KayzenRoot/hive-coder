# Evidence Bundle — HCODER-WO-0011

**Risk:** ELEVATED  
**Base:** `f02ee394e792324920478f00572933741ff8e037`  
**HEDS correction evidence head:** `5c1020ca56fd8efec6ac7b302b446c99ffab8453`  
**Governance:** `34924937295`

## Required invariants proven
- Agent competence is measured, not declared.
- Expertise Capsules and Agent Profiles cannot grant execution authority.
- Agent Profiles are trusted-host sealed and bind exact role, capsule, context ceiling, independence lineage, model capability set and execution-stack digest.
- Benchmark evidence binds the exact sealed profile fingerprint; changing the execution stack invalidates prior certification evidence.
- Trusted sample-set replay for the same profile/dimension is rejected.
- Context required for authoritative decisions must be host trusted; untrusted content remains explicitly labeled data.
- Code Truth facts require provenance and host verification before authority.
- Architectural Genome invariants bind to exact verified facts and the exact Project Digital Twin.
- Competence uses role-specific dimensions, irreducible rank floors, sample counts, benchmark-family diversity and Wilson 95% lower confidence bounds.
- A caller cannot weaken a `DISTINGUISHED` standard by configuration.
- Production AgentMesh and adversarial challenge paths accept only `DISTINGUISHED` competence standards.
- Critical benchmark failures, policy violations or tamper events block certification even with perfect pass rates.
- Provider/model names and generated self-description are absent from competence scoring.
- AgentMesh accepts only a sealed CP-0010 MasterPlan on the exact Digital Twin and enforces oversight/implementation lineage separation independent of step ordering.
- CounterPlan and Failure Oracle require host-sealed, registered, measured, role-eligible and lineage-separated challengers.
- Challenge output can block but cannot grant permissions, capabilities or evidence trust.

## Corrections
`HCODER-WO-0011-CR-001` closes competence portability, sample replay, configurable rank downgrade, reviewer/challenger independence, suite-family gaming, forged/stale challenge plan acceptance and auditability findings. Weak test fixtures were upgraded to the production rank floor rather than weakening the invariant.

## Deterministic evidence
Exact head `5c1020ca56fd8efec6ac7b302b446c99ffab8453`:
- Ubuntu 24.04 broad regression: **195/195 PASS**.
- Windows Server 2025 HIGH_ASSURANCE regression: **56/56 PASS**.
- Exact-head checkout verified on both jobs.
- `PYTHONWARNINGS=error::ResourceWarning` on test gates.

## Evaluation quality policy
No single public coding benchmark is promotion authority. Hive requires independent benchmark-family diversity plus fresh/project-specific/hidden evaluations. Benchmark contamination, leakage, broken tasks or weak graders are evaluation risks and cannot silently become competence evidence.

## HEDS verdict
**APPROVED for the expert-agent measurement, context, truth, routing, AgentMesh and bounded challenge contracts.**

No unresolved HIGH/CRITICAL finding remains in the approved scope.

## Explicit non-claim
This approval does **not** claim that any real provider-backed Hive agent has already earned `DISTINGUISHED`. WO-0011 proves the machinery that makes such a claim measurable and hard to fake. Real provider/model/tool stacks must earn certification through trusted evaluations bound to their exact profile fingerprint.
