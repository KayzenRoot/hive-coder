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
Capability class: `GovernedGitStageCapability`.

Required surface:
```python
prepare_stage_request(session_id: str, paths: Sequence[str]) -> ActionRequest
stage_paths(request: ActionRequest, *, permit_token: str) -> GitStageReceipt
close() -> None
```
No arbitrary Git arguments or command text.

## Control plane
Never reuse `SHELL_EXECUTE`. A dedicated `Capability.GIT_WRITE = "git.write"` requires an explicit Context Lock delta covering control-plane files. It must be HIGH, materially sensitive, mandatory approval and workspace-targeted.

## Repository support envelope v1
Support only repository-root trusted workspaces with a real local `.git` directory, ordinary non-bare repository, proven regular/absent index, explicit regular files, `1..128` paths and deterministic unique normalized ordering.

Fail closed for linked worktrees/gitdir indirection, submodules/nested repositories, bare repositories, unproven sparse/split/conflicted indexes, symlink/reparse targets, special files, pathspec/glob magic, deleted-path staging, executable filters/hooks and unsupported configuration.

## Exact request arguments
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
Raw worktree/index bytes never enter approval or audit metadata.

## Mutation algorithm
1. Normalize/deduplicate/sort paths and reject unsupported input.
2. Strongly identify repository root and `.git` without unsafe indirection.
3. Observe HEAD, index and requested worktree state.
4. Build exact ActionRequest.
5. Validate exact request shape/target on execution.
6. Re-observe repository/HEAD/index/worktree and reject stale approval.
7. Prepare new index representation before permit consumption wherever safely possible.
8. Final active-session/cancellation check.
9. Consume request-bound single-use permit at the last safe boundary.
10. Recheck session and latest safely observable approved state.
11. Publish via ownership-safe transaction. Never truncate the live index and rebuild in place.
12. Verify staged entries equal approved path/digest set.
13. Return redacted receipt with repository identity, old/new index state and exact paths.
14. Cleanup only capability-owned temporary/lock state.

## Concurrency and filters
Foreign index locks fail closed and are never stolen/deleted. Cleanup requires ownership proof. HEAD/index/worktree changes make approval stale. Never claim strict CAS without an expected-state publication predicate. No hooks or silent external clean/smudge/process filters; unsupported executable transformations fail closed.

## Backend selection gate
Compare a maintained local Git library, a narrowly spawned Git process and a Hive-owned index writer. Prefer a maintained library with explicit local index transactions and no process execution. Subprocess and bespoke writer routes remain blocked until their larger proof burden is explicitly accepted.

## Hive Harness execution laws
WO-0023 is the first consumer of the Hive Harness Frontier. Executor bundles are **proof-carrying and delta-minimized**:
- **Context Capsule:** provide exact source symbols, decisions, tests and dependency facts required by the WO. Full-repository context is fallback, not default.
- **Capability Budget:** declare the exact authority set. Any request outside it stops instead of escalating implicitly.
- **Mutation Budget:** declare expected files/symbols and maximum semantic radius. Unexpected mutation is drift evidence.
- **Proof-Carrying Action:** privileged mutation produces request digest, permit identity, pre-state digest, post-state digest and native evidence reference without leaking secrets/raw content.
- **Counterfactual Gate:** promotion requires evidence that stale, tampered and extra-authority variants fail, not merely that the happy path passes.
- **Context Delta Ledger:** each executor round persists only changed decisions, facts and evidence. The next round consumes immutable anchors plus the delta rather than replaying the transcript.
- **Uncertainty Ledger:** unresolved assumptions are explicit machine-addressable gates and cannot silently become implementation facts.
- **Evidence Graph:** requirement → decision → contract → test → CI job → review → checkpoint edges must be traceable; missing required edges block promotion.
- **Rollback Capsule:** mutation-heavy rounds record the smallest verified rollback boundary and identities needed to restore it.
- **Entropy Budget:** duplicated context, repeated discovery and unconstrained logs are harness defects. Prefer compact deterministic summaries and targeted retrieval.
- **Speculative Parallelism with Merge Firewall:** independent read/review/test agents may work concurrently, but mutations converge only through one governed integration lane with conflict and evidence checks.
- **Adaptive Model Routing:** future orchestration may route discovery, coding, review and verification to different models by measured task risk/cost/quality, while policy remains model-independent.

These laws add no runtime authority in WO-0023. Executable machinery for them requires explicit future Work Orders.

## Tests before promotion
Contract tests cover exact request shape, deterministic ordering, normalization/duplicate law, stale HEAD/index/worktree rejection, exact approval binding, permit single-use, exact-path staging, redaction and unsupported states.

Security tests cover traversal, `.git`, symlink/reparse, pathspec/glob, special files, foreign index lock, linked worktree, nested repo/submodule, cancellation/takeover/emergency state, tampered request, extra/missing path, post-approval content/index changes, no raw bytes and no hooks/process/network execution.

Native proof runs independently on Windows, Linux and macOS. Platform skips cannot promote that platform.

## Evidence required
Record exact technical head, workflow/run/job IDs, runner OS/version/architecture, runtime/library versions, focused test counts/skips, exact-head verification, security assertions and HEDS HIGH/CRITICAL `0/0`.

## Executor handoff bundle
Any executor receives only:
`Checkpoint → Issue #68 → Context Lock → Implementation Pack → Executor Brief → Context Capsule → exact allowed-file/symbol list → failing acceptance tests → Uncertainty Ledger → expected Evidence Graph edges`.

It completes implementation rather than rediscovering product scope.

## STOP
No commit/ref/branch/remote mutation. No generic Git command API. No terminal. No arbitrary `.git` filesystem capability. No production claim without independent native exact-head proof on all three target OSes.