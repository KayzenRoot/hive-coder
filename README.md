# Hive Coder

Hive Coder is a standalone AI-native desktop coding and computer-use platform. Its Python `hive_runtime/` engine, Tauri 2 desktop, trusted control plane and Open Interpreter/Cua adapters live in **this repository**; they are not the separately installed `KayzenRoot/hive` context service.

## Development without an external HIVE installation

A running external HIVE server is **not required or used** for this repository's development, build, test, review, checkpoint, context collection or CI. Do not install Docker, PostgreSQL, Redis, a HIVE MCP context server or mount another checkout in order to work on Hive Coder. The owner's separate local HIVE installation may be uninstalled without removing this product's own runtime.

Start from `AGENTS.md` and the accepted `docs/project-brain/11-CHECKPOINT.md`, then accepted decisions, Scope/DoD/Architecture and the active Work Order/Context Lock. Use Git, focused repository-local inspection, exact-head GitHub Actions and a substantive HEDS-style OWNER_SELF_AUDIT / NOT_INDEPENDENT. The no-external-HIVE development decision DEC-032 is accepted after operational PR #96; the obsolete context PR #94 remained unmerged.

## Repository governance without collaborators
The `KayzenRoot` owner may handle Work Orders, author/read PRs, review, commit and merge on its own. Current protected `main` requires applicable exact-head CI, an up-to-date base, resolved blocking threads and permitted squash merge, but requires **zero human approvals**. The owner records an exact-head semantic review clearly labeled `OWNER_SELF_AUDIT / NOT_INDEPENDENT` and explicit HIGH_ASSURANCE risk acceptance when applicable. No second account or paid code-review bot is needed. This policy DEC-033 was accepted through Issue #95 / merged PR #96 and its four postmerge workflows, with no required second account. Earlier independent human reviews remain historically accurate, while new work uses honest owner-only audits and unchanged security/CI checks.

## Current verified product state

Canonical checkpoint until conditional CP-0027 promotion is proven: `HCODER-CP-0026` (release-trust substrate). The bounded Rust-only Tauri updater product from HCODER-WO-0027 / PR #93 is already MERGED / PRODUCT POSTVALIDATED on `main c25103bdfdfb74e12891fcdc13b0495d3fcf786d` (13 required checks, four fresh product-main workflows, guarded merge preserving reviewed tree). Its separate docs-only conditional CP-0027 / DEC-031 promotion is the current Work Order stage; its new exact-head audit/merge and *fresh postpromotion* main gates remain mandatory. Shipped trust is unconfigured; signing, endpoint provisioning, real signed download, installation, notarization, publication and N-to-N+1 remain unproven/unapproved. Separate pre-existing Linux `glib 0.18.5` advisory remediation is Issue #97 before clean production distribution.

The Cua Driver uses its own upstream MCP protocol and Open Interpreter uses ACP. Neither is the removable HIVE context MCP. Retain the approved product-owned `hive_runtime/`, `hive-*` contract names, Tauri shell, Git and permission/security boundaries.
