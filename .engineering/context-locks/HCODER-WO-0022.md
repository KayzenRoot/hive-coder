# Context Lock — HCODER-WO-0022

**Canonical base:** `9c2623f8b335cf29b63b5db5f43e694bfd77938e`  
**Checkpoint:** `HCODER-CP-0021`  
**Risk:** HIGH_ASSURANCE  
**Issue:** `#61`

## SOURCE PRIORITY
`Checkpoint > Decisions Ledger / ADRs > Scope > Definition of Done > Architecture > Requirements > Backlog > WO-specific evidence`.

## REQUIRED CANONICAL SOURCES
- `AGENTS.md`
- `docs/project-brain/00-SOURCE-HIERARCHY.md`
- `docs/project-brain/02-REQUIREMENTS.md`
- `docs/project-brain/03-SCOPE.md`
- `docs/project-brain/04-ARCHITECTURE.md`
- `docs/project-brain/05-SECURITY.md`
- `docs/project-brain/06-TEST-BENCHMARK-PLAN.md`
- `docs/project-brain/08-BACKLOG.md`
- `docs/project-brain/09-DEFINITION-OF-DONE.md`
- `docs/project-brain/10-DECISIONS-LEDGER.md`
- `docs/project-brain/11-CHECKPOINT.md`
- `docs/project-brain/adrs/DEC-025-TRUSTED-WORKSPACE-FILE-CAPABILITY.md`
- `.engineering/work-orders/HCODER-WO-0021.md`
- `.engineering/evidence/HCODER-CP-0021-CANONICAL-CLOSEOUT.md`

## IMPLEMENTATION SOURCES
- `hive_runtime/workspace_files.py`
- `hive_runtime/workspace_files_posix.py`
- `hive_runtime/workspace_files_windows.py`
- `hive_runtime/control_types.py`
- `hive_runtime/control_policy.py`
- `hive_runtime/control_plane.py`
- `tests/runtime/test_workspace_files.py`
- `tests/runtime/test_workspace_files_posix.py`
- `tests/runtime/test_workspace_files_windows.py`
- `tests/runtime/test_workspace_file_path_security.py`
- `.github/workflows/governance.yml`

## SEALED PREDECESSOR LAW
CP-0021 authority is only `write_file_v1` create-only/no-clobber. WO-0022 may add only separately identifiable `replace_file_v1`; it must not reinterpret or weaken `write_file_v1`.

## ALLOWED IMPLEMENTATION DELTA
Initially limited to the workspace-file capability modules, focused runtime tests, governance test wiring if strictly required, WO/context/evidence/ADR/checkpoint-delta documentation. Any additional product path requires explicit source-derived justification recorded before change.

## EXECUTOR CONTEXT PACK
An implementation executor should not need repository-wide exploration. Read this Context Lock, WO-0022, CP-0021 workspace-file modules/tests, control-plane request/permit types, DEC-025 and the candidate DEC-026. Preserve names/contracts unless a failing platform proof demonstrates a necessary correction.

## FORBIDDEN ASSUMPTIONS
- A path string proves target identity.
- Atomic rename automatically provides compare-and-swap against an existing target.
- A pre-approval digest remains valid at commit time without live revalidation.
- Windows and POSIX replacement primitives have equivalent semantics by default.
- Passing happy-path tests proves race safety.
- Model/task text can authorize or mint a permit.

## STOP CONDITION
Stop and return a Correction Delta if the proposed platform primitive cannot prove no-follow/reparse resistance plus expected-target compare-and-swap semantics. Never silently downgrade the contract.