# DEC-027 — Governed Git Staging Boundary

**Status:** PROPOSED  
**Work Order:** `HCODER-WO-0023`  
**Issue:** `#68`  
**Source main:** `22b56b0f3111158cbf50789b1647c5a578a171c1`

## Context
Hive Coder can safely create and replace trusted-workspace regular files under the Permission & Control Plane, but practical coding also requires converting an approved worktree state into repository index state. Granting generic Git or shell execution would be a much larger authority boundary than staging itself.

## Decision candidate
Introduce a dedicated Hive-owned action `git_stage_paths_v1` whose only product effect is staging the exact current bytes of an explicitly approved bounded set of regular workspace files into the local repository index.

The request binds repository identity, exact HEAD state, exact index state, deterministic normalized path set and exact observed worktree metadata/digests. Raw worktree/index bytes are excluded from approval and audit metadata. A request-bound single-use permit is consumed only at the final safe mutation boundary after stale-state checks.

## Backend decision gate
The implementation must not expose arbitrary Git arguments and must not use shell execution. The preferred backend class is a maintained library with explicit local index transaction APIs and no process/network execution. If no dependency with acceptable provenance and semantics is available in the repository, adding one requires a governed dependency/provenance delta before implementation. A `git add` subprocess is not implicitly equivalent to a safe index primitive because repository configuration, attributes and filters can change behavior and can invoke external programs.

A bespoke index writer is also not automatically acceptable. It requires proof of Git index-format correctness, lock ownership, atomic publication semantics and cross-platform behavior.

## Supported v1 envelope
The selected workspace must itself be a non-bare repository root with a real local `.git` directory. Linked worktrees, submodules, nested repositories, pathspec/glob input, deleted-path staging, special files, executable filters, unsupported sparse/split/conflicted index states and unsafe repository indirection fail closed unless separately proven.

## Concurrency law
The index is shared mutable state. A foreign index lock is never deleted or stolen. Hive may clean only temporary/lock objects whose ownership it can prove. Approval is stale when HEAD, the approved index state or any approved worktree state changes before the latest safe revalidation.

No strict CAS claim is permitted unless the selected backend objectively predicates publication on the exact approved prior index state. Any residual race must be documented precisely before promotion.

## Platform law
Windows, Linux and macOS are independent evidence targets. A platform is not promoted merely because the same high-level library API exists there. Exact-head native tests must prove path safety, lock behavior, stale-state rejection, permit ordering and exact staged result on each supported platform.

## Non-decision
This ADR does not approve commit, ref/branch/tag mutation, checkout/reset/restore/clean/stash, merge/rebase/cherry-pick, remotes/network, credentials, hooks, external filters, generic process execution, terminal/shell authority, arbitrary `.git` filesystem writes or desktop/Tauri mutation authority.

## Promotion gate
DEC-027 remains PROPOSED until the backend/dependency decision is proven, executable contract/security tests pass natively on all three target OSes, exact-head CI is green and HEDS reports HIGH/CRITICAL `0/0`.