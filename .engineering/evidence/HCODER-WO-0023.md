# HCODER-WO-0023 — Evidence Ledger

**Status:** PREBUILT / MUTATION UNPROVEN  
**Canonical base:** `22b56b0f3111158cbf50789b1647c5a578a171c1`  
**Issue:** #68

## Claims allowed now

- Current desktop Git observation is read-only and does not execute Git.
- Canonical workspace create/replace capabilities provide the control-plane pattern this WO must preserve.
- `git_stage_paths_v1` product contract, request fields and redaction model are prebuilt.
- Contract-level datatypes/tests may execute before a backend exists.

## Claims explicitly NOT allowed yet

- Git staging is implemented.
- Any Git mutation is safe or production-ready.
- `git.write` is canonical.
- Windows, Linux or macOS Git staging is proven.
- A backend/library dependency has been approved.
- Strict CAS of index/worktree state exists.

## Backend-selection checkpoint

Repository source inspection found no root Python dependency manifest and no existing Git library dependency. Therefore a third-party Git library cannot be silently introduced in this WO. The implementation must either:
1. add a separately reviewed provenance/dependency decision and Context Lock delta for a maintained library with safe index transaction APIs; or
2. prove a Hive-owned index backend sufficiently to satisfy cross-platform format, locking, atomic publication and adversarial tests.

A `git add` subprocess remains blocked because generic process/Git executable configuration behavior is outside this WO.

## Prebuilt acceptance state

- Contract constants/types: MATERIALIZED.
- Contract unit tests: MATERIALIZED.
- Security/adversarial test map: MATERIALIZED AS SKIPPED GATES.
- Control-plane `git.write`: NOT YET MATERIALIZED.
- Backend: NOT YET SELECTED/PROVEN.
- Native Windows proof: UNPROVEN.
- Native Linux proof: UNPROVEN.
- Native macOS proof: UNPROVEN.
- HEDS: NOT YET RUN.

## Promotion evidence template

For each exact technical head record:
- commit SHA;
- workflow/run/job IDs;
- runner OS/version/architecture;
- Python and Git-adapter/library version;
- focused test counts and **zero security-gate skips**;
- exact-head verification;
- index transaction/lock behavior;
- stale HEAD/index/worktree rejection;
- no shell/process/hook/filter/network/credential execution;
- permit consumption ordering;
- request/audit/receipt redaction;
- HEDS HIGH/CRITICAL counts.

## STOP

Skipped security acceptance tests are a hard non-promotion state. No merge/promotion of mutation authority until backend selection is governed, all required tests are executable, all three native target lanes are green at exact head, and HEDS reports H/C `0/0`.