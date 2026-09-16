# Prebuilt Implementation Pack — HCODER-WO-0022 / CR-001

Purpose: make implementation execution narrow, deterministic and low-discovery. This pack is a build map, not authority.

## TARGET API SHAPE
Extend `WorkspaceFileCapability` without changing `write_file_v1` semantics.

Frozen public surface:
- `prepare_replace_request(session_id, relative_path, content) -> ActionRequest`
- `replace_bytes(request, content, *, permit_token) -> WorkspaceReplaceReceipt`

Frozen constants/types live in `hive_runtime/workspace_replace_contract.py`:
- `REPLACE_CONTRACT = "hive-workspace-replace-v1"`
- `REPLACE_ACTION = "replace_file_v1"`
- `REPLACE_TARGET_STATE = "regular"`
- `WorkspaceReplaceObservedState`
- `WorkspaceReplaceReceipt`

The request metadata deterministically includes contract, normalized path, parent identity, target state=`regular`, exact observed target identity, old content SHA-256 + byte length, new content SHA-256 + byte length. Raw bytes are never metadata.

## CR-001 CONTRACT SELECTION
Strict expected-target CAS is no longer the claimed portable contract. The selected candidate is **bounded-race atomic replacement**:
- bind approval to exact observed old identity/content and exact new bytes;
- revalidate workspace/parent/target/old bytes as late as safely possible before publication;
- fail closed on every stale state observed before publication;
- publish the exact approved new bytes with a platform-proven atomic namespace replacement;
- explicitly retain the documented residual race from an uncooperative external process acting after final successful revalidation and before the native publication call where the OS API cannot predicate publication on the approved identity;
- never call this residual contract strict CAS;
- fail closed on platform/filesystem combinations lacking proven atomic replacement/safety semantics.

## EXECUTABLE PREBUILT SEAMS
- `hive_runtime/workspace_replace_backend.py` freezes the cross-platform `PreparedReplace` / `ReplaceBackend` protocol.
- `hive_runtime/workspace_replace_posix.py` already proves pinned/live expected-state revalidation; its publication seam must now implement the corrected atomic replacement contract rather than an imaginary CAS predicate.
- `hive_runtime/workspace_replace_windows.py` freezes Windows handle/reparse-resistant requirements; publication must use a documented atomic replacement path with native race evidence.
- `tests/runtime/test_workspace_file_replace_contract.py` freezes API and metadata behavior.
- `tests/runtime/test_workspace_file_replace_security.py` freezes adversarial invariants.
- `tests/runtime/test_workspace_file_replace_posix.py` proves read-only expected-state revalidation and currently keeps publication fail-closed until corrected publication is implemented.

Skeleton presence is not implementation evidence. `NotImplementedError` remains a STOP gate until the corrected publication implementation and tests exist.

## PUBLICATION DESIGN LAW
Atomic namespace publication and strict expected-inode CAS are distinct. Implementation MUST NOT claim the latter.

A platform implementation must:
1. create/write the replacement as a capability-owned temporary regular object inside the pinned/verified parent filesystem context;
2. verify the temporary object's identity and exact new digest/length before publication;
3. perform the latest safe revalidation of root, parent and live destination old identity/content;
4. reach the mutation-ready point without consuming the permit while publication is unavailable/unimplemented;
5. consume the valid request-bound single-use permit at the final safe boundary immediately associated with the real mutation path;
6. run final cancellation/session checks permitted by the platform design;
7. atomically publish the verified temporary object over the destination using the selected native primitive;
8. verify post-publication bytes/receipt metadata without claiming that post-check retroactively creates CAS semantics;
9. clean up only a temporary object whose identity the capability still proves it owns.

Do not truncate the destination in place. Do not copy bytes into the destination after publication. Cross-filesystem fallback is forbidden.

## PLATFORM ADAPTER SHAPE
### Linux/POSIX
Use pinned parent/root traversal already established by CP-0021. Temporary creation must be parent-relative, exclusive/no-follow, same-filesystem, mode-safe and identity-owned. Final publication may use a documented atomic same-filesystem rename primitive only after latest live destination revalidation. Real tests must force target substitution/content mutation both before and around the publication boundary and assert the corrected bounded-race contract without labeling the final unobservable interval CAS.

### Windows
Use reparse-resistant handle-oriented traversal and identity capture. Replacement staging must remain on the same volume and be capability-owned. Use a documented Windows replacement/rename primitive only after latest live destination revalidation. Native tests must include file-ID/content changes, junction/reparse cases and publication failure cleanup. Path-only validation is insufficient for prepublication checks.

### macOS/Darwin
Dedicated native evidence is mandatory under HCODER-PLATFORM-001 / Issue #63. Do not inherit Linux proof. Same-filesystem atomic rename/swap/exclusive facilities must be validated against the corrected contract and filesystem behavior before macOS is declared supported.

## REQUIRED TEST MATRIX
Contract tests: success; missing target; directory target; `.git`; traversal/unsafe Unicode; wrong content; wrong target/workspace/parent; old identity change; old content change; replay; stale permit; cancellation; takeover; emergency stop; oversize payload; workspace replacement.

Native security tests: symlink/reparse target; linked/reparse parent; staging object ownership; staging digest mismatch; target change before final revalidation; content change before final revalidation; publication failure cleanup; same-filesystem requirement; concurrent owner preservation for observable stale-state cases; exact approved bytes after success.

Race tests must distinguish two assertions:
- **guaranteed:** stale state observed before publication causes fail-closed;
- **documented residual:** an uncooperative external change in the final interval not expressible as a native expected-target predicate is not claimed eliminated.

No deterministic test may be written to falsely imply a guarantee the native API does not expose.

## PERMIT ORDERING
Current prebuilt `replace_bytes` ordering must be corrected before promotion. A permit MUST NOT be consumed before discovering that `publish_replace` is `NotImplemented` or otherwise unavailable. Platform preparation must expose a mutation-ready publication path first. The permit is then consumed exactly once at the last safe point immediately before that real mutation path. Wrong content, stale state, unavailable backend, staging failure and prepublication validation failure must leave a valid permit unconsumed where the control-plane API permits objective verification.

## IMPLEMENTATION ORDER
1. Contract/tests/protocol seams: PREBUILT.
2. Pure request preparation and backend prepare seam: PREBUILT.
3. POSIX expected-state revalidation: PREBUILT/DONE read-only.
4. CR-001 feasibility + corrected WO/ADR: DONE.
5. Refine backend protocol only as minimally necessary to represent staging + mutation-ready publication without broadening authority.
6. Implement POSIX staging, final revalidation, atomic publication and identity-owned cleanup.
7. Fix `replace_bytes` permit ordering and add permit-not-burned tests.
8. Implement Windows expected-state revalidation/staging/publication and native tests.
9. Add macOS native validation lane and implementation/evidence before declaring macOS support.
10. Run focused tests, existing create-only regressions, full platform governance, Evidence Bundle and HEDS exact-head review.

## ALLOWED FILE MAP
Product code:
- `hive_runtime/workspace_files.py`
- `hive_runtime/workspace_files_posix.py`
- `hive_runtime/workspace_files_windows.py`
- `hive_runtime/workspace_replace_contract.py`
- `hive_runtime/workspace_replace_backend.py`
- `hive_runtime/workspace_replace_posix.py`
- `hive_runtime/workspace_replace_windows.py`
- a Darwin-specific replacement adapter only if platform dispatch requires a distinct implementation;
- control-plane policy/types only if the fixed action cannot be represented without a minimal explicit addition.

Tests:
- existing workspace-file and replacement test files named by the WO;
- new focused native replacement tests where they reduce coupling;
- macOS-specific native test file/lane under Issue #63.

Governance:
- `.github/workflows/governance.yml` only to ensure HIGH_ASSURANCE tests execute on required OS surfaces.

Governance docs/evidence:
- WO-0022 Context Lock, CR-001, implementation/executor packs, feasibility/evidence, checkpoint delta, DEC-026 candidate.

## FORBIDDEN SHORTCUTS
No truncate-and-rewrite in place. No shell/Git command. No broad filesystem export. No cross-filesystem copy fallback. No deletion of an object unless capability ownership is proven. No ordinary atomic rename may be labeled strict CAS. No cooperative lock may be represented as blocking arbitrary external writers. No valid permit may be intentionally burned merely to discover an unimplemented publication seam.

## CODEX/HUMAN EXECUTOR HANDOFF
Treat this pack as the local map. Do not redesign adjacent systems. Do not scan unrelated repository areas unless a named contract fails to resolve. Prefer completing predeclared tests/contracts over inventing new abstractions. If a platform cannot prove the corrected atomic-publication/safety contract, mark that platform/filesystem capability unavailable and stop rather than weakening guarantees.