# HCODER-WO-0023 Codex 95% Handoff

Status: PREBUILT FRONTIER / AUTHORITY DISABLED
WO: HCODER-WO-0023
Action: `git_stage_paths_v1`
Target preparation maturity: 95%

## What is already decided and scaffolded

The executor MUST complete the existing Hive-owned surfaces rather than redesigning staging:

1. `git_stage_contract.py`: stable request/receipt metadata contract.
2. `git_stage.py`: adapter boundary; no public mutation until control-plane delta.
3. `git_stage_observer.py`: read-only repository/HEAD/index/worktree observation, stale revalidation, nested Git rejection.
4. `git_index_envelope.py`: v2/v3 safety firewall.
5. `git_stage_index_codec.py`: reviewed codec boundary; Dulwich remains candidate only.
6. `git_stage_transaction.py`: private `index.lock` preparation and ownership-safe cleanup; publication disabled.
7. `git_object_candidate.py`: pure canonical blob identity.
8. `git_object_store_inspector.py`: repository-local SHA-1 object-store envelope.
9. `git_loose_object_transaction.py`: deterministic compression and exact existing-object verification; publication disabled.
10. `git_object_private_prep.py`: private-object plan; materialization/publication disabled pending native proof.
11. `git_stage_plan.py`: one-to-one binding from approved worktree state to exact blob OID; publication disabled.

## Codex completion order

A. Close parser/backend gate. Pin reviewed Dulwich version/provenance and use only controlled index parse/serialize primitives. Never use porcelain, subprocess, hooks, filters, network or implicit publication.

B. Implement native private loose-object materialization behind `PrivateObjectPreparer.materialize_private_temp`. Use no-follow, exclusive creation, same-store identity proof, bounded writes, fsync where required, exact digest verification and ownership-safe cleanup. Do not publish yet.

C. Implement existing-object race revalidation and content-addressed publication. Existing exact object is success/no-op. Foreign/conflicting/unsafe object fails closed. New object publication cannot overwrite a foreign object. Crash after blob publication but before index publication is NOT staging success.

D. Complete index codec candidate generation. Candidate index must reference exactly the OIDs in `GitStagePlan`; reject unsupported index versions/extensions/conflicts/sparse/split semantics.

E. Prepare `index.lock`, verify candidate digest/identity, then perform final observer + object-store + object candidate revalidation.

F. Only then introduce the explicit Permission & Control Plane Context Lock delta for dedicated `Capability.GIT_WRITE`. Do not reuse `SHELL_EXECUTE`. Request must bind repository identity, HEAD, previous index identity/digest, exact paths/worktree identities/digests/lengths, exact blob OIDs and candidate index digest. Raw bytes never enter approval/audit.

G. Consume request-bound single-use permit at the final safe boundary. Recheck cancellation/takeover/expiry/emergency state. Publish required content-addressed blobs, revalidate, atomically publish index with platform-proven primitive, verify postconditions, emit redacted receipt.

H. Native evidence: independent Windows, Linux and macOS tests. No platform may inherit another platform's proof.

## Remaining mandatory executable proofs

- private object temp no-follow/exclusive/identity-owned cleanup;
- existing object races and collision behavior;
- object publication interruption semantics;
- real codec roundtrip and rejection corpus;
- index candidate exact OID/path/mode binding;
- dedicated `git.write` permit single-use/request binding;
- cancellation/takeover/expiry/emergency stop at final boundary;
- zero shell/process/hook/filter/network/credential authority;
- redacted request/audit/receipt;
- native Windows/Linux/macOS staging E2E;
- exact-head HEDS H/C = 0.

## Non-goals that remain frozen

No commit, branch, tag, reset, checkout, clean, delete-path staging, arbitrary `.git` write, generic shell/process, remote/network mutation, credentials, linked worktrees, submodules, sparse/split index, partial/promisor clone, alternates/shared object stores or SHA-256 repository support in this first slice.

## STOP CONDITION

Do not expose public `stage_paths`, enable `mutation_authority_enabled`, instantiate a real publishing backend, or call WO-0023 complete until the dedicated control-plane authority delta and all mandatory executable/native proofs are green at the same exact head and HEDS reports HIGH=0 / CRITICAL=0.
