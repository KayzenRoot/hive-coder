# Test & Benchmark Plan — Hive Coder

Baseline by risk:
- LOW: targeted deterministic checks.
- STANDARD: unit + lint + typecheck/build + relevant integration.
- ELEVATED: STANDARD + broad regression, persistence/security/recovery where applicable.
- HIGH_ASSURANCE: ELEVATED + independent review, adversarial/permission tests, rollback proof and platform-specific validation.

Computer-use tests must cover permission denial, emergency stop, wrong-window protection where feasible, sensitive-data redaction and safe failure.

## Expert-agent evaluation policy

Agent competence is measured independently from model/provider reputation. A model name, benchmark marketing claim, system prompt or agent self-description cannot promote competence.

The first Hive competence matrix measures repository reasoning, debugging, architecture, testing, security, performance, maintainability, code review, long-horizon engineering, tool reliability and tamper resistance.

A Distinguished role profile must satisfy the versioned role standard across every required dimension. The initial WO-0011 standard requires at least 40 trusted samples per dimension, at least two independent suites per dimension, a 95% Wilson lower confidence bound of at least 0.80, and zero critical benchmark failures, policy violations or tamper events.

Promotion must use suite diversity rather than a single public leaderboard. External suites such as repository-level issue resolution, long-horizon engineering and terminal/tool benchmarks are calibration signals only. They must be combined with fresh Hive-generated tasks, hidden adversarial tasks and project-specific evals. Known benchmark contamination, broken tasks, leakage or weak graders reduce confidence and must not be hidden.

Benchmark result trust belongs to a host verifier and evidence digest. Raw model/provider claims remain non-authoritative. Evaluation records must preserve suite/version identity, sample counts, incidents and evidence references.

Future benchmark upgrades should add dynamic/fresh task generation, language/framework suites, cost/latency telemetry, repair quality, regression severity, benchmark decay and post-upgrade re-certification. Never report unmeasured gains as facts.