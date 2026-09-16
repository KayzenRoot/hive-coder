# HCODER-WO-0023 — Prebuilt Implementation Pack

**Status:** PREBUILT CONTRACT / EXECUTION NOT YET PROVEN  
**Base:** `22b56b0f3111158cbf50789b1647c5a578a171c1`  
**Issue:** #68

## Mission

Implement the smallest useful Hive-owned Git mutation: stage an explicit approved set of regular workspace files into the local repository index, without granting a model generic Git, shell or process authority.

## Fixed product contract

```text
GIT_STAGE_CONTRACT = "hive-git-stage-v1"
GIT_STAGE_ACTION = "git_stage_paths_v1"
GIT_STAGE_TARGET_STATE = "index_update"
MAX_STAGE_PATHS = 128
```

The capability class is `GovernedGitStageCapability`.

Required public surface:

```python
prepare_stage_request(session_id: str, paths: Sequence[str]) -> ActionRequest
stage_paths(request: ActionRequest, *, permit_token: str) -> GitStageReceipt
close() -> None
```

No method may accept arbitrary Git arguments or command text.

## Control-plane capability

Do not reuse `SHELL_EXECUTE`. Introduce a dedicated `Capability.GIT_WRITE = "git.write"` only if the control-plane change is explicitly included by Context Lock delta and its spec is HIGH, materially sensitive, mandatory approval, target field `workspace`. If introducing the enum would broaden this WO beyond the allowed-file set, stop and amend the Context Lock before implementation.

## Repository support envelope v1

Supported:
- selected workspace is the repository worktree root;
- `.git` is a real local directory, not symlink/reparse point;
- ordinary non-bare repository;
- index either absent in a valid unborn/empty repository state or a supported regular index format proven by the chosen adapter;
- explicit regular-file paths under the trusted root;
- path count `1..128`;
- deterministic unique normalized path ordering.

Fail closed for v1:
- linked worktrees / `.git` file indirection;
- submodules and nested repositories;
- bare repositories;
- sparse index unless adapter proof explicitly covers it;
- split index unless explicitly proven;
- unmerged/conflicted index entries unless explicitly proven;
- symlink/reparse targets;
- directories, devices, FIFOs/sockets and other special files;
- pathspec/glob magic;
- deleted-path staging in this first slice;
- executable filters or hooks required by repository configuration.

## Exact request arguments

Freeze these keys as a set:

```text
contract
repository_identity
repository_head
index_state
index_identity
index_sha256
paths
worktree_states
path_count
target_state
```

Rules:
- `contract == hive-git-stage-v1`.
- `target_state == index_update`.
- `paths` is the deterministic tuple/list of normalized repository-relative paths.
- `worktree_states` contains only bounded metadata per path: normalized path, stable file identity where available, SHA-256, byte length, regular-file state. No raw bytes.
- `repository_head` is the exact observed OID or explicit unborn sentinel.
- `index_state` is `absent` or `regular`.
- `index_identity` is an explicit absent sentinel or stable observed identity.
- `index_sha256` is an explicit absent sentinel or digest of the exact approved index bytes.
- approval display/audit must not contain raw worktree/index bytes.

## Mutation algorithm

1. Normalize/deduplicate/sort exact paths and reject anything outside the support envelope.
2. Open/pin or otherwise strongly identify the repository root and `.git` directory without following unsafe indirection.
3. Observe HEAD, index and every requested worktree path.
4. Build `ActionRequest` from exact observed state.
5. On execution, validate exact request shape and target workspace.
6. Re-observe repository identity, HEAD, index and worktree states. Reject stale approval before mutation.
7. Prepare the new index representation entirely before permit consumption where the adapter permits this without mutation.
8. Run final active-session/cancellation check.
9. Consume the single-use request-bound permit at the last safe boundary.
10. Recheck active session and the latest safely observable approved state.
11. Publish the index update atomically or through an adapter transaction whose crash/race semantics are explicitly proven. Never truncate the live index then rebuild it in place.
12. Verify resulting staged entries match the approved worktree digests and exact path set.
13. Return a receipt containing repository identity, old/new index digest/identity as applicable, exact staged paths and committed state. No raw bytes.
14. Cleanup only capability-owned temporary/lock state and never remove another process's lock.

## Concurrency and lock law

Git index concurrency is security-relevant. The implementation must use an ownership-safe lock/transaction mechanism equivalent in effect to Git's index lock discipline. Existing foreign lock means fail closed, not delete-and-retry. Temporary/lock cleanup requires ownership proof. Approval becomes stale if the live index or approved worktree state changes before publication.

Do not claim strict CAS unless the selected backend objectively supplies an expected-state atomic predicate. Otherwise document the bounded residual race exactly, as WO-0022 does for filesystem replacement.

## Hooks, attributes and filters

The staging adapter must not execute hooks. It must not silently invoke external clean/smudge/process filters. If faithfully producing Git blob/index state for repository attributes requires executable filters or unsupported configuration, fail closed. A future WO may govern that separately.

## Backend selection gate

Before implementation, compare at least:
- a pure/library Git implementation available to the runtime;
- a narrowly spawned `git` process with hooks/network/filter defenses;
- a Hive-owned index writer.

The default preference is a maintained library with explicit index transaction APIs and no process execution. A subprocess route is blocked by this pack unless a correction delta proves why it does not create generic process authority and how executable Git config/filter behavior is disabled. A bespoke index writer is blocked unless index-format correctness and cross-platform locking can be proven with focused tests.

## Tests to exist before promotion

`test_git_stage_contract.py` must cover exact request shape, deterministic path ordering, duplicate rejection/normalization law, stale HEAD/index/worktree rejection, exact approval binding, permit single-use, successful exact-path staging, receipt redaction and unsupported repo states.

`test_git_stage_security.py` must cover traversal, `.git`, symlink/reparse, pathspec/glob syntax, special files, foreign index lock, linked worktree, nested repo/submodule, cancelled/takeover/emergency session, tampered request, extra/missing path, content changed after approval, index changed after approval, no raw bytes in request/audit/receipt, no hooks/process/network execution.

Native proof must run on Windows, Linux and macOS. Platform skips require explicit evidence and cannot promote that platform.

## Evidence required

For the exact technical head record:
- workflow/run/job IDs;
- runner OS/version and architecture;
- Python/tool/library versions;
- focused test counts and skips;
- exact-head verification;
- security assertions for no shell/process/hook/network/credential authority;
- HEDS review with HIGH/CRITICAL = 0/0.

## Codex handoff bundle

Codex receives only:
`Checkpoint → Issue #68 → Context Lock → this Implementation Pack → Executor Brief → exact allowed-file list → failing acceptance tests → source symbols needed by those tests`.

It should complete implementation, not rediscover product scope.

## STOP

No commit/ref/branch/remote mutation. No generic Git command API. No terminal. No arbitrary `.git` filesystem capability. No production claim without independent native exact-head proof on all three target OSes.