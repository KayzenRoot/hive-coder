# HCODER-WO-0023 — Context Lock

**Status:** LOCKED FOR PREBUILT IMPLEMENTATION  
**Issue:** #68  
**Canonical base:** `22b56b0f3111158cbf50789b1647c5a578a171c1`  
**Risk:** HIGH_ASSURANCE  
**Authority delta:** first repository-local Git index mutation only

## Source check
The current desktop Git surface is read-only and deliberately does not execute Git. `apps/desktop/src-tauri/src/lib.rs` discovers `.git`, reads bounded `HEAD`, loose refs and `packed-refs`, rejects symlink/reparse traversal, rejects linked-worktree gitdir files, and reports provenance `git-head-read-v1`.

The canonical filesystem mutation layer in `hive_runtime/workspace_files.py` supplies the pattern to preserve: trusted canonical workspace, exact request arguments, mandatory HIGH approval, request-bound single-use permit at the final safe mutation boundary, active-session rechecks, fail-closed native backends and `.git` excluded from arbitrary filesystem-write authority.

`Capability` currently has no Git-specific mutation capability. `SHELL_EXECUTE` is CRITICAL and is not an acceptable implementation route.

## Selected first slice
The first Git mutation is exact-path staging/index update, action `git_stage_paths_v1`. It stages approved current workspace content for an explicit bounded path set. It does not commit and does not expose generic Git commands.

A subprocess `git add`, even without a shell, is not pre-approved because it crosses into process/tool execution and Git configuration/filter behavior requiring separate proof.

## Request binding candidate
Bind contract version, canonical workspace/repository identity, deterministic normalized path set, observed worktree state, observed index identity/state and target state `index_update`. No raw bytes in approval/audit metadata. Exact names are frozen by the implementation pack.

## Security law
1. Default deny and mandatory trusted approval.
2. Single-use request-bound permit only after safe non-mutating preparation.
3. Revalidate repository, index and approved worktree state as late as safely possible.
4. Workspace root must be the supported repository root. Nested repos, submodules, linked worktrees and gitdir indirection are unsupported unless separately proven.
5. `.git` remains forbidden as arbitrary workspace file path; dedicated adapter access is limited to exact index objects required by contract.
6. No shell, generic process authority, hooks, executable filters, network, remotes, credentials or config mutation.
7. No commit/tag/branch/reset/checkout/restore/clean/stash/merge/rebase/cherry-pick/delete/ref mutation.
8. Symlink/reparse/path traversal and special files fail closed.
9. Session cancellation, takeover, expiry and emergency epoch remain authoritative.
10. Windows, Linux and macOS require independent exact-head evidence.

## Allowed-file set
Prebuilt phase may change only:
- `.engineering/context-locks/HCODER-WO-0023.md`
- `.engineering/prebuilt/HCODER-WO-0023-IMPLEMENTATION-PACK.md`
- `.engineering/prebuilt/HCODER-WO-0023-EXECUTOR-BRIEF.md`
- `.engineering/prebuilt/HCODER-HARNESS-FRONTIER-v1.md`
- `.engineering/prebuilt/HCODER-HARNESS-BENCHMARK-v1.md`
- `.engineering/evidence/HCODER-WO-0023.md`
- `.engineering/work-orders/HCODER-WO-0023.md`
- `docs/project-brain/adrs/DEC-027-GOVERNED-GIT-STAGING.md`
- `hive_runtime/git_stage_contract.py`
- `hive_runtime/git_stage.py`
- focused `hive_runtime/git_stage_*` platform/backend files if objectively required
- `tests/runtime/test_git_stage_contract.py`
- `tests/runtime/test_git_stage_security.py`
- focused Windows/Linux/macOS native Git-stage tests if objectively required
- `.github/workflows/governance.yml` only for exact native proof lanes/tests

Any expansion requires explicit Context Lock delta before code changes.

## Harness frontier note
Non-authority-expanding harness frontier and benchmark specifications may be developed in this WO because they constrain how this and later executors receive context, prove actions and stop. They must not activate new runtime permissions inside WO-0023. Executable frontier mechanisms belong to explicit future Work Orders with independent evidence.

## STOP CONDITION
STOP and return to architecture/review if safe staging requires generic shell/process execution, Git hooks/external filters, remote/network access, credentials, arbitrary `.git` writes, unsupported repository indirection or weakening the Permission & Control Plane. No commit capability is included.