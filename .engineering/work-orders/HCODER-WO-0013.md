# HCODER-WO-0013 — Provider Certification Lab & Semantic Repository Twin

**Status:** IN PROGRESS  
**Issue:** #26  
**Risk:** HIGH_ASSURANCE  
**Task class:** T3  
**Context radius:** C4

## OBJECTIVE
Build a trusted provider-certification laboratory and semantic repository twin above HCODER-CP-0012 so exact model/agent stacks can be evaluated under independent execution/grading and repository semantics can be reasoned over without executing indexed code.

## CONTEXT
CP-0012 provides RepoDNA, TruthWeave, GenomePulse, ShadowBench, ChronoSeal, signed certification evidence and competence half-life. It does not yet provide a provider-backed trial runner/grader separation, durable rollback-resistant chronology with an external monotonic floor, semantic repository graph extraction, or auditable exact-stack certification reports.

## SCOPE
- Semantic Repository Twin from static RepoDNA text.
- SchemaSense, APIVein, Dataflow Echo and Dependency Cortex.
- Provider Certification Lab with sealed runner/grader identities.
- StackSeal exact-stack trial binding.
- TrialForge model-visible materialization with hidden oracle boundary.
- Blind grader contract.
- Contamination Radar downgrade/block-only semantics.
- DurableAttestationJournal and Durable ChronoSeal using a host-injected monotonic anchor.
- Trial receipts, benchmark attestation and auditable certification reports.
- Deterministic mocks and adversarial tests.

## OUT OF SCOPE
Real provider credentials in CI, billing, arbitrary code execution during indexing, remote control, distributed benchmark farms, universal multi-language semantics, automatic skill promotion, permission expansion or claims that a real provider stack is already DISTINGUISHED.

## FILES / SOURCES TO READ
- `docs/project-brain/11-CHECKPOINT.md`
- `docs/project-brain/10-DECISIONS-LEDGER.md`
- `docs/project-brain/05-SECURITY.md`
- `docs/project-brain/06-TEST-BENCHMARK-PLAN.md`
- `docs/project-brain/13-INTEGRATION-CONTRACTS.md`
- `hive_runtime/providers.py`
- `hive_runtime/expert_evaluation.py`
- `hive_runtime/repository_intelligence.py`
- `hive_runtime/evaluation_runtime.py`

## REQUIREMENTS
1. Runner and grader identities are host-sealed and lineage-separated.
2. Trial identity binds exact sealed Agent Profile/execution stack, provider/model, repository snapshot, semantic twin, benchmark dimension/family, hidden case and evaluation protocol.
3. Provider/model output cannot grade or certify itself.
4. Model-visible trial material contains no plaintext or host oracle secret.
5. Trial evidence is host-sealed before it can become BenchmarkResult evidence.
6. Benchmark evidence is verifiable by CP-0011 ExperienceLedger without trusting provider prose.
7. Persistent chronology must be HMAC authenticated and use a host-injected monotonic floor to detect signed rollback.
8. Semantic extraction is static/no-exec and deterministically fingerprinted.
9. Contamination signals only block/lower confidence.
10. No existing authority boundary is weakened.

## ARCHITECTURE RULES
- Competence and permission remain separate.
- Trusted-host authorities are injected and unavailable to model/tool surfaces.
- Exact-stack fingerprints cannot be inferred from provider marketing names.
- Unknown/tampered chronology, actor identity, trial seal or evidence fails closed.
- Repository semantics are descriptive evidence only.

## CONSTRAINTS
- Standard library only for this increment.
- No provider secrets in repository/tests/logs.
- No arbitrary repository execution.
- Existing public APIs remain backward compatible unless a Correction Delta explicitly approves a change.

## ACCEPTANCE CRITERIA
- Semantic Twin deterministically captures static symbols/dependencies/routes/schema/dataflow observations.
- Dependency Cortex provides bounded graph impact traversal.
- Durable chronology survives restart and rejects rollback below trusted anchor floor.
- StackSeal rejects profile/stack or actor independence mismatch.
- Trial replay is rejected durably for the same profile/case lineage.
- Contamination Radar blocks known exposure and cannot add score.
- Sealed trial receipts aggregate into verifiable BenchmarkResult evidence.
- Broad regression and Windows HIGH_ASSURANCE remain green.

## TESTS
Unit, adversarial filesystem/chronology/identity/tamper/replay tests, compileall, full Linux discovery suite and existing Windows HIGH_ASSURANCE regression.

## DELIVERABLES
Runtime code, tests, canonical docs, evidence, correction deltas if required, DEC-017, CP-0013 and checkpoint delta.

## REVIEW FORMAT
HEDS_DELTA exact-head. UNKNOWN is not PASS. HIGH/CRITICAL findings block promotion.

## STOP CONDITION
Exact-head Governance green; HEDS APPROVED; no open HIGH/CRITICAL; DEC-017 and CP-0013 APPROVED; squash merge; post-merge Governance green.
