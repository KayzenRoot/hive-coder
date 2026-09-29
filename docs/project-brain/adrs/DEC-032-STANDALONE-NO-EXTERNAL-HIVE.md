# DEC-032 — Standalone development without separately installed HIVE

**Status:** PROPOSED / NOT CANONICAL pending exact-head HEDS and governed merge  
**Requested by:** repository owner, 2026-09-28  
**Work Order:** `HCODER-OPS-0001` / Issue #95  
**Canonical predecessor:** `HCODER-CP-0026` and its already approved decisions.  
**Affected:** current development, source ingestion/context, test/review and integration prerequisites.

## Context

The owner is uninstalling the **separate `KayzenRoot/hive` HIVE context/indexing platform** because its local installation is causing development problems. Draft HIVE v1.0.3 context-first PR #94 and separate HIVE repo mount PR #167/Issue #166 are unmerged proposals, not accepted product dependencies. Hive Coder already owns its own repository/source pack, Python `hive_runtime`, Tauri desktop, Git-aware evidence model, GEF/HEDS and GitHub Actions. It also implements third-party Cua Driver's independent MCP transport; this is unrelated to the removable HIVE context MCP.

## Proposed decision

1. Development and acceptance must be completely possible **without** locally installed external HIVE. Canonical Git, the approved Project Brain/ADRs, exact Work Order/Context Lock, repository-local code/tests and GitHub CI/evidence are the source of execution truth.
2. Do not attempt, require or automatically fall back to external HIVE discovery, project/task registry, `project.list`, `checkpoint.read`, `context.search`, `context.build`, `memory.search`, REST `localhost` HIVE calls, mounted `/workspace/projects`, `HIVE_PROJECTS_ROOT`, external index/corpus or Docker/PostgreSQL/Redis as part of a Hive Coder task. This prohibition applies to developer instructions and dependency bootstrapping, not to historical records that describe earlier investigations.
3. Use small, fingerprinted source sets read directly from Git. Local deterministic read-only analysis, selective test harnesses and GitHub exact-head evidence replace the previous external-HIVE executor-context workflow. Missing external HIVE must **never** be a blocker or a synthetic FAILED test.
4. Preserve existing Hive Coder product branding, its `hive_runtime/` implementation, internal `hive-*` schemas, stable public contracts, control plane, local supervisor and external foundation integrations (Open Interpreter ACP, Cua MCP). No renaming or deletion of these based on the shared word 'Hive'.
5. Preserve exact historical source/evidence/decision text. A narrowly appended delta overrides only old external-HIVE execution preconditions in the active WO-0027 context; historical proof and HIGH_ASSURANCE updater gates remain intact.
6. Close obsolete unmerged external-HIVE context and mounting proposals as superseded, not as proven completed. Do not modify `KayzenRoot/hive` WO-032 or uninstall software in this GitHub change.

## Alternatives considered

- Repair and retain the external HIVE container/registration: declined by the owner's explicit uninstall/independence decision.
- Delete everything with Hive in its name: rejected because `hive_runtime/` and wire identifiers are product-owned and already proven through canonical checkpoints.
- Maintain optional external HIVE fallback: outside the requested standalone scope and risks reviving an operational prerequisite. This decision neither designs nor retains that fallback.

## Consequences / validation

Git and deterministic repository-local source inspection become the only mandatory context substrate. The existing four hosted CI workflows stay required, and HEDS remains an independent gate. Static source search must distinguish product-owned Hive names and Cua MCP from the disallowed separate HIVE service. No new code capability, release/signing/updater privilege, checkpoint promotion or production-deployment claim arises from this decision.

**Promotion:** This ADR becomes effective only after its implementing docs/source migration passes required exact-head validation, independent review and governed merge. `HCODER-CP-0026` stays canonical in the meantime.
