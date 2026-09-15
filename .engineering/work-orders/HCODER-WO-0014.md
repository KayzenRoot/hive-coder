# HCODER-WO-0014 — Elite Specialist Forge & Autonomous Engineering Arena

**Status:** PROMOTION CANDIDATE  
**Issue:** #28  
**Risk:** HIGH_ASSURANCE  
**Task class:** T3  
**Context radius:** C4

## OBJECTIVE
Build a governed specialist-forging and autonomous engineering arena above HCODER-CP-0013 so exact-stack specialists are composed, challenged and selected through fresh independent evidence rather than labels, model fame or self-description.

## CONTEXT
CP-0013 provides exact-stack Provider Certification Lab evidence, StackGenome, SuiteLineage, EvidenceDNA, durable chronology and Semantic Repository Twin. It does not yet provide governed language/framework specialization packs, an anti-overfit arena, multi-objective telemetry-aware specialist selection or negative production-regression memory for routing.

## SCOPE
- Specialization Packs with trusted-host provenance and no authority fields.
- SkillGenome exact skill-composition descriptor.
- ForgeSeal SpecialistBlueprint bound to profile, StackGenome, repository, Semantic Twin, pack, skill genome and trusted certification evidence.
- ChallengeMorph hidden challenge variation from trusted ShadowBench cases and SuiteLineage.
- Anti-Overfit Horizon replay/lineage rejection.
- ArenaEvidence with trusted telemetry + GradeProof binding.
- Mastery Lattice multidimensional quality/reliability/cost/latency evidence.
- Diversity Quorum and irreducible arena quality/reliability floors.
- Reliability Shadow negative-only regression memory.
- Pareto Crown deterministic selection after safety/quality floors.
- Deterministic mock-only tests and adversarial HEDS.

## OUT OF SCOPE
Real paid provider credentials in hosted CI, autonomous billing/purchases, distributed benchmark farms, remote control, arbitrary repository execution, permission expansion, automatic skill activation, self-modifying policies or claims that any real model/provider is already elite.

## FILES / SOURCES TO READ
- `docs/project-brain/11-CHECKPOINT.md`
- `docs/project-brain/10-DECISIONS-LEDGER.md`
- `docs/project-brain/05-SECURITY.md`
- `docs/project-brain/06-TEST-BENCHMARK-PLAN.md`
- `docs/project-brain/13-INTEGRATION-CONTRACTS.md`
- `hive_runtime/expert_identity.py`
- `hive_runtime/expert_evaluation.py`
- `hive_runtime/evaluation_runtime.py`
- `hive_runtime/certification_contracts.py`
- `hive_runtime/certification_lab.py`

## REQUIREMENTS
1. Specialization labels/model names/self-description grant zero competence or authority.
2. ForgeSeal requires a sealed AgentProfile, exact StackGenome binding, trusted Specialization Pack and trusted exact-repository certification.
3. SkillGenome must match the skillset digest represented by the exact StackGenome.
4. ChallengeMorph must use trusted ShadowBench cases and sealed SuiteLineage without oracle exposure.
5. Anti-Overfit Horizon rejects exact, prompt and source-lineage replay.
6. Arena evidence must bind challenge, blueprint, repository, twin, grade proof and verified telemetry.
7. Mastery Lattice counts one evidence item per blueprint/challenge pair and uses confidence-adjusted quality/reliability.
8. Quality, reliability and diversity floors cannot be weakened by caller policy.
9. Cost/latency may optimize among safe qualified candidates but never override quality/security/tamper floors.
10. Reliability Shadow is negative-only and can block/demote; it cannot promote mastery.
11. Pareto Crown revalidates certification at selection time and is deterministic for identical evidence/policy.
12. Existing CP-0005 through CP-0013 authority boundaries remain unchanged.

## ARCHITECTURE RULES
- Competence is separate from execution authority.
- Trusted-host authorities/verifiers remain unavailable to model/tool surfaces.
- No specialization artifact contains permission grants or skill-activation authority.
- Unknown/tampered seals, evidence, telemetry or certification fail closed.
- Quality/safety floors precede optimization.

## CONSTRAINTS
- Python standard library only for this increment.
- No provider credentials in repository/tests/logs.
- No arbitrary repository execution.
- Existing public APIs remain backward compatible unless a Correction Delta explicitly approves a change.

## ACCEPTANCE CRITERIA
- Sealed specialization packs and blueprints are exact-stack/repository/twin bound.
- ChallengeMorph + Anti-Overfit Horizon reject replay and cosmetic challenge churn.
- ArenaEvidence seals verified telemetry and GradeProof.
- Mastery Lattice rejects duplicate challenge evidence and computes confidence-adjusted metrics.
- Pareto Crown selects only certified specialists satisfying irreducible quality/reliability/diversity floors.
- Cost/latency cannot win over a candidate that fails reliability/quality or has policy/tamper/critical incidents.
- Regression Memory can block a previously qualified specialist without manufacturing positive competence.
- Full Linux regression and Windows HIGH_ASSURANCE remain green.

## TESTS
Unit/adversarial seal, stack/skill binding, replay, evidence tamper, policy-floor, regression-memory and deterministic selection tests; compileall; full Linux discovery suite; existing Windows HIGH_ASSURANCE regression.

## DELIVERABLES
Runtime code, tests, canonical docs, evidence, Correction Deltas if required, DEC-018, CP-0014 and checkpoint delta.

## REVIEW FORMAT
HEDS_DELTA exact-head. UNKNOWN is not PASS. HIGH/CRITICAL findings block promotion.

## PROMOTION CANDIDATE STATE
Technical runtime head `54d19f3acbac6e20f34287d5fe12cc2316d89e23` is HEDS-approved for promotion candidate and passed Governance run `34965734345` with Ubuntu **256/256 PASS** and Windows Server 2025 HIGH_ASSURANCE **56/56 PASS**. `CR-001..CR-004` are resolved. Promotion documentation is staged under this same PR and must pass its own exact-head Governance + final HEDS before DEC-018/CP-0014 can become APPROVED.

## STOP CONDITION
Exact-head Governance green; HEDS APPROVED; no open HIGH/CRITICAL; DEC-018 and CP-0014 APPROVED; squash merge; post-merge Governance green.
