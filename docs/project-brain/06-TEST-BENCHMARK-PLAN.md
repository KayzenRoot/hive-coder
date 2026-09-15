# Test & Benchmark Plan — Hive Coder

Baseline by risk:
- LOW: targeted deterministic checks.
- STANDARD: unit + lint + typecheck/build + relevant integration.
- ELEVATED: STANDARD + broad regression, persistence/security/recovery where applicable.
- HIGH_ASSURANCE: ELEVATED + independent review, adversarial/permission tests, rollback proof and platform-specific validation.

Computer-use tests must cover permission denial, emergency stop, wrong-window protection where feasible, sensitive-data redaction and safe failure.

## Expert-agent evaluation policy

Agent competence is measured independently from model/provider reputation. A model name, benchmark marketing claim, system prompt or agent self-description cannot promote competence.

The Hive competence matrix measures repository reasoning, debugging, architecture, testing, security, performance, maintainability, code review, long-horizon engineering, tool reliability and tamper resistance.

A Distinguished role profile must satisfy the versioned role standard across every required dimension. The initial WO-0011 standard requires at least 40 trusted samples per dimension, at least two independent benchmark families per dimension, a 95% Wilson lower confidence bound of at least 0.80, and zero critical benchmark failures, policy violations or tamper events.

Promotion must use benchmark-family diversity rather than a single public leaderboard. External suites are calibration signals only. They must be combined with fresh Hive-generated tasks, hidden adversarial tasks and project-specific evals. Known benchmark contamination, broken tasks, leakage or weak graders reduce confidence and must not be hidden.

Benchmark result trust belongs to a host verifier and evidence digest. Raw model/provider claims remain non-authoritative. Evaluation records must preserve suite/version identity, sample counts, incidents and evidence references.

## Freshness, novelty and repository binding

`HCODER-WO-0012` adds repository-aware evaluation controls:
- RepoDNA snapshot identity binds evaluation to exact indexed repository content.
- ShadowBench case generation is host-keyed and derived from verified repository facts.
- Hidden oracle material is represented by host-bound digests rather than model-visible answer text.
- Benchmark Novelty requires trusted ShadowBench case verification before admission; cosmetic case IDs, epoch changes or trivial mutations over one fact lineage do not count as independent novelty.
- Counterfactual Forge creates structure-bound what-if probes without mutating repository code.
- Production certification is HMAC-sealed by a trusted-host Certification Authority and binds exact Agent Profile, Competence Standard, competence report and repository snapshot.
- Certification observation time comes from monotonic trusted-host ChronoSeal, never from a model/caller-supplied freshness value.
- Competence Half-Life makes certification time-bounded. Evidence may become `DUE` or `EXPIRED` even when it was previously valid.
- Repository snapshot or execution-stack changes invalidate reuse of older certification unless a later governed compatibility rule explicitly proves equivalence.
- Outcome Echo is advisory-only. Negative regressions/rollbacks may force earlier recertification; positive production outcomes cannot mint benchmark evidence or promote competence.

Fresh hidden/project-specific suites should use multiple verified independent source lineages and preserve generation-version identity. A generator change is an evaluation protocol change and requires regression evidence. Never treat generated-case novelty as sufficient proof by itself: trusted execution, grading and evidence binding remain mandatory before a case contributes to Experience Ledger competence.

## Provider Certification Lab policy

`HCODER-WO-0013` adds HIGH_ASSURANCE laboratory controls for exact-stack trials:
- **StackGenome** canonically binds provider, model, model revision, toolset, capsule, skillset and runtime to the exact sealed Agent Profile execution-stack digest.
- **SuiteLineage Authority** seals suite identity and derives competence-family diversity from an independence root. Renaming or version-churning one lineage cannot create additional family diversity.
- Runner and grader identities are host-sealed with role, independence lineage and **EndpointSeal** digest. Runner/grader lineage or endpoint collapse is rejected.
- **TrialForge** verifies ShadowBench/repository/Semantic Twin bindings and exposes no oracle material to the provider runner.
- **One-Shot Trial Law** atomically and durably reserves profile + stack + hidden-case lineage before provider execution. Provider/grader failure cannot be used to reroll the same hidden case.
- **GradeProof** requires every grading decision to carry a host-verifiable rationale/evidence digest before a TrialReceipt can exist.
- Provider responses are bounded; invalid incident counters, oversized output or malformed responses fail closed.
- **Contamination Radar** is downgrade/block-only. Known exposure can invalidate a trial but can never increase success, confidence or rank.
- TrialReceipts are host-sealed and bind exact trial, profile, StackGenome, repository snapshot, Semantic Twin, SuiteLineage, dimension, response and durable chronology.
- **EvidenceDNA** wraps CP-0011 BenchmarkResult evidence with exact StackGenome + repository snapshot + Semantic Twin + SuiteLineage binding. A valid benchmark cannot be transplanted to another repository state or execution stack.
- Auditable certification accepts only verified EvidenceDNA envelopes matching the current exact certification context.
- Durable chronology is HMAC-authenticated and uses a host-injected external monotonic sequence floor to detect rollback of an otherwise valid older journal.

HIGH_ASSURANCE laboratory tests must include exact-head CI, runner/grader independence, endpoint collapse, grade-proof absence, concurrent reservation, signed rollback, case replay, StackGenome drift, SuiteLineage gaming, contamination blocks, EvidenceDNA tamper/transplant and unchanged Windows control-plane regression.

## Elite Specialist Forge & Arena policy

`HCODER-WO-0014` adds HIGH_ASSURANCE specialist composition, anti-overfit challenge admission and quality-first routing controls:
- ForgeSeal tests must reject unsealed AgentProfiles, specialization provenance tamper, exact StackGenome mismatch, SkillGenome transplant, repository snapshot drift, Semantic Twin transplant and stale/invalid certification.
- SkillGenome fingerprint must equal the certified StackGenome skillset digest before blueprint issuance.
- ChallengeMorph tests must prove challenge identity remains bound to trusted ShadowBench and sealed SuiteLineage while provider-visible material receives no oracle authority.
- Anti-Overfit Horizon tests must reject exact challenge replay, prompt replay and source/base-lineage replay. Mastery admission must independently re-enforce sealed base-lineage diversity so bypassing the horizon helper cannot inflate mastery.
- ArenaEvidence tests must reject telemetry tamper, GradeProof mismatch, blueprint/challenge transplant and repository/twin mismatch.
- Mastery Lattice must reject duplicate blueprint/challenge evidence and compute quality/reliability only from admitted trusted evidence.
- Diversity Quorum, minimum quality and minimum reliability floors are irreducible and must reject caller attempts to weaken them.
- Pareto Crown must directly reverify AgentProfile authority and current certification context at routing time.
- Critical, policy and tamper incidents must block candidate selection regardless of lower cost or latency.
- Cost/latency tests must prove optimization occurs only among candidates already satisfying all hard security, quality, reliability and diversity floors.
- Reliability Shadow tests must prove negative outcomes can block/demote/force recertification while positive outcomes cannot create mastery, benchmark evidence or authority.
- Deterministic selection must be identical for identical sealed evidence and policy inputs.

WO-0014 promotion requires exact-head Governance, full Ubuntu discovery with `ResourceWarning` fatal, unchanged Windows Server 2025 HIGH_ASSURANCE regression, adversarial HEDS, no unresolved HIGH/CRITICAL finding, and a documentation delta that does not overclaim real-provider evidence.

Technical head `54d19f3acbac6e20f34287d5fe12cc2316d89e23` established **256/256 Ubuntu PASS** and **56/56 Windows HIGH_ASSURANCE PASS** before promotion-document staging. The final promotion candidate must independently re-run those gates on its own exact head.

## Explicit evaluation limits

Hosted CI uses deterministic mock provider runners/graders and contains no production provider credentials. Passing laboratory or arena contract tests is therefore not evidence that a real model/provider stack has earned `DISTINGUISHED` or elite status.

The CP-0013 durable journal provides thread-safe atomic reservation inside one process. Cross-process/distributed reservation requires a later transactional/lease-backed laboratory service and is not approved by this checkpoint.

The host-injected `MonotonicAnchor` is a contract, not yet a production platform implementation. A later deployment may bind it to an OS secure store, TPM, remote attestation service or another independently reviewed monotonic authority.

Semantic Twin evidence is conservative static analysis. APIVein observations can include framework-like decorator patterns and Dataflow Echo is not dynamic taint analysis. These observations improve task construction/context but do not become architecture or security truth merely by existing.

WO-0014 `ArenaTelemetry` trust is an injected verifier contract. Hosted CI does not prove real provider billing/latency/reliability telemetry provenance. Mastery Lattice, Horizon state and Reliability Shadow are process/session-bounded in WO-0014; durable rollback-resistant reputation is not approved.

Future benchmark upgrades may add live provider qualification through locally provisioned credentials, stronger contamination estimation, cross-process transactional trial reservation, externally attested monotonic chronology, authenticated real-provider telemetry and durable mastery memory. `TelemetrySeal` and `MasteryVault` remain future direction only until separately governed. Never report unmeasured gains as facts.
