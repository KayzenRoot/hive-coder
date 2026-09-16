# Executor Brief — HCODER-WO-0022

This is the minimal handoff for the implementation executor.

## READ FIRST
1. `.engineering/context-locks/HCODER-WO-0022.md`
2. `.engineering/work-orders/HCODER-WO-0022.md`
3. `.engineering/prebuilt/HCODER-WO-0022-IMPLEMENTATION-PACK.md`
4. `docs/project-brain/adrs/DEC-025-TRUSTED-WORKSPACE-FILE-CAPABILITY.md`
5. `docs/project-brain/adrs/DEC-026-GOVERNED-EXISTING-FILE-REPLACEMENT.md`
6. `hive_runtime/workspace_replace_contract.py`
7. current `hive_runtime/workspace_files*.py`
8. `tests/runtime/test_workspace_file_replace_contract.py`
9. `tests/runtime/test_workspace_file_replace_security.py`

## JOB
Complete only `replace_file_v1`. Preserve `write_file_v1` exactly. Make the prebuilt replacement tests meaningful and green, then add the native POSIX/Windows race fixtures required by the WO.

## EXPECTED SYMBOLS
`WorkspaceFileCapability.prepare_replace_request(...)`
`WorkspaceFileCapability.replace_bytes(...)`
Backend `prepare_replace(...)` plus a prepared-target object that can expose bounded observed state, revalidate exact old state and publish approved new bytes without silent concurrent clobber.

## NON-NEGOTIABLES
Approval binds old identity+digest+length and new digest+length. Raw bytes never enter request/audit metadata. Permit is consumed only after read-only validation and immediately before first mutation. Workspace, parent and target are revalidated. `.git`, traversal, symlink/reparse and non-regular targets fail closed. Cleanup is identity-owned. No generic rename/delete/shell/Git surface.

## VALIDATION ORDER
Focused replacement tests -> existing workspace-file regression tests -> full Python discovery -> Windows HIGH_ASSURANCE -> exact-head Governance/Desktop Shell -> evidence/HEDS.

## STOP
If the native OS primitive cannot prove expected-target replacement semantics under a real late race, do not substitute ordinary overwrite. Record the failing proof and return a same-WO Correction Delta.