# Prebuilt Implementation Pack — HCODER-WO-0022

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

The request metadata must deterministically include contract, normalized path, parent identity, target state=`regular`, exact target identity, old content SHA-256 + byte length, new content SHA-256 + byte length. Raw bytes are never metadata.

## EXECUTABLE PREBUILT SEAMS
- `hive_runtime/workspace_replace_backend.py` freezes the cross-platform `PreparedReplace` / `ReplaceBackend` protocol.
- `hive_runtime/workspace_replace_posix.py` freezes pinned-parent/pinned-target POSIX state and digest behavior while deliberately refusing an unproven publication fallback.
- `hive_runtime/workspace_replace_windows.py` freezes Windows native-proof requirements and deliberately refuses path-only/ordinary overwrite fallback.
- `tests/runtime/test_workspace_file_replace_contract.py` freezes API and metadata behavior.
- `tests/runtime/test_workspace_file_replace_security.py` freezes first adversarial invariants.

Skeleton presence is not evidence of implementation. `NotImplementedError` is an intentional STOP gate until a native primitive is proven.

## PLATFORM ADAPTER SHAPE
POSIX adapter must expose a prepare/revalidate/publish path that keeps root/parent/target handles or identities sufficient to detect target substitution. Windows adapter must use reparse-resistant handle-relative traversal and an OS primitive whose exact semantics can be tested against a concurrent target replacement. Names may be corrected only with a recorded reason; semantics may not be weakened.

## REQUIRED TEST MATRIX
Contract tests must cover: success; missing target; directory target; symlink/reparse target; `.git`; traversal/unsafe Unicode; wrong content; wrong target/workspace/parent; old target identity change; old content change; concurrent replacement after approval; replay; stale permit; cancellation; takeover; emergency stop; oversize payload; workspace replacement; publication failure cleanup; concurrent owner preservation.

POSIX and Windows platform tests must contain at least one real late-race fixture using native filesystem behavior, not only mocks. Windows must include real NTFS junction/reparse coverage when hosted runner supports it.

## IMPLEMENTATION ORDER
1. Contract/tests/protocol seams: PREBUILT.
2. Wire pure request preparation into `WorkspaceFileCapability` and backend `prepare_replace` without mutation.
3. Complete POSIX expected-state revalidation + native publication and adversarial race tests.
4. Complete Windows expected-state revalidation + native publication and adversarial race tests.
5. Wire permit consumption at the last safe point before first mutation.
6. Run focused tests, existing create-only regressions, then full Ubuntu/Windows governance.
7. Build Evidence Bundle and HEDS exact-head review.

## ALLOWED FILE MAP
Product code:
- `hive_runtime/workspace_files.py`
- `hive_runtime/workspace_files_posix.py`
- `hive_runtime/workspace_files_windows.py`
- `hive_runtime/workspace_replace_contract.py`
- `hive_runtime/workspace_replace_backend.py`
- `hive_runtime/workspace_replace_posix.py`
- `hive_runtime/workspace_replace_windows.py`
- control-plane policy/types only if the fixed action cannot be represented without a minimal explicit addition.

Tests:
- `tests/runtime/test_workspace_files.py`
- `tests/runtime/test_workspace_files_posix.py`
- `tests/runtime/test_workspace_files_windows.py`
- `tests/runtime/test_workspace_file_path_security.py`
- `tests/runtime/test_workspace_file_replace_contract.py`
- `tests/runtime/test_workspace_file_replace_security.py`
- new focused native replacement test files are allowed if they reduce coupling.

Governance:
- `.github/workflows/governance.yml` only to ensure new HIGH_ASSURANCE tests execute on both required OS surfaces.

Governance docs/evidence:
- WO-0022 Context Lock, implementation/executor packs, evidence, checkpoint delta, DEC-026 candidate.

## FORBIDDEN SHORTCUTS
No truncate-and-rewrite in place. No path-only check followed by path-only replace. No shell/git command. No broad filesystem library export. No fallback overwrite when the CAS/identity proof fails. No deletion of an object unless the capability proves it created and still owns that exact temporary object.

## CODEX/HUMAN EXECUTOR HANDOFF
Treat this pack as the local map. Do not redesign adjacent systems. Do not scan unrelated repository areas unless a named contract fails to resolve. Prefer completing predeclared tests/contracts over inventing new abstractions. If a platform guarantee is impossible, stop with evidence and propose a same-WO Correction Delta.