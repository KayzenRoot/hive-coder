# HCODER-WO-0023 — Context Lock

**Status:** LOCKED FOR PREBUILT IMPLEMENTATION  
**Issue:** #68  
**Canonical execution base:** `22b56b0f3111158cbf50789b1647c5a578a171c1`  
**Current canonical main:** `ccfed1f960c80dc58e4f45cb627451e77c7d5a79`  
**Main delta after execution base:** evidence-only HCODER-PLATFORM-001 reconciliation; no WO-0023 authority change  
**Risk:** HIGH_ASSURANCE  
**Authority delta:** first repository-local Git index mutation only

## Context Lock Delta 001 — non-authority product input reconciliation
This delta does not expand runtime authority. It regularizes the already-created competitive capability matrix as a product/planning input and records that canonical `main` advanced after this WO branch was created.

The WO branch must not force-rewrite history merely to absorb the evidence-only PLATFORM-001 closeout. Before promotion, the PR must be reconciled with then-current canonical `main` using a provenance-preserving integration/rebase strategy supported by the repository workflow, followed by fresh exact-head gates. No previous exact-head result may be reused after that reconciliation.

The competitive capability matrix and harness benchmark are planning/benchmark inputs only. They cannot activate runtime permissions, dependencies, subprocess execution, network access or Git mutation.

## Context Lock Delta 002 — governance reconciliation and reviewed Python dependency mechanism
This delta records the Prompt 01 governance repair and the bounded Python dependency mechanism required to close the Dulwich backend/provenance gate. **It does not grant runtime Git mutation authority, does not enable a public `stage_paths` API, does not enable `git.write`, and does not enable object or index publication.** The prebuilt authority posture (`mutation_authority_enabled = False` everywhere, no permit path) is unchanged by this delta.

### Authorized additional files
This delta authorizes exactly these additional files, and nothing else:
- `AGENTS.md` (current-state prose only; historical facts preserved)
- `docs/project-brain/11-CHECKPOINT.md`
- `docs/project-brain/10-DECISIONS-LEDGER.md`
- `.engineering/prebuilt/HCODER-WO-0023-CODEX-100-HANDOFF.md`
- `.engineering/gef/GEF-REVIEW-PROTOCOL.md`
- `.engineering/prompts/REVIEW-PROMPT-TEMPLATE.md`
- `foundations/python-dependencies.lock.json` (new)
- `tools/foundations/verify_python_dependencies.py` (new)
- `.github/workflows/governance.yml` (dependency installation and exact native proof lanes only)
- `tests/runtime/test_git_stage_index_codec.py`
- `tests/runtime/test_git_stage_contract.py`
- `tests/runtime/test_git_object_private_prep.py` (new focused lane)
- `tests/runtime/test_git_binary_byte_fidelity.py` (new focused regression lane)
- `tests/runtime/test_git_stage_observer_revalidation.py` (new focused regression lane)
- `tests/runtime/test_git_stage_tree_cache_semantics.py` (new focused real-Git semantic lane)
- `foundations/python-dependencies.requirements.txt` (new, hash-pinned, CI-consumed)

### Recorded resolution 001 — DEC-025 status disagreement
`docs/project-brain/11-CHECKPOINT.md` (CP-0021, canonical) states `DEC-025` is APPROVED / CANONICAL. The `DEC-025` ADR header still reads APPROVED / FINAL CANDIDATE — NOT CANONICAL because it was last written at the WO-0021 product merge `ee2e01e99aaea89deb2754ba8295fe34d7744541` and was not updated by the CP-0021 source-of-truth reconciliation `9c2623f8b335cf29b63b5db5f43e694bfd77938e`.

Resolution: the canonical checkpoint `HCODER-CP-0021` (git-proven closeout main SHA `200540c2605ff4e5c32f54cd1c3be40dbd167520`) is authoritative for DEC-025's promoted status. This delta does **not** rewrite the DEC-025 ADR file; the stale ADR header is carried forward as recorded documentary drift.

### Recorded resolution 002 — Decisions Ledger coverage gap
`docs/project-brain/10-DECISIONS-LEDGER.md` was last updated at CP-0017 (`79e6eb6`) and stops at DEC-021, while ADR files for DEC-022 through DEC-027 already exist under `docs/project-brain/adrs/`. The reconciliation folds those already-evidenced decisions into the ledger verbatim from their ADR records, preserving existing IDs and chronology. No decision content is invented and no historical decision is rewritten.

### Recorded resolution 003 — handoff module-name mismatch
`HCODER-WO-0023-CODEX-100-HANDOFF.md` names `hive_runtime/git_stage_pre_authority.py`, which does not exist. Code evidence shows the pre-authority adapter seam is implemented by `GovernedGitStageAdapter` in `hive_runtime/git_stage.py`, with the pre-authority stage executor in `hive_runtime/git_stage_plan.py`. The stale reference is corrected in the handoff rather than creating a redundant module.

### Recorded resolution 004 — review deliverable policy
The rule that every completed review must deliver the next executable Codex prompt as a generated PDF is canonicalized in `.engineering/gef/GEF-REVIEW-PROTOCOL.md` and referenced from `.engineering/prompts/REVIEW-PROMPT-TEMPLATE.md`.

### Reviewed Python dependency mechanism
The repository had no canonical Python third-party dependency mechanism. This delta authorizes exactly one minimal mechanism: a hash-pinned `foundations/python-dependencies.lock.json` with a verifier `tools/foundations/verify_python_dependencies.py`, consumed by CI. It introduces no packaging redesign and no new runtime authority. At the time of this delta the only admitted entry is `dulwich==1.2.15` as an index **parser/serializer primitive**, pinned to the pure-Python wheel, with `urllib3` deliberately not materialized so the client/network path is structurally unavailable.

## Context Lock Delta 003 — same-WO correction: TREE cache-tree semantics
Review verdict on the Prompt 01 slice was CORRECTION REQUIRED. This delta records the correction. **It does not grant runtime Git mutation authority, does not enable `stage_paths`, does not enable `git.write`, and does not enable object or index publication.** The authority posture is unchanged.

### Corrected defect
The data-only codec captured the validated source index's raw extension region and appended it verbatim to the candidate. That is wrong for a mutated index. The `TREE` extension is a cache-tree: each node records tree object ids that describe portions of the **previous** index. Replacing a staged path invalidates every node covering it, but the node structure and entry counts remain consistent, so Git's cache-tree verification does not detect the staleness.

Reproduced objectively against a real repository: with the previous region carried forward, `git write-tree` on the candidate returned a tree whose `dir` subtree was byte-identical to `HEAD:dir`, silently committing the pre-change blob and discarding the staged modification, with **no error reported by Git**. Dropping the region made `write-tree` match the tree Git itself produces for the same change exactly.

### Corrected law
- A validated `TREE` extension is still **accepted when reading** a source index.
- The candidate **never** carries a source extension. This slice produces an empty extension region, always.
- Rebuilding a cache-tree is deliberately **not** implemented here; `TREE` is optional, so removal is the fail-safe rule.
- The accepted extension set is not broadened by this delta.
- `hive_runtime/git_index_envelope.py` no longer exposes the raw extension-region accessor. It existed only to enable the corrected behavior and would otherwise advertise extension passthrough as a supported pattern.

### Cleanup-hardening review (Prompt 02 §8)
`PrivateObjectPreparer.cleanup_private_temp` was re-audited. Outcome: the failure path no longer removes a pathname it cannot prove it owns, and the residual name-based deletion window is stated precisely in the docstring as a bounded race — the same posture CP-0022 records for its own replacement contract, rather than a race-free identity deletion claim. The Hive-owned temporary directory claim is also narrowed: mode 0700 applies only where the platform honours POSIX permission bits, and on Windows the effective control is the inherited ACL of `.git`.

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
- `.engineering/prebuilt/HCODER-COMPETITIVE-CAPABILITY-MATRIX-v1.md`
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
Non-authority-expanding harness frontier, benchmark and competitive capability specifications may be developed in this WO because they constrain how this and later executors receive context, prove actions and stop. They must not activate new runtime permissions inside WO-0023. Executable frontier mechanisms belong to explicit future Work Orders with independent evidence.

## Promotion reconciliation gate
Before HEDS FINAL / promotion:
- reconcile this branch with current canonical `main` without destructive history rewriting unless an explicit governed correction authorizes it;
- rerun Governance and Desktop Shell at the reconciled exact head;
- rerun all WO-0023 native proof lanes at that exact head;
- record the reconciled base/head and evidence in the WO ledger;
- do not represent evidence-only PLATFORM-001 history as part of the Git staging authority delta.

## STOP CONDITION
STOP and return to architecture/review if safe staging requires generic shell/process execution, Git hooks/external filters, remote/network access, credentials, arbitrary `.git` writes, unsupported repository indirection or weakening the Permission & Control Plane. No commit capability is included.