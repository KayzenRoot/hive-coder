# Definition of Done — Hive Coder

A product version is complete only when approved scope is functional, tested, documented, deployable and objectively validated.

For each increment: approved Work Order; Context Lock/source match; implementation only in scope; relevant tests/lint/typecheck/build/security/integration/benchmarks; Evidence Bundle exact-head; PR; HEDS audit; no unresolved HIGH/CRITICAL defect; accurate docs; approved Checkpoint Delta; merge under repository policy.

For a releasable desktop version additionally require secure permission model, installer/package, secrets handling, recovery/rollback, dependency/license compliance, supported-provider validation and end-to-end desktop-use proof on declared platforms.

## Prospective owner-only review gate (DEC-033, proposed in Issue #95/PR #96)
For work accepted **after** this governance change's merge, the mandatory semantic audit is an exact-head, evidence-backed `OWNER_SELF_AUDIT / NOT_INDEPENDENT` when performed by `KayzenRoot`, not a second GitHub account or fictitious independent approval. All other DoD obligations remain, including in-scope Work Order/Context Lock, security and adverse-case coverage, all required exact-head GitHub checks, zero unresolved HIGH/CRITICAL and no open blocking review thread. HIGH_ASSURANCE also requires explicit recorded owner threat/risk acceptance. Use a guarded squash merge and fresh exact-main postvalidation; never claim signing, live hardware E2E or unavailable secrets as passed. The historical `HEDS audit` in the original DoD remains a real semantic audit function, but future human-reviewer identity follows DEC-033, and past independent receipts remain untouched.
