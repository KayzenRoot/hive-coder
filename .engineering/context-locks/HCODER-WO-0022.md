# Context Lock — HCODER-WO-0022 / CR-001

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

## WO-0022 CORRECTION SOURCES
These sources govern the corrected implementation and supersede the original strict-CAS assumption only inside this WO candidate:
- `.engineering/corrections/HCODER-WO-0022-CR-001.md`
- `.engineering/evidence/HCODER-WO-0022-CAS-FEASIBILITY.md`
- `.engineering/prebuilt/HCODER-WO-0022-IMPLEMENTATION-PACK.md`
- `.engineering/prebuilt/HCODER-WO-0022-EXECUTOR-BRIEF.md`
- `docs/project-brain/adrs/DEC-026-GOVERNED-EXISTING-FILE-REPLACEMENT.md` (PROPOSED / NOT CANONICAL)

## IMPLEMENTATION SOURCES
- `hive_runtime/workspace_files.py`
- `hive_runtime/workspace_files_posix.py`
- `hive_runtime/workspace_files_windows.py`
- `hive_runtime/workspace_replace_contract.py`
- `hive_runtime/workspace_replace_backend.py`
- `hive_runtime/workspace_replace_posix.py`
- `hive_runtime/workspace_replace_windows.py`
- `hive_runtime/control_types.py`
- `hive_runtime/control_policy.py`
- `hive_runtime/control_plane.py`
- focused workspace create/replace tests under `tests/runtime/`
- `.github/workflows/governance.yml`

## SEALED PREDECESSOR LAW
CP-0021 authority is only `write_file_v1` create-only/no-clobber. WO-0022 may add only separately identifiable `replace_file_v1`; it must not reinterpret or weaken `write_file_v1`.

## CR-001 REPLACEMENT LAW
`replace_file_v1` is a bounded-race atomic replacement candidate, not strict expected-target CAS. Approval binds exact observed old target identity/content and exact new bytes. The implementation must use pinned/no-follow or reparse-resistant traversal, same-filesystem/volume verified staging, latest safe live revalidation, atomic native publication, identity-owned cleanup and the canonical single-use permit.

Every stale state observable before publication must fail closed. Where the native API has no expected-destination identity predicate, an uncooperative external process can still race in the final interval after successful revalidation and before publication. That residual must remain explicit in ADR, evidence and tests and must never be renamed away as CAS.

A platform/filesystem combination lacking objective evidence for atomic publication plus root/link/reparse/staging/cleanup guarantees is unsupported and fail-closed.

## PERMIT LAW
Staging, backend availability and mutation-readiness must be established before permit consumption. A valid permit must not be consumed merely to discover `NotImplemented`, unsupported platform/filesystem, staging failure or observable stale state. The permit is consumed exactly once at the last safe capability boundary immediately associated with a real publication path, followed by the final allowed session/revalidation checks.

## ALLOWED IMPLEMENTATION DELTA
Limited to workspace-file/replacement capability modules, focused runtime/native tests, governance platform wiring strictly required for objective proof, WO/context/correction/evidence/ADR/checkpoint-delta documentation. A Darwin-specific adapter/lane is allowed only to satisfy Issue #63 first-class platform proof. Any unrelated product path remains out of scope.

## EXECUTOR CONTEXT PACK
An implementation executor should not need repository-wide exploration. Read this Context Lock, WO-0022, CR-001, feasibility evidence, Implementation Pack, Executor Brief, CP-0021 workspace-file modules/tests, control-plane request/permit types, DEC-025 and candidate DEC-026. Preserve names/contracts unless a failing native proof demonstrates another same-WO correction is necessary.

## FORBIDDEN ASSUMPTIONS
- A path string proves target identity.
- Atomic rename automatically provides compare-and-swap against an existing target.
- A pre-approval digest remains valid at commit time without live revalidation.
- Windows, Linux and Darwin replacement primitives have equivalent semantics by default.
- Cooperative/advisory locking blocks arbitrary external writers.
- Passing happy-path tests proves race safety.
- Model/task text can authorize or mint a permit.
- A green POSIX lane implies Windows or macOS support.

## STOP CONDITION
Stop and fail closed if a platform primitive cannot prove the CR-001 bounded-race contract: root/link/reparse resistance, verified staging, latest observable expected-state revalidation, atomic publication, identity-owned cleanup and correct permit ordering. Do not claim strict CAS unless a future native primitive objectively predicates publication on the approved destination identity.