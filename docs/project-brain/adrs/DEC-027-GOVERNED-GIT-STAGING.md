# DEC-027 — Governed Git Staging Boundary

**Status:** PROPOSED — PROMOTION CANDIDATE PREPARED, NOT CANONICAL  
**Work Order:** `HCODER-WO-0023`  
**Issue:** `#68`  
**Original source main:** `22b56b0f3111158cbf50789b1647c5a578a171c1`  
**Promotion-preflight canonical main:** `aaa75242826db33442cd96cdc1d550d69bd25faa`  
**Last behavior-changing implementation head:** `b904b473416786e72c7e805e2e8c8b557d377166`  
**Independently reviewed promotion-candidate head:** `b827cb2eaa04eb2efa3ffb0b9aa7a82cbb7c672a`  
**Independent A4/HEDS review artifact:** PR review `5229345968`  
**Promotion candidate:** `.engineering/checkpoint-deltas/HCODER-WO-0023.md`

> **State transition record (explicit and evidence-bound).** This ADR remains **PROPOSED**. Its original source main is preserved above and is not backdated or erased. The promotion-candidate preparation records that every condition in the promotion gate below is now objectively satisfied at the independently reviewed head; the canonical status itself has **not** been declared, and cannot be until the governing review and promotion mutation occur. Nothing in this record may be read as a canonical decision.

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

**Condition status at the independently reviewed head `b827cb2eaa04eb2efa3ffb0b9aa7a82cbb7c672a` (evidence-bound):**

| Condition | Status | Evidence |
|---|---|---|
| Backend/dependency decision proven | MET | `foundations/python-dependencies.lock.json`, `foundations/python-dependencies.requirements.txt`, `tools/foundations/verify_python_dependencies.py`; pure-Python wheel hash-pinned; import isolation asserted |
| Executable contract/security tests pass natively on all three target OSes | MET | At the same reviewed head `b827cb2e`: Governance run `35161417857` with the native Linux, Windows HIGH_ASSURANCE and macOS governed Git staging lanes all SUCCESS, each independent of the others |
| Exact-head CI green | MET | At the reviewed head `b827cb2e`: Governance `35161417857` SUCCESS; Desktop Shell `35161417859` SUCCESS |
| HEDS HIGH/CRITICAL `0/0` | MET | Independent A4/HEDS review `5229345968` at `b827cb2e`: CRITICAL `0`, HIGH `0`. The executor's prepared audit additionally recorded MEDIUM `0`, LOW `3`; all three LOW were source-accuracy prose corrections carried in `b827cb2e` and documentation-only |

The gate is therefore satisfied as a **promotion candidate**. Declaring DEC-027 canonical remains the governing review's decision and is explicitly **not** done here.