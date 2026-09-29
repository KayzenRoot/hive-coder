# Hive Coder

Hive Coder is a standalone AI-native desktop coding and computer-use platform. Its Python `hive_runtime/` engine, Tauri 2 desktop, trusted control plane and Open Interpreter/Cua adapters live in **this repository**; they are not the separately installed `KayzenRoot/hive` context service.

## Development without an external HIVE installation

A running external HIVE server is **not required or used** for this repository's development, build, test, review, checkpoint, context collection or CI. Do not install Docker, PostgreSQL, Redis, a HIVE MCP context server or mount another checkout in order to work on Hive Coder. The owner's separate local HIVE installation may be uninstalled without removing this product's own runtime.

Start from `AGENTS.md` and the accepted `docs/project-brain/11-CHECKPOINT.md`, then approved decisions, Scope/DoD/Architecture and the active Work Order/Context Lock. Use Git, focused repository-local inspection, existing exact-head GitHub Actions and independent HEDS reviews for evidence. The unmerged external-HIVE-context PR #94 is obsolete under HCODER-OPS-0001 / proposed DEC-032.

## Current verified product state

Canonical checkpoint: `HCODER-CP-0026` (release-trust substrate). The Tauri updater implementation is an **unmerged, Draft** candidate under HCODER-WO-0027 / PR #93 and still requires independent review and governed promotion. Production signing, notarization, publication and live install/update remain unproven or unauthorised.

The Cua Driver uses its own upstream MCP protocol and Open Interpreter uses ACP. Neither is the removable HIVE context MCP. Retain the approved product-owned `hive_runtime/`, `hive-*` contract names, Tauri shell, Git and permission/security boundaries.
