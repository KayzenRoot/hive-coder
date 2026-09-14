# GEF V1 Execution Protocol — Hive Coder

## Pipeline
`REQUEST -> Source Drift Sentinel -> Task Class/Risk -> Context Radius -> Work Order -> Context Lock -> Patch Recipe -> SOURCE_MATCH -> bounded implementation -> A0/A1/A2 -> Evidence Bundle -> PR -> A3 hosted gates -> HEDS Delta -> exact-head verdict`.

## Execution Pack contract
Every pack carries project/WO/branch, authorized base/head, task class, radius, risk, accepted/frozen decisions, one bounded goal, allowed files/symbols, prescribed transform/postconditions, forbidden shortcuts, tests, budgets, deliverables, review format, and exact STOP condition.

## SOURCE_MATCH
Implementation starts only when repository identity/base, checkpoint/decisions, target paths/contracts and Context Lock remain compatible. Drift => `SOURCE_CONFLICT` and recompile/rebase.

## Assurance
- `A0`: syntax/static/basic checks.
- `A1`: focused tests.
- `A2`: impacted regression/integration/evals.
- `A3`: hosted CI/security/platform gates.
- `A4`: independent HEDS semantic audit.

## STOP states
`COMPLETE_CANDIDATE | SOURCE_CONFLICT | SCOPE_EXPANSION_REQUIRED | BLOCKED_EVIDENCE | NEEDS_ARCHITECTURE | BLOCKED_SECURITY`.
