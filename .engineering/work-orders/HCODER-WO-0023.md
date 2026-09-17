# HCODER-WO-0023 — Governed Git Staging Capability

**Status:** COMPLETE / CANONICAL / SEALED — product PR #69, closeout PR #75 and final-seal PR #76 all merged and post-seal validated on exact `main`; Issue #68 CLOSED / COMPLETED  
**Delivered authority:** exactly one bounded action, `git_stage_paths_v1`, under `Capability.GIT_WRITE` (HIGH, mandatory approval, request-bound single-use permit)  
**Backend result:** route (1) selected — `dulwich==1.2.15`, pure-Python wheel, hash-pinned, provenance and import isolation closed  
**Native proof:** Windows, Linux and macOS governed Git staging lanes pass independently at exact head  
**Risk:** HIGH_ASSURANCE  
**Task class:** T3  
**Context radius:** C4  
**Canonical base:** `22b56b0f3111158cbf50789b1647c5a578a171c1`  
**Decision:** `DEC-027` — CANONICAL / SEALED under `HCODER-CP-0023`  
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

## Backend gate (HISTORICAL — as written at prebuild; resolution recorded below)
This section is preserved as the historical record of the gate that opened this Work Order. It is no longer current state.

Repository inspection found no existing governed Python Git library/manifest that can simply be reused. Therefore implementation must not silently add a dependency or fall back to a `git add` subprocess. Before executor-heavy implementation, choose one of these only with objective proof:
1. maintained local Git library with index transaction API, pinned provenance and no process/network behavior;
2. narrowly governed external Git process only through an explicit correction/authority decision proving filters/config/hooks/process semantics safe;
3. Hive-owned index writer only if index-format, locking and atomicity are proven cross-platform.

The preferred route is (1). Routes (2) and (3) are blocked until their additional proof burden is accepted.

**Resolution (recorded, not rewritten).** Route (1) was selected and closed under WO-0023 Context Lock Delta 002. `dulwich==1.2.15` is pinned to the exact pure-Python artifact by hash in `foundations/python-dependencies.lock.json`, with a non-installing verifier consumed by CI. Route (2) — a governed external Git process — was never taken, and no `git add` subprocess exists in the product. Route (3) — a Hive-owned index writer — was not needed. Correctness does not depend on the optional compiled extension, and the admitted module surface imports no `urllib3`, `socket` or `ssl`.

Implementation completed under Context Lock Deltas 004 (authority/publication), 005 (crash-safe publication and exact binding) and 006 (final-link freshness). Every prebuilt acceptance gate is activated; `PREBUILT:` skips remaining: 0.

## Acceptance law
Contract/security tests were prebuilt first. Promotion requires successful exact-path staging plus stale HEAD/index/worktree rejection, foreign-lock safety, traversal/.git/symlink/reparse rejection, permit lifecycle proof, redaction proof and independent Windows/Linux/macOS evidence.

**Status of that law:** all of the above is implemented and passing at the independently reviewed head `b827cb2e`, including independent native Windows, Linux and macOS governed staging lanes. Promotion has since completed: `DEC-027` is CANONICAL / SEALED, PR #69 merged, the closeout and final-seal PRs merged, and Issue #68 is CLOSED / COMPLETED.

## Preserved exclusions
No commit/ref/branch/tag mutation; no checkout/reset/restore/clean/stash; no merge/rebase/cherry-pick; no remote/network/credentials; no hooks/external executable filters; no generic shell/process/terminal; no arbitrary `.git` write authority; no desktop/Tauri mutation expansion.

## STOP CONDITION
If exact-path staging cannot be implemented without one of the excluded authorities or without a dependency/provenance expansion, stop at the backend gate and create the smallest explicit governed delta. Do not smuggle the broader authority into this WO.

That condition did not trigger: exact-path staging was implemented within the excluded-authority boundaries, and no broader authority was smuggled in. The preserved exclusions below still hold at the approved head.

**Approval state (historical phase).** At the approval-state phase this Work Order was APPROVED / READY FOR MERGE on its branch and not yet merged. That phase has been superseded: the product, closeout and final-seal merges are complete, `HCODER-CP-0023` is SEALED / CANONICAL, and Issue #68 is CLOSED / COMPLETED. The frozen execution law below still holds for any future Work Order. Historical backend-gate and correction chronology above is preserved and is not rewritten.