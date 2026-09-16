# HCODER-WO-0023 — Evidence Ledger

**Status:** AUTHORITY SLICE IMPLEMENTED / NATIVE E2E PROVEN / PROMOTION PENDING REVIEW  
**Canonical base:** `22b56b0f3111158cbf50789b1647c5a578a171c1`  
**Canonical main at execution:** `ccfed1f960c80dc58e4f45cb627451e77c7d5a79`  
**Issue:** `#68`  
**Draft PR:** `#69`

## Claims allowed now

- Current desktop Git observation is read-only and does not execute Git.
- Canonical workspace create/replace capabilities provide the control-plane pattern this WO preserves.
- The reviewed codec backend provenance gate is **closed**: `dulwich==1.2.15` is pinned to the exact pure-Python wheel by hash, and the resolver/verifier are committed and consumed by CI.
- A data-only index candidate can be built from an approved observation plus an authority-free stage plan, and the produced bytes are accepted by Git as a correct index.
- **`Capability.GIT_WRITE` / `git_stage_paths_v1` is implemented and reachable only through the Permission & Control Plane**, with mandatory trusted approval and a request-bound single-use permit consumed at the final safe boundary.
- **Blob publication into the repository-local `.git/objects` store and atomic `.git/index` publication are implemented** and proven by a real-Git end-to-end lane on Windows, Linux and macOS independently.

## Claims explicitly NOT allowed yet

- Any Git mutation is safe or production-ready in general.
- `git.write` is canonical (DEC-027 remains PROPOSED until the promotion gates pass).
- Strict CAS of index/worktree state exists.
- Any capability beyond `git_stage_paths_v1` exists: no commit, tag, ref, branch, remote, credential, generic Git argv or shell surface.
- Staged content is committed. This slice updates the index only.

## Backend provenance record

| Field | Value |
|---|---|
| Backend | `dulwich` `1.2.15` |
| License | `Apache-2.0 OR GPL-2.0-or-later` (Apache-2.0 selected) |
| Admitted artifact | `dulwich-1.2.15-py3-none-any.whl` |
| Artifact sha256 | `5c863992962bab0fc5f75be132399a16f670f2a9283faf9aaeb953fd8891db83` |
| Excluded artifacts | all platform wheels; sdist (may compile optional extensions) |
| Native extension needed | **no** — verified: `dulwich._objects` is absent under the admitted wheel |
| Declared transitives | `urllib3>=2.2.2` (not materialized by design); `typing_extensions` only for Python < 3.12 |
| Lock | `foundations/python-dependencies.lock.json` |
| Pin file | `foundations/python-dependencies.requirements.txt` |
| Verifier | `tools/foundations/verify_python_dependencies.py` (non-installing, fails closed) |
| CI consumption | `governance.yml` source-pack + all three native lanes install the pin file with `--no-deps --require-hashes`, then run the verifier |

Import isolation is asserted by test, not assumed: importing and using `dulwich.index` introduces 83 modules including stdlib `urllib.parse`, but **no** `urllib3`, `socket` or `ssl`. The codec module is additionally AST-checked so it cannot reach `subprocess`, `socket`, `ssl`, `urllib`, `urllib3`, `requests`, porcelain, `GitFile` or a generic `Repo`.

Dulwich is a parser/serializer primitive only. Hive owns index version policy, conflict and extension policy, entry ordering, the SHA-1 trailer, and the rule that **no source extension is propagated into a mutated candidate**. Dulwich neither preserves the `TREE` extension through its serializer nor writes the index trailer, and its inability to preserve `TREE` turns out to be the correct behavior for this slice.

## Extension policy after the Prompt 02 correction

The Prompt 01 slice carried the validated source extension region into the candidate verbatim. Review held that to be a blocking defect, and the defect was then reproduced objectively:

- Source index carries a real `TREE` cache-tree.
- A tracked file under that cache is modified and the Hive candidate is built with the previous region carried forward.
- `git write-tree` on that candidate returns a tree whose `dir` subtree is **byte-identical to `HEAD:dir`** — it reuses the pre-change blob and silently discards the staged modification, with **no error from Git**.
- The same candidate built with the region dropped matches the tree Git itself produces for the identical change, exactly.

Root cause: a cache-tree node records tree object ids describing portions of the previous index. Replacing a staged path invalidates every node covering it, but node structure and entry counts stay consistent, so Git's cache-tree verification does not detect the staleness and `write-tree` reuses the cached subtree.

Corrected law: a validated `TREE` extension is accepted when **reading** a source index, and the candidate **always** carries an empty extension region. Rebuilding a cache-tree is deliberately out of scope; `TREE` is optional, so removal is the fail-safe rule. The accepted extension set was not broadened. `hive_runtime/git_index_envelope.py` no longer exposes the raw extension-region accessor, since it existed only to enable the corrected behavior.

Semantic proof: `tests/runtime/test_git_stage_tree_cache_semantics.py`, which compares the produced tree against Git's own staging result for both a modified tracked file and an added untracked file, and additionally constructs a deliberately stale-TREE-carrying candidate to prove the lane fails if the regression returns.

## Implementation slice 01 — exact head

**Implementation head:** `9ac5ad43742376245da09de48ce812a7f7678d2e`  
**Verified head:** `19c8c1abdd960196b1e9b8bb52ebba90843a77a3` (adds the observation-idempotence fix below)  
**Correction head:** `ceb6cda42c3a6b3864b39a75afb27fb1982053ba` (Prompt 02 same-WO correction: TREE cache-tree semantics, main reconciliation, cleanup-hardening review)  
**Authority head:** `52d8cc3195bd4f9c948b1327ed124042739b2530` (Prompt 03: dedicated `git.write` authority, publication and native E2E)

## CR-05 correction candidate (Prompt 05)

**Status:** CORRECTION_CANDIDATE_READY_FOR_HEDS. Not APPROVED, not READY, not COMPLETE.

GEF V1 universal was adopted on `main` during this correction. The real main delta (`ccfed1f..aaa7524`) touched only GEF governance, templates, the PR template and `AGENTS.md`; it touched no WO-0023 runtime, contract, publisher, permit-boundary or test file, so the frozen authority model is unaffected. `origin/main` was integrated with a provenance-preserving merge commit and no history rewrite. Two conflicts (`AGENTS.md`, `GEF-REVIEW-PROTOCOL.md`) were resolved by the local source hierarchy: GEF V1 adoption content and the prompt-01 review-deliverable law are both preserved, and neither side's governance was deleted.

### CR-05-A — final-link freshness
`LooseObjectPublisher.publish()` now takes an optional Hive-owned `pre_publish_check` invoked after every preparation/revalidation step and immediately before `os.link`. `stage_paths()` supplies a closure that re-checks session ACTIVE; the external pre/post checks per blob remain, and permit consumption is not moved into the publisher.

Deterministic integrated proof (`FinalLinkFreshnessTests`), using the real request -> approval -> permit -> `stage_paths` flow: the session is transitioned at the genuine fanout helper, i.e. after the private temporary is materialized and re-proved and before the atomic promotion. Coverage: cancel, takeover, session expiry, session-scoped emergency stop, global emergency stop, and a multi-file case where one blob is already canonical. In every case the affected canonical OID pathnames stay absent, `.git/index` is byte-identical, no success receipt is produced, and no `index.lock` remains. No sleep is used and no test-only hook exists in production code.

### CR-05-B — approval-confusion proof
The test now builds the contradictory request **before** any challenge, then runs the real challenge -> trusted approval -> authorize flow against that contradictory request, so the rejection can only come from the executor's semantic path-equality validation rather than a fingerprint mismatch. It proves zero object/index mutation, zero residual lock, and that the permit was **not** consumed — verified by successfully consuming it afterwards through the canonical `consume_execution_permit` API, with no new introspection surface.

### Local assurance (A0-A2)

| Step | Command | Exit | Seconds | Result |
|---|---|---|---|---|
| A0 | `python -m compileall -q hive_runtime tests/runtime` | 0 | 0.27 | PASS |
| A1 focused | `python -m unittest discover -s tests/runtime -p "test_git_stage_authority.py"` | 0 | 16.3 | PASS, 48 tests |
| A1/A2 impacted | `python -m unittest discover -s tests/runtime -p "test_git_stage_security.py"` | 0 | 3.36 | PASS, 21 tests (13 platform/capability skips) |

`test_git_stage_security.py` required no edit; its lane already covers the properties and the new proof is not duplicated.

### Exact-head CI at `411c9facb6649315e85072f43dd53438250bdc02` (Prompt 04 correction head)

| Workflow | Run | Result |
|---|---|---|
| Governance | `35147086747` | **SUCCESS** |
| Desktop Shell | `35147086909` | **SUCCESS** |

Governance jobs: `source-pack` SUCCESS, `governed-runtime-linux` SUCCESS, `control-plane-windows` SUCCESS, `workspace-replace-macos` SUCCESS.

Native governed Git staging proof, executed independently per platform on the corrected publication primitive:
- `Native Linux governed Git staging proof (codec, object, authority, E2E)`: **SUCCESS**
- `Native Windows HIGH_ASSURANCE governed Git staging proof (codec, object, authority, E2E)`: **SUCCESS**
- `Native macOS governed Git staging proof (codec, object, authority, E2E)`: **SUCCESS**

Desktop Shell jobs: `desktop-web`, `desktop-windows`, `desktop-linux`, `desktop-macos` — all SUCCESS.

At this head: 527 tests OK, 53 skipped (1 capability-gated symlink fixture plus pre-existing POSIX-primitive fixtures, each with a Windows-native counterpart). `PREBUILT:` skips remaining: 0.

### Exact-head CI at `52d8cc3195bd4f9c948b1327ed124042739b2530`

| Workflow | Run | Result |
|---|---|---|
| Governance | `35143445682` | **SUCCESS** |
| Desktop Shell | `35143445758` | **SUCCESS** |

Governance jobs: `source-pack` SUCCESS, `governed-runtime-linux` SUCCESS, `control-plane-windows` SUCCESS, `workspace-replace-macos` SUCCESS.

Native governed Git staging proof, executed independently per platform:
- `Native Linux governed Git staging proof (codec, object, authority, E2E)`: **SUCCESS**
- `Native Windows HIGH_ASSURANCE governed Git staging proof (codec, object, authority, E2E)`: **SUCCESS**
- `Native macOS governed Git staging proof (codec, object, authority, E2E)`: **SUCCESS**

Desktop Shell jobs: `desktop-web`, `desktop-windows`, `desktop-linux`, `desktop-macos` — all SUCCESS.

Platform-specific regression found and fixed at this head: a POSIX-gated pre-authority gate still asserted that `publish()` was unavailable, so it failed on Linux, macOS and source-pack while the local Windows run skipped it. That gate was updated to assert the real fail-closed and atomic-publication semantics, and equivalent coverage was added to the platform-neutral authority lane so that class of hidden regression cannot recur.

## Authority slice — dedicated git.write capability and publication

Granted by **WO-0023 Context Lock Delta 004**, bounded to exactly `git_stage_paths_v1` for explicit regular files in the already-proven ordinary local SHA-1 repository envelope.

### Control plane
- `Capability.GIT_WRITE = "git.write"` added, risk **HIGH**, materially sensitive, **mandatory approval**, required target field `workspace`.
- Exactly one allowlisted action: `git_stage_paths_v1`. `FILESYSTEM_WRITE` and `SHELL_EXECUTE` are not reused and cannot satisfy a `git.write` rule.
- Trusted UI resolution remains the only approval route; the capability mints no approval and no permit.

### Frozen request binding
The approval fingerprint commits to 17 exact argument keys, with no raw-byte representation anywhere: contract, repository identity, repository HEAD, index state/identity/source digest, path count, paths, canonical worktree states, deterministic per-path bindings (path, content SHA-256, byte length, resulting blob OID), candidate index SHA-256 and byte length, object-store contract/format/git-dir identity/store identity, and `target_state=index_update`.

### Preparation before authority
Normalize paths, observe repository/HEAD/index/worktree, prepare each blob candidate and OID, inspect the object store, build the authority-free stage plan, and build the extension-free candidate index with Dulwich primitives only. All of this happens in `prepare_stage_request`, which mutates nothing.

**Deliberate design decision worth review:** the capability does *not* hold `.git/index.lock` across the approval window. Holding the index lock while waiting for human approval would block the user's own Git operations and manufacture a stale lock that this Work Order forbids removing. The lock is therefore acquired inside `stage_paths`, and its identity and exact candidate digest are verified before the permit is consumed — the ordering the prompt requires is preserved, but the lock is never held while an unbounded human decision is pending.

### Final safe boundary (ordering proven by tests, not comments)
1. validate request shape and exact prepared metadata; 2. late observer revalidation of HEAD, source index and worktree; 3. late object-store revalidation; rebuild the plan and candidate from live bytes and prove they reproduce the approved bindings exactly; 4. acquire the owned `index.lock`, write the candidate, verify digest/length and lock identity; 5. session ACTIVE check; 6. **consume the request-bound single-use permit**; 7. session ACTIVE check again; 8. publish content-addressed blobs; 9. session and state recheck; 10. atomic index publication; 11. postconditions; 12. receipt only after verification.

### Publication law (as corrected by Prompt 04)
- **A canonical OID pathname is never opened for writing.** The complete compressed object is materialized and digest-verified in Hive-owned private storage outside `.git/objects`, then promoted with an atomic create-if-absent primitive (`os.link`, no-clobber on POSIX and on Windows/NTFS). `os.replace` is never used for objects because it would overwrite.
- A crash, kill or power loss at any point before promotion leaves the canonical pathname **absent**. It can never hold partial bytes.
- An existing object is accepted only after proving it is the exact approved blob; it is never overwritten and never deleted. Fanout directories are created only with bounded identity checks and fail closed on symlink/reparse/non-directory collisions.
- The private temporary is removed only under identity-safe cleanup, and the mode is left at the owner-only creation mode because a read-only file cannot be unlinked on Windows.
- The index is published only by the capability-owned `index.lock` transaction. A foreign or pre-existing lock fails closed and is never removed.
- A crash after blob publication but before index publication may leave an unreachable content-addressed blob. That is the documented, accepted outcome; it is never reported as success and the blob is not rolled back.

### Request-binding law (as corrected by Prompt 04)
`paths`, the observed worktree paths and the path-binding paths must be **identical** after canonical normalization, in the same deterministic order, and `path_count` must equal all three lengths. A contradiction is a malformed request and is rejected before any permit consumption or mutation; it is never silently canonicalized.

### Mid-publication authority (as corrected by Prompt 04)
The session is re-checked immediately **before and after each** final object promotion, in addition to the existing check before index publication. A cancellation, takeover, expiry or emergency transition after one blob is published prevents every later publication and prevents index publication, while the already-published blob is left in place and never rolled back.

### Windows platform finding
`os.replace` fails with `WinError 32` while a handle to the source file is still open, so the owned lock handle is released immediately before the atomic replacement, with the lock identity re-proved on the pathname in between. Publication remains a single atomic same-filesystem replacement; ownership cannot be lost silently because a changed identity aborts before the call.

### Residual bounded-race claim
Consistent with CP-0022, this slice claims an atomic **publication**, not strict CAS. An uncooperative external process may act between the last successful revalidation and the atomic call. This is stated here and must never be represented as strict CAS.

### Public API and receipt
`prepare_stage_request` and `stage_paths` are separable so approval occurs over stable bounded metadata. `stage_paths` is exact-path only; pathspecs, globs and generic argv are rejected by the pre-existing normalizer. `GitStageReceipt` reports workspace, repository identity/HEAD, previous and committed index SHA-256, deterministic staged paths and `committed_state=index_updated`. Approval display, audit and receipt contain no raw worktree bytes, raw index bytes, compressed object bytes, credentials or permit tokens.

### Exact-head CI at `ceb6cda42c3a6b3864b39a75afb27fb1982053ba`

| Workflow | Run | Result |
|---|---|---|
| Governance | `35139273213` | **SUCCESS** |
| Desktop Shell | `35139273260` | **SUCCESS** |

Governance jobs: `source-pack` SUCCESS, `governed-runtime-linux` SUCCESS, `control-plane-windows` SUCCESS, `workspace-replace-macos` SUCCESS. The `Native <platform> governed Git index codec/object proof` step now includes the real-Git TREE cache-tree semantic lane on all three platforms.

Desktop Shell jobs: `desktop-web`, `desktop-windows`, `desktop-linux`, `desktop-macos` — all SUCCESS.

### Exact-head CI at `19c8c1abdd960196b1e9b8bb52ebba90843a77a3`

| Workflow | Run | Result |
|---|---|---|
| Governance | `35136454078` | **SUCCESS** |
| Desktop Shell | `35136454102` | **SUCCESS** |

Governance jobs: `source-pack` SUCCESS, `governed-runtime-linux` SUCCESS, `control-plane-windows` SUCCESS, `workspace-replace-macos` SUCCESS — including the new `Install governed Python dependencies` and `Verify governed Python dependency lock` steps, and the new native Git index codec/object lanes on all three platforms.

Desktop Shell jobs: `desktop-web`, `desktop-windows`, `desktop-linux`, `desktop-macos` — all SUCCESS.

Delivered in this head:

1. **Governance reconciliation** (WO-0023 Context Lock Delta 002) — checkpoint, AGENTS.md and Decisions Ledger reconciled to the Git-proven CP-0022 state; DEC-025 ADR status disagreement recorded as drift; CODEX-100 handoff module reference corrected; review-deliverable law canonicalized.
2. **Governed dependency mechanism** — see the provenance table above.
3. **Data-only index codec** (`hive_runtime/git_stage_index_codec.py`) — `DulwichGitIndexCodec` returns candidate bytes plus derived digest/length only. No `.git/index` write, no `.git/index.lock`, no object-store access, no permit, no publication.
4. **Envelope policy** (`hive_runtime/git_index_envelope.py`) — validates the DIRC envelope, entry framing, checksum, version and extension set. A validated source `TREE` extension is accepted on read and is never propagated into a candidate.
5. **Exact stat binding** (`hive_runtime/git_stage_contract.py`, `git_stage_observer.py`) — `GitStageWorktreeStat` carries the numeric stat record a Git index entry requires, so the codec never has to guess it. The codec fails closed when it is absent.
6. **Private object preparation** (`hive_runtime/git_object_private_prep.py`) — owned, bounded, no-follow temporary materialization inside `.git/hive-object-tmp`, with identity-verified cleanup. Publication still raises.

## Observation-idempotence defect found and fixed

An earlier revision of this head captured file **access time** into the approved worktree state. Observing a file reads it, which updates access time, so `revalidate()` reported an unchanged repository as stale — the exact check that exists to prove nothing changed. Linux and macOS failed `observe -> revalidate` immediately; Windows still passed, because its access-time handling hid the defect.

Git index entries record ctime, mtime, dev, ino, mode, uid, gid and size but never access time, so the field was removed from `GitStageWorktreeStat` rather than merely excluded from comparison. Regression lane: `tests/runtime/test_git_stage_observer_revalidation.py`, which runs on all three platforms and includes a positive control proving real HEAD, index, worktree and same-size content changes are still detected.

Local Windows verification could not reproduce this defect, which is why the regression lane is explicitly cross-platform.

## Windows binary-fidelity defect found and fixed

The WO-0023 Git modules opened files with `os.open` **without** `O_BINARY`. On Windows the CRT then uses text mode, where `os.read` stops at the first `0x1A` (Ctrl-Z) byte and `os.write` translates every `LF` to `CRLF`. A real Git index contains `0x1A` routinely, because entry and extension data include binary SHA-1 bytes.

Observed impact before the fix: the index digest was computed over 209 of 237 bytes, so the approved index digest could not match the approved bytes and the codec correctly failed closed; worktree digests and prepared index bytes were exposed to the same class of defect.

Fixed in `git_stage_observer.py`, `git_loose_object_transaction.py`, `git_object_store_inspector.py` and `git_stage_transaction.py`, matching the pattern already present in `repository_intelligence.py`. Regression lane: `tests/runtime/test_git_binary_byte_fidelity.py`.

## Local verification at the exact head

| Check | Result |
|---|---|
| `verify_lock.py` | PASS (`FOUNDATIONS_LOCK_OK`) |
| `doctor.py --inventory-only` | PASS (`LOCKED`, side effects NONE) |
| `verify_python_dependencies.py` | PASS (`LOCKED`, wheel tag `py3-none-any`) |
| `compileall hive_runtime tools` | PASS |
| Full Python suite | PASS — **506 tests**, `OK`, 53 skipped (1 capability-gated symlink fixture) |
| `tools/desktop/security_gate.py` | PASS (run under the CI precondition; see note) |
| Desktop `npm ci` / typecheck / vitest / build:web / audit | PASS / PASS / **26/26** / PASS / **0 vulnerabilities** |
| `cargo test --locked` | PASS — **13/13** |
| `cargo check --locked` | PASS |

Focused WO-0023 lanes at this head: codec 19 tests; private object preparation 13 tests (1 capability skip); binary byte fidelity 5 tests; observer revalidation 6 tests; real-Git TREE cache-tree semantics 4 tests; governed authority/E2E and failure injection 21 tests; activated security acceptance gates 5 tests; control-plane `git.write` 11 tests. All non-skipped.

Note on the desktop security gate: CI runs it **before** `npm ci`, so it never sees `node_modules`. Running it locally after `npm ci` makes it scan dependency sources and fail on third-party `invoke()`/`-apple-system`/`dangerouslySetInnerHTML` occurrences. Under the CI precondition it reports `DESKTOP_SECURITY_GATE=PASS` with `FRONTEND_INVOKES=3` and the expected capability surface. This is a pre-existing gate/ordering property, not a regression from this head.

## Prebuilt gates implemented

Every prebuilt gate for this Work Order is now activated. The data-only codec gates went first:
- `test_real_codec_round_trip_preserves_supported_index_semantics`
- `test_real_codec_rejects_sparse_split_conflicted_and_unknown_required_extensions`
- `test_real_codec_cannot_invoke_porcelain_shell_hooks_filters_network_or_credentials`

The five authority/publication gates are now real tests in `tests/runtime/test_git_stage_security.py`: permit request-binding and single use, cancellation/takeover/expiry/emergency stop, authority isolation (no shell/process/hook/filter/network/credentials), request/audit/receipt redaction, and independent non-skipped native proof.

**`PREBUILT:` skips remaining: 0.** No required security acceptance test is skipped for implementation incompleteness.

## Skips remaining and why

| Skip | Reason it is still legitimate |
|---|---|
| `symlink fixture unavailable on this platform/privilege level` | Capability-based: Windows requires a privilege this environment lacks. A cross-platform non-directory variant proves the same fail-closed branch instead |
| `POSIX ...` variants | Pre-existing platform fixtures that need POSIX primitives; unchanged, and each has a Windows-native counterpart lane |

No new blanket skip was introduced, and no skip remains that is caused by incomplete implementation. Every authority, publication, permit-ordering, redaction and failure-injection gate executes on all three platforms.

## Known blockers

- The `DEC-025` ADR header still reads `APPROVED / FINAL CANDIDATE — NOT CANONICAL` while `HCODER-CP-0021` records it canonical. Recorded as `KNOWN_DOC_DRIFT` in the ledger and in Context Lock Delta 002; the historical ADR was deliberately not rewritten.
- The private-temp cleanup path performs a name-based deletion after an identity check. The residual window is a documented bounded race, matching the CP-0022 posture. It is a hardening item, not a defect in this slice, and the failure path no longer removes a pathname it cannot prove it owns.
- `DEC-027` remains **PROPOSED**. This head implements the decision's bounded action and produces the evidence, but promotion is the independent review's decision, not the executor's.
- Residual bounded race on publication, as stated above: atomic publication, not strict CAS.

## Main reconciliation

`origin/main` was integrated into this branch with a provenance-preserving merge commit, as required by the Context Lock promotion reconciliation gate and Prompt 02 Phase A. No rebase and no force push: the branch retains its full 61-commit provenance plus the merge.

The merge absorbed the evidence-only `HCODER-PLATFORM-001` reconciliation (`ccfed1f`), which records the native validation matrix as **CANONICAL / PROVEN_CI MATRIX COMPLETE**. Linux and macOS desktop native Rust/Tauri **build** are now proven, so the earlier statement in this ledger that Linux/macOS native desktop evidence was still open was stale and has been corrected. Launch smoke remains PROVEN_CI on Windows only, and release package/install remains UNPROVEN on all platforms.

## Promotion evidence template

For each exact technical head record:
- commit SHA;
- workflow/run/job IDs;
- runner OS/version/architecture;
- Python and Git-adapter/library version;
- focused test counts and **zero security-gate skips**;
- exact-head verification;
- index transaction/lock behavior;
- stale HEAD/index/worktree rejection;
- no shell/process/hook/filter/network/credential execution;
- permit consumption ordering;
- request/audit/receipt redaction;
- HEDS HIGH/CRITICAL counts.

## STOP

Authority is **implemented** at this Work Order, not pending. `Capability.GIT_WRITE` / `git_stage_paths_v1`, request-bound single-use permit consumption, content-addressed blob publication and atomic `.git/index` publication all exist and are covered by activated acceptance gates, including crash-safety, no-clobber and mid-publication cancellation proof on all three platforms.

Current state, stated plainly:

- **Authority implemented**: yes, bounded to exactly `git_stage_paths_v1`.
- **Correction pending final review**: yes. This ledger records the Prompt 04 correction head; the independent review of it is the next step.
- **PR #69 remains Draft.**
- **HEDS not yet approved.** No FINAL HEDS has been run, and `DEC-027` remains **PROPOSED** — promotion is the reviewer's decision, not the executor's.
- **No merge** and no marking ready for review until that review completes.

The only outstanding implementation seam is the promotion review itself; every executable seam the pre-Codex frontier named is complete (`FINAL_HEDS` aside, which is not an implementation seam).
