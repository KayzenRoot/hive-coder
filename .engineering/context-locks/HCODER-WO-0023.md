# HCODER-WO-0023 — Context Lock

**Status:** LOCKED FOR PREBUILT IMPLEMENTATION  
**Issue:** #68  
**Canonical base:** `22b56b0f3111158cbf50789b1647c5a578a171c1`  
**Risk:** HIGH_ASSURANCE  
**Authority delta:** first repository-local Git index mutation only

## Source check

The current desktop Git surface is read-only and deliberately does not execute Git. `apps/desktop/src-tauri/src/lib.rs` discovers `.git`, reads bounded `HEAD`, loose refs and `packed-refs`, rejects symlink/reparse traversal, rejects linked-worktree gitdir files, and reports provenance `git-head-read-v1`.

The canonical filesystem mutation layer in `hive_runtime/workspace_files.py` already provides the pattern to preserve: trusted canonical workspace, exact request arguments, mandatory HIGH approval, request-bound single-use execution permit consumed at the final safe mutation boundary, active-session rechecks, fail-closed native backends and `.git` excluded from arbitrary filesystem-write authority.

`Capability` currently has no Git-specific mutation capability. `SHELL_EXECUTE` is CRITICAL and is explicitly not an acceptable implementation route for this WO.

## Selected first slice

The first Git mutation is **exact-path staging/index update**, product action `git_stage_paths_v1`. It stages the approved current workspace content for an explicit bounded set of paths into the repository index. It does not commit and does not expose a generic Git command surface.

The executor must prefer a Hive-owned library/native Git index adapter that can prove no hook/process/network execution. A subprocess invocation of `git add`, even without a shell, is NOT pre-approved by this lock because it crosses into generic process/tool execution and Git configuration/filter behavior that requires a separate proof.

## Request binding candidate

The request must bind at minimum:
- contract version;
- canonical workspace/repository identity;
- exact normalized path set in deterministic order;
- observed worktree state for each path sufficient to reject stale approval;
- observed index identity/state sufficient to reject stale approval;
- target state `index_update`;
- no raw file bytes in approval/audit metadata.

Exact field names are frozen by the implementation pack before executor work.

## Security law

1. Default deny and mandatory trusted approval.
2. Single-use request-bound permit consumed only after all non-mutating validation/preparation that can safely occur before mutation.
3. Revalidate repository identity, index identity/state and approved path worktree state as late as safely possible.
4. Workspace root must itself be the supported repository root for this first slice. Nested repositories, submodules, linked worktrees and gitdir indirection are unsupported unless separately proven.
5. `.git` remains forbidden as an arbitrary workspace file path. Any index access is internal to the dedicated Git adapter and limited to the exact index objects required by this contract.
6. No shell, generic process authority, hooks, filters that execute external programs, network, remotes, credentials or config mutation.
7. No commit, tag, branch, reset, checkout, restore, clean, stash, merge, rebase, cherry-pick, delete or arbitrary ref mutation.
8. Symlink/reparse/path traversal fails closed. Special file types fail closed.
9. Session cancellation, takeover, expiry and emergency epoch semantics remain authoritative.
10. Windows, Linux and macOS require independent exact-head evidence.

## Allowed-file set

Prebuilt phase may change only:
- `.engineering/context-locks/HCODER-WO-0023.md`
- `.engineering/prebuilt/HCODER-WO-0023-IMPLEMENTATION-PACK.md`
- `.engineering/prebuilt/HCODER-WO-0023-EXECUTOR-BRIEF.md`
- `.engineering/evidence/HCODER-WO-0023.md`
- `.engineering/work-orders/HCODER-WO-0023.md`
- `docs/project-brain/adrs/DEC-027-GOVERNED-GIT-STAGING.md`
- `hive_runtime/git_stage_contract.py`
- `hive_runtime/git_stage.py`
- focused `hive_runtime/git_stage_*` platform/backend files if objectively required
- `tests/runtime/test_git_stage_contract.py`
- `tests/runtime/test_git_stage_security.py`
- focused Windows/Linux/macOS native Git-stage tests if objectively required
- `.github/workflows/governance.yml` only to add exact native proof lanes/tests

Any expansion requires an explicit Context Lock delta before code changes.

## STOP CONDITION

STOP and return to architecture/review if safe staging requires generic shell/process execution, Git hooks or external filters, remote/network access, credentials, arbitrary `.git` writes, unsupported repository indirection, or weakening the Permission & Control Plane. No commit capability is included in WO-0023.