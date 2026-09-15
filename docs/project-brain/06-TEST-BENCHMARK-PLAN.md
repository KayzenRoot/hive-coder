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

ChronoSeal and Benchmark Novelty are session-bounded in CP-0012. Durable cross-restart time/novelty attestation is required before a future provider-backed certification service can rely on those properties across processes or machines.

Future benchmark upgrades should add stronger language/framework-specific task materialization, cost/latency telemetry, repair quality, regression severity, contamination estimation, durable benchmark lineage state and provider-backed re-certification. Never report unmeasured gains as facts.
