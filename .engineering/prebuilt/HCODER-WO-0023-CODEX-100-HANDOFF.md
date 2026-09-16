# HCODER-WO-0023 CODEX 100% HANDOFF

Status: READY FOR CODEX AFTER EXACT-HEAD CI GREEN
Mode: HIGH_ASSURANCE / implementation completion

## Start here

Read, in order:
1. `.engineering/checkpoints/HCODER-PRE-CODEX-100.md`
2. `.engineering/context-locks/HCODER-WO-0023.md`
3. `.engineering/work-orders/HCODER-WO-0023.md`
4. `.engineering/prebuilt/HCODER-WO-0023-IMPLEMENTATION-PACK.md`
5. `.engineering/prebuilt/HCODER-WO-0023-DULWICH-BACKEND-GATE.md`
6. `.engineering/prebuilt/HCODER-WO-0023-GIT-OBJECT-STORE-BOUNDARY.md`
7. `docs/project-brain/adrs/DEC-027-GOVERNED-GIT-STAGING.md`
8. existing `hive_runtime/git_*` modules and `tests/runtime/test_git_*` tests.

## Objective

Complete the already-designed `git_stage_paths_v1` capability without redesigning the authority model. The implementation must stage explicit regular worktree files in the supported ordinary local SHA-1 repository envelope, using Hive-owned authority-late publication and no generic Git subprocess.

## Mandatory implementation order

A. Close codec provenance/backend gate. Pin/prove backend and license/transitives. Use parser/serializer primitives only. Never use porcelain.add, GitFile.close auto-publication, hooks, filters, subprocess, network or credentials.

B. Complete object preparation. Use existing candidate/store/loose-object boundaries. Private temporary objects must be identity-owned, no-follow, bounded, repository-local and safe to abandon. Existing objects must prove exact canonical blob identity.

C. Build exact index candidate from observed index + explicit stage plan. Reject unsupported index envelopes/features. Candidate must be data-only and bind source index digest, deterministic paths and resulting bytes/digest.

D. Extend the action request only through an explicit Context Lock Correction/Delta so approval binds the exact repository/index/worktree state, path set, blob OIDs/content digests and candidate index digest. Raw worktree/index/object bytes must never enter approval/audit metadata.

E. Add dedicated `Capability.GIT_WRITE = "git.write"` and policy only through the approved control-plane change. It is HIGH_ASSURANCE. Model/tool/backend cannot mint permits. Never reuse SHELL_EXECUTE or generic FILESYSTEM_WRITE as Git authority.

F. Final safe boundary: exact observer revalidation -> object-store revalidation -> private object/index readiness -> cancellation/session/emergency checks -> request-bound single-use permit consumption -> bounded publication.

G. Publication order: content-addressed blob(s) first, then atomic index publication. A crash after a new blob but before index publication may leave an unreachable content-addressed blob but MUST NOT report success. Never delete an object unless ownership/reachability is independently proven.

H. Postconditions: exact index digest, staged paths/OIDs, repository identity, no unrelated path change, redacted receipt/audit. Failure is never success.

I. Native proof on Windows, Linux and macOS. Include ordinary modified/untracked file staging, exact index result, stale HEAD/index/worktree/object-store rejection, symlink/reparse/nested repo rejection, unsupported config/index envelope, cancellation/takeover/expiry/emergency stop, permit replay/wrong request, no shell/hooks/filters/network/credentials, crash/failure semantics.

J. Evidence Ledger + HEDS exact head. HIGH/CRITICAL must be 0/0 before PR #69 leaves Draft or merges.

## Allowed-first file set

Prefer completing existing files rather than creating parallel architecture:
- `hive_runtime/git_stage.py`
- `hive_runtime/git_stage_contract.py`
- `hive_runtime/git_stage_observer.py`
- `hive_runtime/git_stage_transaction.py`
- `hive_runtime/git_stage_index_codec.py`
- `hive_runtime/git_index_envelope.py`
- `hive_runtime/git_object_candidate.py`
- `hive_runtime/git_object_store_inspector.py`
- `hive_runtime/git_loose_object_transaction.py`
- `hive_runtime/git_stage_plan.py`
- `hive_runtime/git_object_private_prep.py`
- `hive_runtime/git_stage_codex_frontier.py`
- corresponding `tests/runtime/test_git_*`
- control-plane files only after explicit Context Lock authority delta.

> **Prompt 01 correction (WO-0023 Context Lock Delta 002).** This list previously named `hive_runtime/git_stage_pre_authority.py`. That module does not exist and never did. Code evidence shows the pre-authority seams are already implemented in existing modules: `GovernedGitStageAdapter` in `hive_runtime/git_stage.py`, `PreAuthorityStageExecutor` in `hive_runtime/git_stage_plan.py`, and `PreAuthorityLooseObjectTransaction` in `hive_runtime/git_loose_object_transaction.py`. The stale reference was corrected rather than creating a redundant parallel module. Do not create `git_stage_pre_authority.py`.

## Forbidden shortcuts

No `git add` subprocess. No shell command fallback. No arbitrary `.git` writer. No hook/filter execution. No credentials/remotes/network. No silent support for linked worktrees, submodules, nested repos, bare, sparse/split index, conflicts, alternates/shared object DB, promisor/partial clone, SHA-256 repo, deleted-path staging or unproven extensions. No weakening tests to obtain green CI.

## Definition of Done for Codex execution

Implementation is complete only when the supported explicit-path staging operation works through the dedicated permission plane on all three OSes, all adversarial tests are active, exact-head Governance/Desktop/native evidence is green, Evidence Ledger is complete, HEDS says APPROVED with HIGH=0 and CRITICAL=0, and PR #69 is eligible for governed promotion.

## STOP

If completing any step requires generic shell/process authority, hooks/filters, network/credentials, arbitrary `.git` writes, weakening the Permission & Control Plane, or silently broadening repository support, STOP and create a same-WO Correction Delta instead.
