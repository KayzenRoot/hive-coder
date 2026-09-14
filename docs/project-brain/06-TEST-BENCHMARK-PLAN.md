# Test & Benchmark Plan — Hive Coder

Baseline by risk:
- LOW: targeted deterministic checks.
- STANDARD: unit + lint + typecheck/build + relevant integration.
- ELEVATED: STANDARD + broad regression, persistence/security/recovery where applicable.
- HIGH_ASSURANCE: ELEVATED + independent review, adversarial/permission tests, rollback proof and platform-specific validation.

Computer-use tests must cover permission denial, emergency stop, wrong-window protection where feasible, sensitive-data redaction and safe failure. Coding benchmarks will later measure task completion, latency, token/cost telemetry when exposed, regressions and repair quality. Never report unmeasured gains as facts.
