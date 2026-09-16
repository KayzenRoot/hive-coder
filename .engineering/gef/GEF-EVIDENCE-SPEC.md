# GEF V1 Universal Evidence Specification — Hive Coder

Machine evidence is primary; narrative must not invent unsupported facts.

## Required identity
Evidence binds `schemaVersion`, `workOrder`, `repository`, `branch`, `baseSha`, `headSha`, `taskClass`, `contextRadius`, `risk`, `changedFiles`, `decisions`, `tests`, `lint`, `typecheck`, `build`, `security`, `integration`, `benchmarks`, `hostedGates`, `resolvedFindings`, `openFindings`, `risks`, `checkpointDelta`, `stopState`.

## Proof states
`PROVEN | CARRY_FORWARD | INVALIDATED | UNKNOWN | NOT_REQUIRED`.

## Rules
- Exact-head evidence only proves its exact SHA.
- Record real command/workflow identity, result/exit status and artifact identity where available.
- Never synthesize usage/cost/reviewer/gate data.
- A failed test remains failed until rerun evidence closes it.
- `UNKNOWN` cannot be converted to PASS.
- Hash integrity is not signing.
- Redact secrets and sensitive screenshots/traces.
- Do not commit raw user desktop traces unless explicitly sanitized and required.
- Brownfield legacy facts are historical evidence only; they do not become retroactive GEF acceptance.
- Hosted gate receipts belong in durable evidence/comments when practical.
