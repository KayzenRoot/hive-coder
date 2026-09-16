# HCODER-WO-0023 — Evidence Ledger

**Status:** SLICE 01 IMPLEMENTED / MUTATION STILL UNPROVEN  
**Canonical base:** `22b56b0f3111158cbf50789b1647c5a578a171c1`  
**Canonical main at execution:** `ccfed1f960c80dc58e4f45cb627451e77c7d5a79`  
**Issue:** `#68`  
**Draft PR:** `#69`

## Claims allowed now

- Current desktop Git observation is read-only and does not execute Git.
- Canonical workspace create/replace capabilities provide the control-plane pattern this WO must preserve.
- `git_stage_paths_v1` product contract, request fields and redaction model are prebuilt.
- The reviewed codec backend provenance gate is **closed for the data-only slice**: `dulwich==1.2.15` is pinned to the exact pure-Python wheel by hash, and the resolver/verifier are committed and consumed by CI.
- A data-only index candidate can be built from an approved observation plus an authority-free stage plan, and the produced bytes are accepted by Git as a correct index.

## Claims explicitly NOT allowed yet

- Git staging is implemented end-to-end.
- Any Git mutation is safe or production-ready.
- `git.write` is canonical.
- Windows, Linux or macOS Git staging is proven end-to-end.
- Strict CAS of index/worktree state exists.
- Object publication or index publication is enabled.

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
**Correction head:** Prompt 02 same-WO correction — TREE cache-tree semantics, main reconciliation and cleanup-hardening review (see below)

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
| Full Python suite | PASS — **468 tests**, `OK`, 57 skipped |
| `tools/desktop/security_gate.py` | PASS (run under the CI precondition; see note) |
| Desktop `npm ci` / typecheck / vitest / build:web / audit | PASS / PASS / **26/26** / PASS / **0 vulnerabilities** |
| `cargo test --locked` | PASS — **13/13** |
| `cargo check --locked` | PASS |

Focused WO-0023 lanes at this head: codec 19 tests; private object preparation 13 tests (1 capability skip); binary byte fidelity 5 tests; observer revalidation 6 tests; real-Git TREE cache-tree semantics 4 tests. All non-skipped.

Note on the desktop security gate: CI runs it **before** `npm ci`, so it never sees `node_modules`. Running it locally after `npm ci` makes it scan dependency sources and fail on third-party `invoke()`/`-apple-system`/`dangerouslySetInnerHTML` occurrences. Under the CI precondition it reports `DESKTOP_SECURITY_GATE=PASS` with `FRONTEND_INVOKES=3` and the expected capability surface. This is a pre-existing gate/ordering property, not a regression from this head.

## Prebuilt gates implemented

Removed from the prebuilt-skip set by this head:
- `test_real_codec_round_trip_preserves_supported_index_semantics`
- `test_real_codec_rejects_sparse_split_conflicted_and_unknown_required_extensions`
- `test_real_codec_cannot_invoke_porcelain_shell_hooks_filters_network_or_credentials`

## Skips remaining and why

| Skip | Reason it is still legitimate |
|---|---|
| `PREBUILT: integrate dedicated git.write control-plane action` | Control-plane authority delta — later phase |
| `PREBUILT: integrate session state with staging executor` | Requires the executor — later phase |
| `PREBUILT: implement Git adapter without executable extension points` | Staging executor seam — later phase |
| `PREBUILT: implement redacted request/audit/receipt` | Publication-phase receipt — later phase |
| `PREBUILT: add native CI proof on all target platforms` | End-to-end staging proof — later phase |
| `symlink fixture unavailable on this platform/privilege level` | Capability-based; a cross-platform non-directory variant runs instead |
| `POSIX ...` variants | Pre-existing Windows platform skips, unchanged |

No new blanket skip was introduced. Skipped security acceptance tests remain a hard non-promotion state for the publication phase.

## Known blockers

- The `DEC-025` ADR header still reads `APPROVED / FINAL CANDIDATE — NOT CANONICAL` while `HCODER-CP-0021` records it canonical. Recorded as `KNOWN_DOC_DRIFT` in the ledger and in Context Lock Delta 002; the historical ADR was deliberately not rewritten.
- `git.write`, permit consumption, blob publication to final object paths and atomic `.git/index` publication remain unimplemented and unavailable. That is the next reviewed phase, not a defect.
- The private-temp cleanup path performs a name-based deletion after an identity check. The residual window is a documented bounded race, matching the CP-0022 posture, and is a hardening item before publication authority rather than a defect in this slice.

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

This head delivers the data-only slice only. `git.write`, permit consumption, blob publication to final object paths and atomic `.git/index` publication are the next reviewed phase and remain unavailable. No merge/promotion of mutation authority until backend selection is governed, all required tests are executable, all three native target lanes are green at exact head, and HEDS reports H/C `0/0`.
