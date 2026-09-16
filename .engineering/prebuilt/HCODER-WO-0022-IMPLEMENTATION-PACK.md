# Prebuilt Implementation Pack — HCODER-WO-0022

Purpose: make implementation execution narrow, deterministic and low-discovery. This pack is a build map, not authority.

## TARGET API SHAPE
Extend `WorkspaceFileCapability` without changing `write_file_v1` semantics.

Proposed public surface:
- `prepare_replace_request(relative_path: str, content: bytes) -> ActionRequest`
- `replace_bytes(relative_path: str, content: bytes, permit: ExecutionPermit) -> WorkspaceFileReceipt`

Proposed constants:
- `REPLACE_CONTRACT = "hive-workspace-replace-v1"`
- `REPLACE_ACTION = "replace_file_v1"`
- retain `DEFAULT_MAX_WRITE_BYTES = 1_048_576`

The request metadata must deterministically include contract, normalized path, parent identity, target state=`regular`, exact target identity, old content SHA-256 + byte length, new content SHA-256 + byte length. Raw bytes are never metadata.

## PLATFORM ADAPTER SHAPE
POSIX adapter must expose a prepare/revalidate/publish path that keeps root/parent/target handles or identities sufficient to detect target substitution. Windows adapter must use reparse-resistant handle-relative traversal and an OS primitive whose exact semantics can be tested against a concurrent target replacement. Names may be corrected only with a recorded reason; semantics may not be weakened.

## REQUIRED TEST MATRIX
Contract tests must cover: success; missing target; directory target; symlink/reparse target; `.git`; traversal/unsafe Unicode; wrong content; wrong target/workspace/parent; old target identity change; old content change; concurrent replacement after approval; replay; stale permit; cancellation; takeover; emergency stop; oversize payload; workspace replacement; publication failure cleanup; concurrent owner preservation.

POSIX and Windows platform tests must contain at least one real late-race fixture using native filesystem behavior, not only mocks. Windows must include real NTFS junction/reparse coverage when hosted runner supports it.

## IMPLEMENTATION ORDER
1. Freeze request/receipt metadata contract in tests.
2. Add pure validation/request preparation with no mutation.
3. Add POSIX platform primitive and adversarial tests.
4. Add Windows platform primitive and adversarial tests.
5. Wire permit consumption at the last safe point before first mutation.
6. Run focused tests, then full Ubuntu/Windows governance.
7. Build Evidence Bundle and HEDS exact-head review.

## ALLOWED FILE MAP
Product code:
- `hive_runtime/workspace_files.py`
- `hive_runtime/workspace_files_posix.py`
- `hive_runtime/workspace_files_windows.py`
- control-plane policy/types only if the fixed action cannot be represented without a minimal explicit addition.

Tests:
- `tests/runtime/test_workspace_files.py`
- `tests/runtime/test_workspace_files_posix.py`
- `tests/runtime/test_workspace_files_windows.py`
- `tests/runtime/test_workspace_file_path_security.py`
- a new focused replacement test file is allowed if it reduces coupling.

Governance:
- `.github/workflows/governance.yml` only to ensure new HIGH_ASSURANCE tests execute on both required OS surfaces.

Governance docs/evidence:
- WO-0022 Context Lock, implementation pack, evidence, checkpoint delta, DEC-026 candidate.

## FORBIDDEN SHORTCUTS
No truncate-and-rewrite in place. No path-only check followed by path-only replace. No shell/git command. No broad filesystem library export. No fallback overwrite when the CAS/identity proof fails. No deletion of an object unless the capability proves it created and still owns that exact temporary object.

## CODEX/HUMAN EXECUTOR HANDOFF
Treat this pack as the local map. Do not redesign adjacent systems. Do not scan unrelated repository areas unless a named contract fails to resolve. Prefer completing predeclared tests/contracts over inventing new abstractions. If a platform guarantee is impossible, stop with evidence and propose a same-WO Correction Delta.