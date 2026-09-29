# HCODER-OPS-0001 — Context Lock

**State:** PROPOSED / SOURCE LOCK for user-directed external HIVE removal, no canonical promotion.  
**Issue:** https://github.com/KayzenRoot/hive-coder/issues/95  
**Branch:** `ops/HCODER-OPS-0001-remove-external-hive`  
**Verified base:** `a9b48bce43fcc2c1a14b70036ed4555f52ba3537`  
**Canonical checkpoint at base:** `HCODER-CP-0026`; DEC-030 canonical; DEC-031 proposed.  
**Related held product PR:** #93 at `d6b512292b2d8bb9085059b4e3ff114a9ddea805` (Draft, unmerged).  
**Superseded proposal:** this repo Draft PR #94 (external HIVE v1.0.3 context-first); separate HIVE PR #167 / Issue #166 (external mount).

## Base source fingerprints (Git blob SHAs)

| Path | SHA |
| --- | --- |
| `AGENTS.md` | `c59e02d5b891a4dcc15b71753eef4884726774c5` |
| `README.md` | `48a6f83528525a65ae9bad62855ff33340850cec` |
| `docs/project-brain/11-CHECKPOINT.md` | `df0ead8e90a46320b8e02bc8dce4f3e27dd67266` |
| `docs/project-brain/10-DECISIONS-LEDGER.md` | `1a142966f7c3ec1178978aefd90d423591c4e6f9` |
| `docs/project-brain/03-SCOPE.md` | `330ce490cc29fc5f3ba4e612db8935dd982d745c` |
| `docs/project-brain/04-ARCHITECTURE.md` | `446a0c47f9ac1be4ce4817c97cd258e7b749129e` |
| `docs/project-brain/09-DEFINITION-OF-DONE.md` | `9770301f87703ec9a24b6c17525c6b55a23da317` |
| `docs/project-brain/13-INTEGRATION-CONTRACTS.md` | `1d42c3086d70308559aeebd40ad96d79c6cad168` |
| `.engineering/context-locks/HCODER-WO-0027.md` | `868147fee2fe72fcef4a82ba99ee5d17193a0c8b` |
| `.github/workflows/governance.yml` | `1f823d7672f95217ca144a4fe8c8d96f318b63d4` |

## Context separation

`KayzenRoot/hive` = separately installed external context/indexing service; remove as prerequisite or integration.  
`KayzenRoot/hive-coder` = THIS product with its own `hive_runtime/`, branding, Git-first governance, versioned `hive-*` protocols and Tauri security; PRESERVE.  
Cua Driver's upstream modern MCP transport is not external HIVE's context MCP; PRESERVE.

## Frozen

All product source/code, package manifests, `.github/workflows/**`, historical ADRs/Work Orders/evidence, approved checkpoint/DoD/security/release policy, HCODER-WO-0027 PR #93 candidate bytes and all four required hosted gates. Only files explicitly named in HCODER-OPS-0001 may change; active WO-0027 Context Lock only append a forward delta and retain original historical text.

## STALE / STOP

If canonical checkpoint, current main, relevant Scope/Architecture/approved ADR, external HIVE dependency findings or active PR #93 changes materially after source capture, refresh exact fingerprints and recompile this lock. If live external integration appears in runtime not covered by this Work Order's allowed paths, STOP and propose a targeted correction. If this branch is reviewed/merged, source truth only changes upon exact-head audit and post-merge evidence. No local uninstall or external HIVE registry mutation is done by this GitHub work.
