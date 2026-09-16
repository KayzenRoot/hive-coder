# HCODER-WO-0023 — Governed Git Staging Capability

**Status:** PREBUILT / BACKEND GATE OPEN  
**Risk:** HIGH_ASSURANCE  
**Task class:** T3  
**Context radius:** C4  
**Canonical base:** `22b56b0f3111158cbf50789b1647c5a578a171c1`  
**Decision:** `DEC-027` PROPOSED  
**Issue:** `#68`

## Objective
Add the smallest repository mutation required after governed file editing: stage exact approved regular-file worktree content into the local Git index without granting generic Git, process or terminal authority.

## Frozen product surface
- contract: `hive-git-stage-v1`;
- action: `git_stage_paths_v1`;
- target state: `index_update`;
- maximum path count: 128;
- exact normalized deterministic path set;
- approval bound to repository identity, HEAD, index state and each worktree path state;
- no raw worktree/index bytes in approval/audit/receipt;
- permit mandatory, request-bound, short-lived and single-use;
- no arbitrary Git argv/command input.

## Current backend gate
Repository inspection found no existing governed Python Git library/manifest that can simply be reused. Therefore implementation must not silently add a dependency or fall back to a `git add` subprocess. Before executor-heavy implementation, choose one of these only with objective proof:
1. maintained local Git library with index transaction API, pinned provenance and no process/network behavior;
2. narrowly governed external Git process only through an explicit correction/authority decision proving filters/config/hooks/process semantics safe;
3. Hive-owned index writer only if index-format, locking and atomicity are proven cross-platform.

The preferred route is (1). Routes (2) and (3) are blocked until their additional proof burden is accepted.

## Acceptance law
Contract/security tests are prebuilt first. Promotion requires successful exact-path staging plus stale HEAD/index/worktree rejection, foreign-lock safety, traversal/.git/symlink/reparse rejection, permit lifecycle proof, redaction proof and independent Windows/Linux/macOS evidence.

## Preserved exclusions
No commit/ref/branch/tag mutation; no checkout/reset/restore/clean/stash; no merge/rebase/cherry-pick; no remote/network/credentials; no hooks/external executable filters; no generic shell/process/terminal; no arbitrary `.git` write authority; no desktop/Tauri mutation expansion.

## STOP CONDITION
If exact-path staging cannot be implemented without one of the excluded authorities or without a dependency/provenance expansion, stop at the backend gate and create the smallest explicit governed delta. Do not smuggle the broader authority into this WO.