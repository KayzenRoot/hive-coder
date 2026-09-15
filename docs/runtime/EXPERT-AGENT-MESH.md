# Hive Expert Agent Mesh

HCODER-WO-0011 turns specialist roles into measurable engineering profiles. The design goal is not to imitate a famous programmer's writing style. It is to reproduce the habits that make exceptional engineers effective: strong problem framing, explicit invariants, disciplined context selection, evidence-driven decisions, adversarial review, deep debugging, change-radius awareness, operational thinking and continual measured improvement.

## Non-negotiable principle

**Agent quality is measured, never declared.**

A system prompt, model name, provider marketing claim, generated self-description or one benchmark score cannot create a Principal or Distinguished agent. Promotion requires trusted-host benchmark evidence across multiple dimensions and independent suites, with enough samples to support a confidence-adjusted lower bound and zero critical integrity/policy/tamper incidents.

This competence layer remains descriptive. It cannot grant permissions, mint execution permits, activate skills, promote model capabilities or mark evidence trusted.

## Expertise Capsules

Each Hive role has a versioned capsule containing:
- engineering domains;
- principles and decision doctrine;
- explicit anti-patterns;
- review lenses;
- required model capabilities;
- descriptive tool kinds;
- required benchmark dimensions;
- provenance digest.

The first capsule library covers Planner, Architect, Backend, Frontend, Data, Security, QA, Performance, DevOps, Reviewer and Documentation.

Examples of doctrine include: preserving invariants before abstractions, designing retries with idempotency, treating concurrency as a first-class failure source, making loading/error/recovery states explicit, migration reversibility, least privilege, negative-path testing, tail-latency measurement, immutable artifact promotion, semantic-diff review and documentation aligned to verified reality.

Capsules do not grant the listed tools. Tool execution remains under the existing capability and permission layers.

## Sealed Agent Profiles

An `AgentProfile` binds an agent identity to exactly one role and one capsule fingerprint, plus required model capabilities, context budget and an independence lineage. Profiles are HMAC-SHA256 sealed by the trusted host. Changing the role, capsule, context budget, capability requirements or independence lineage invalidates the seal.

There is deliberately no self-declared competence level field in the profile. Competence comes from the Experience Ledger.

## ContextLens

ContextLens builds a minimum-sufficient context pack for a specialist instead of flooding every agent with the entire repository.

Rules:
- required context tags must be satisfied by trusted context;
- untrusted external/tool/web content may be carried only as `untrusted_data` and cannot satisfy authoritative context requirements;
- mandatory context is explicit;
- a deterministic token budget applies;
- if trusted required context cannot fit, selection fails closed rather than silently dropping facts;
- selection is deterministic for the same inputs.

This creates a hard instruction/data distinction for future prompt construction. A file, webpage, issue body, terminal output or UI string cannot become policy merely because it contains imperative text.

## Code Truth Map

The first Code Truth Map foundation stores fact identities, subject/predicate, object digest, provenance digest and tags. Fact producers cannot mark themselves trusted. A trusted-host verifier decides which facts enter the authoritative fingerprint.

Unverified facts can remain visible for investigation but cannot support architecture invariants or other authoritative decisions.

Future repository extraction can populate these facts from ASTs, schemas, manifests, tests, runtime probes and dependency graphs. That extraction is not claimed complete in WO-0011.

## Architectural Genome

The Architectural Genome binds important architecture invariants to:
- exact Project Digital Twin fingerprint;
- verified Code Truth facts;
- affected component identities;
- invariant statement digest;
- criticality.

If the project twin or any provenance fact changes, deterministic drift detection identifies the affected invariant. This provides a foundation for future architecture-preservation checks before and after autonomous edits.

## Experience Ledger

Benchmark claims are stored separately from trust. Only results accepted by a trusted-host verifier contribute to competence.

Each result includes:
- agent identity;
- benchmark dimension;
- suite and version;
- successes and sample count;
- critical failures;
- policy violations;
- tamper events;
- evidence digest.

Hive computes a Wilson lower confidence bound rather than routing on raw percentage alone. Small perfect samples therefore rank below large perfect samples.

## Benchmark dimensions

The first competence matrix covers:
1. repository reasoning;
2. debugging/root-cause isolation;
3. architecture;
4. testing/verification;
5. security;
6. performance;
7. maintainability/refactoring;
8. code review/defect detection;
9. long-horizon engineering;
10. tool reliability;
11. tamper resistance.

Every role receives the common repository/tool/tamper dimensions plus role-specific dimensions. Security agents, for example, must also prove security, code review, testing and debugging. Backend agents must prove debugging, testing, security, performance and maintainability.

## Distinguished standard

The initial distinguished policy requires, per required dimension:
- at least 40 trusted samples;
- at least two independent benchmark suites;
- Wilson 95% lower confidence bound of at least 0.80;
- zero critical benchmark failures;
- zero policy violations;
- zero tamper events.

These are promotion gates, not claims of literal equivalence to a named human engineer. The thresholds can be versioned as the internal eval program becomes harder and better calibrated.

## Benchmark diversity policy

No single public benchmark is authoritative enough to promote a Hive agent.

The evaluation program should combine:
- fresh repository-level issue/fix tasks;
- long-horizon engineering tasks;
- terminal/tool coordination tasks;
- hidden Hive regression and adversarial tasks;
- role-specific security/performance/data/frontend suites;
- fresh tasks sampled after the model's likely training cutoff when practical;
- project-specific tasks from Hive Coder itself.

Public benchmark scores are useful calibration signals, not promotion authority. Known benchmark contamination, broken tasks or task leakage must be treated as evaluation risk. Suite diversity exists specifically to reduce this failure mode.

## Experience Routing

`ExperienceRouter` considers only:
- valid host-sealed profiles;
- exact capsule match;
- trusted benchmark results;
- the configured role standard.

It ranks qualified candidates by weakest dimension lower bound first, then average lower bound and evidence volume. This is intentionally a weakest-link design: a backend agent cannot hide poor security behind excellent debugging, and a reviewer cannot hide poor defect detection behind tool speed.

Provider or model names are absent from the scoring formula.

## AgentMesh

`AgentMesh` binds each sealed CP-0010 MasterPlan step to a measured specialist. It revalidates the MasterPlan seal and exact Project Digital Twin before assignment.

Oversight roles (Security, QA, Reviewer) cannot share the same independence lineage already used by implementation assignments. This makes separation of duties explicit and creates a base for stronger future multi-model or multi-session independence policies.

The assignment records fingerprints of the profile, capsule and competence report so future execution/evidence can be tied to the exact specialist state selected for the task.

## CounterPlan and Failure Oracle

Two bounded adversarial challenge surfaces are established:
- **CounterPlan** searches for materially different approaches, hidden assumptions and simpler/reversible alternatives.
- **Failure Oracle** performs a pre-mortem against security, correctness, concurrency, migration, operational and verification failure modes.

Challenger identity is assigned by the trusted host, not returned by model text. Required challengers must have distinct independence lineages. Findings may block planning according to policy, but challengers cannot grant authority.

## What 'elite' means in Hive

Elite engineering is treated as a continuously earned status composed of:
- depth in a specialization;
- broad repository understanding;
- strong debugging and verification behavior;
- ability to reason across change radius and failure modes;
- low tool-error and low tamper rates;
- independent review quality;
- repeatable performance over statistically meaningful samples;
- zero tolerance for critical policy/integrity failures.

The next stages can add dynamic eval generation, benchmark decay, language/framework capsules, cross-agent debate scoring, repository-specific expertise, outcome feedback and automatic re-evaluation after model/capsule/tool changes. None of those future mechanisms should bypass the evidence and authority boundaries established here.