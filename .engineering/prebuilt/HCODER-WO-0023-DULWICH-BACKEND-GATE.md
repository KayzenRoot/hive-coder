# HCODER-WO-0023 — Dulwich Backend Gate

Status: PREBUILT / NOT APPROVED FOR RUNTIME
Candidate: Dulwich 1.2.15
Contract: hive-git-index-codec-v1

## Purpose

Use Dulwich only as a bounded Git object/index parser-serializer behind a Hive-owned adapter. Dulwich is not an authority provider and must not own publication, permits, process execution, hooks, filters, remotes, network, credentials, or generic porcelain behavior.

## Required proof before backend enablement

1. Dependency provenance
   - Pin an exact reviewed version and hash/lock metadata in the repository's governed Python dependency strategy.
   - Record license compatibility and transitive dependency surface.
   - No silent optional native/Rust extension requirement for correctness.

2. Supported index envelope
   - Ordinary non-bare repository only.
   - Index versions accepted only after fixture proof.
   - Regular explicit files only.
   - Reject unresolved conflict stages.
   - Reject sparse index / sparse-directory semantics.
   - Reject split index / link extension.
   - Reject unknown mandatory extensions or any extension whose preservation semantics are not proven.
   - Preserve safe optional extensions only when byte/semantic round-trip is proven.

3. Pure codec boundary
   - No `porcelain.add()`.
   - No subprocess or Git executable.
   - No hook execution.
   - No executable clean/smudge/process filters.
   - No remote/network/client operations.
   - No credential/config discovery that expands authority.
   - No `GitFile.close()` or other library-owned publication to `.git/index`.

4. Candidate construction
   - Input must bind the exact observed source index SHA-256 and deterministic explicit path list.
   - Candidate bytes are returned as data only.
   - Candidate bytes are written only to Hive-owned `index.lock` transaction.
   - Candidate digest/length are verified before any permit can be consumed.

5. Authority-late publication
   - Revalidate repository HEAD, index identity/digest and worktree state immediately before mutation-ready boundary.
   - Dedicated `git.write` capability and fixed action `git_stage_paths_v1` required.
   - Request-bound, short-lived, single-use permit consumed at the final safe boundary.
   - Hive-owned publication only after cancellation/takeover/emergency checks.
   - Post-publication verification and redacted receipt required.

6. Native proof
   - Linux, macOS and Windows independently non-skipped.
   - Lock collision/foreign lock preservation.
   - Crash/failure cleanup.
   - Atomic publication behavior for supported filesystem envelope.
   - No platform inferred from another platform's result.

## Promotion blockers

Any of the following keeps the backend disabled:

- missing governed dependency pin;
- generic porcelain or subprocess Git;
- executable hook/filter path reachable;
- remote/network/credential path reachable;
- library-owned `.git/index` publication;
- sparse/split/conflicted index accepted without proof;
- stale-state revalidation absent;
- dedicated `git.write` authority absent;
- Windows/Linux/macOS native evidence incomplete;
- HIGH or CRITICAL HEDS finding.

## STOP CONDITION

Do not instantiate `DulwichIndexCodecCandidate` and do not expose a public staging mutation until every promotion blocker above is objectively closed by tests/evidence and HEDS approves the exact head.
