# HCODER-WO-0023 Git Object Store Boundary

Status: PREBUILT / MUTATION AUTHORITY NOT APPROVED
Contract: `hive-git-blob-candidate-v1`
Initial object format: SHA-1 only

## Why this boundary exists

Useful Git staging of a modified or untracked regular file is not merely an index rewrite. The approved worktree bytes must first correspond to a Git blob object, and the candidate index must reference that exact object identity. Therefore WO-0023 must model object materialization and index publication as distinct governed mutations.

## Authority-Late pipeline

`approved worktree bytes -> pure blob candidate -> object-store preflight -> candidate index -> index.lock preparation -> exact repository/worktree revalidation -> dedicated git.write permit -> bounded object publication + index publication -> postcondition proof`

The pure blob candidate is intentionally executable-authority-free. It computes only:

- canonical Git blob SHA-1 OID;
- SHA-256 approval/audit digest;
- exact byte length;
- fixed contract/object-format identifiers.

Raw bytes MUST NOT enter approval metadata, audit records or receipts.

## Initial support envelope

The first useful staging slice MAY support only ordinary non-bare SHA-1 repositories whose object store is the repository-local `.git/objects` directory and whose approved targets are ordinary explicit regular files already accepted by the observer.

The first slice MUST fail closed for SHA-256 repositories until independently proven, alternates, shared object stores, promisor/partial-clone semantics, replace-object semantics that affect correctness, submodules/nested repositories, linked worktrees, executable filters, hooks, pathspec expansion, deleted-path staging, sparse/split index, unresolved conflicts and any need for generic shell/process authority.

## Future object publication requirements

Object publication is NOT implemented by this prebuilt increment. Before enabling it, the executor must prove:

1. object path is derived solely from the approved canonical OID and cannot escape the proven local object store;
2. canonical loose-object bytes are produced deterministically using Git object framing and zlib without invoking Git or any external process;
3. temporary object creation is no-follow, identity-owned, same-filesystem and collision-safe;
4. an already-existing object is accepted only after proving that it represents the exact approved object, never merely because the pathname exists;
5. publication cannot overwrite a conflicting foreign object;
6. cancellation/session/emergency state is checked at the final safe boundary;
7. a dedicated request-bound single-use `git.write` permit is consumed only after all non-authoritative proof work that can safely precede mutation;
8. index candidate references exactly the approved blob OIDs;
9. index publication remains Hive-owned and does not delegate authority to `GitFile.close()`, porcelain, subprocess Git, hooks or filters;
10. partial failure semantics are explicit. A newly-created unreachable blob may be tolerable only if documented and proven safe, while a falsely-successful index publication is not;
11. receipts contain OIDs/digests/paths/status only, never raw source bytes or credentials;
12. Windows, Linux and macOS receive independent native evidence.

## Transaction semantics

Git does not provide one atomic filesystem transaction covering loose object creation plus index replacement. Therefore WO-0023 MUST NOT claim global atomic staging. The intended safety contract is bounded multi-step publication:

- content-addressed blob publication first;
- exact revalidation before index publication;
- atomic index namespace replacement within the platform-proven boundary;
- postcondition verification;
- fail closed on ambiguity.

A crash after blob publication but before index publication may leave an unreachable content-addressed object. That state must not be reported as successful staging. Cleanup must never delete an object merely because this operation created it unless ownership and reachability semantics are independently proven.

## Dependency rule

Dulwich remains a provisional parser/serializer/object primitive candidate only. Hive retains authority over observation, envelope policy, locks, revalidation, permit consumption and publication. `porcelain.add()`, subprocess Git and implicit `GitFile.close()` publication remain forbidden for this slice.

## STOP CONDITION

Do not add `.git/objects` mutation or public `stage_paths` authority until object-store repository-locality, object-format detection, existing-object verification, publication ordering, permit binding and independent native evidence are represented by executable tests and exact-head HEDS approval.