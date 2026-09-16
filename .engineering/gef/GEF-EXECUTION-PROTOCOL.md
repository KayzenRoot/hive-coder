# GEF V1 Universal Execution Protocol — Hive Coder

## Pipeline
`ANALYZE -> SOURCE CHECK -> NEXT NECESSARY INCREMENT -> WORK ORDER -> CONTEXT LOCK -> PREFLIGHT -> EXECUTOR -> TESTS/EVIDENCE -> PR -> EXACT-HEAD AUDIT -> CHECKPOINT DELTA -> MERGE -> NEXT`.

## Discovery first
Before mutation, discover repository metadata/default branch, active PRs, source/docs/tests, manifests/locks, workflows, security/release state, existing engineering/governance, real validation commands and AI/agent instructions. Classify GREENFIELD | BROWNFIELD | HYBRID from evidence. Hive Coder baseline classification is BROWNFIELD.

## Collision model
Every proposed governance artifact is classified as `CREATE_SAFE | EXISTS_COMPATIBLE | EXISTS_NEEDS_MERGE | EXISTS_PROJECT_AUTHORITY | COLLISION | DEFER | NOT_APPLICABLE` before mutation.

## Work Order / Context Lock
Every substantial increment carries stable ID, objective, source inputs, in/out scope, allowed files, preservation constraints, requirements, architecture/security constraints, acceptance criteria, tests, evidence, review, recovery, deliverables and STOP CONDITION.

## Executor acceleration pack
Compile only the context required for the increment: Implementation Seed Tree, File Intent Capsule, Brownfield Patch Intent Capsule, Executor Navigation Map, Decision Closure Capsule, Execution Waves, Validation Reuse Plan, Critical Path and Marathon Execution Pack when useful.

## SOURCE_MATCH
Implementation starts only when repository identity/base, canonical sources, target paths/contracts and Context Lock remain compatible. Drift becomes `SOURCE_CONFLICT`; recompile/reconcile before mutation.

## Assurance ladder
- A0 structural/static/basic checks.
- A1 focused/direct tests.
- A2 impacted dependency/integration/risk-expansion tests.
- A3 hosted CI/security/platform gates.
- A4 independent exact-head semantic audit (HEDS delta in Hive Coder).

Existing real commands are authoritative. Never invent commands to satisfy the framework.

## Evidence
Evidence binds Work Order, exact base/head, commands/workflows, results, corrections, security findings and unresolved risk. A failure is never hidden by documentation.

## STOP states
`COMPLETE_CANDIDATE | SOURCE_CONFLICT | SCOPE_EXPANSION_REQUIRED | BLOCKED_EVIDENCE | NEEDS_ARCHITECTURE | BLOCKED_SECURITY | GEF_ADOPTION_IN_PROGRESS | GEF_ADOPTION_EXACT_HEAD_EVIDENCE_REQUIRED | GEF_ADOPTION_BLOCKED_BY_CAPABILITY_GAP | GEF_V1_ADOPTED_READY_FOR_GOVERNED_DEVELOPMENT`.
