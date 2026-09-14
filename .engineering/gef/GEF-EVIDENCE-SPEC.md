# GEF V1 Machine Evidence Specification — Hive Coder

Machine evidence is primary; narrative must not invent unsupported facts.

Required manifest fields: `schemaVersion`, `workOrder`, `projectFingerprint`, `baseSha`, `headSha`, `taskClass`, `contextRadius`, `risk`, `changedFiles`, `decisions`, `tests`, `lint`, `typecheck`, `build`, `security`, `integration`, `benchmarks`, `gates`, `resolvedFindings`, `openFindings`, `risks`, `checkpointDelta`, `stopState`.

Proof states: `PROVEN | CARRY_FORWARD | INVALIDATED | UNKNOWN | NOT_REQUIRED`.

Rules: bind evidence to exact SHAs; record command/status/exit code and artifact identity; never synthesize usage/cost/reviewer/gate data; redact secrets and sensitive screenshots; do not commit raw user desktop traces unless explicitly sanitized and required; gate receipts belong in hosted artifacts/comments when practical.
