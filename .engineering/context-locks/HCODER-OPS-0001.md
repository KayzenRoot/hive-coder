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

## Context Lock Delta 001 — owner-only acceptance (2026-09-29)

**Trigger:** `KayzenRoot` explicitly disallowed mandatory collaborators for all present/future projects. The current repository GitHub ruleset #23768014 already requires zero approvals and no mandatory code-owner review; 13 required status checks, strict main freshness, PR/squash and blocking thread resolution remain active. This Delta does **not** alter GitHub rules or displace those gates.

**Unfrozen only for this same PR:** `.engineering/gef/GEF-REVIEW-PROTOCOL.md`, `.engineering/gef/GEF-EXECUTION-PROTOCOL.md`, `docs/project-brain/09-DEFINITION-OF-DONE.md`, `docs/project-brain/adrs/DEC-033-OWNER-ONLY-GOVERNANCE.md`, and prospective sections of previously allowed AGENTS/README/Decisions Ledger/WO-0027 Context Lock/this Work Order/this Context Lock/Evidence Bundle. No executable, workflow YAML, branch protection, active checkpoint, historic approved predicate, security/release/authz contract or other path unfrozen. Preserve all historical identity claims.

**Admission model:** owner-only `KayzenRoot` issue/PR/review/merge is permissible after: exact-head identity and changed-path scope; current source fingerprint and objective evidence; unresolved HIGH/CRITICAL = 0; all 13 applicable required status checks and unchanged four workflows; zero unresolved blocking review threads; an explicit owner-authored HEDS-style **self-audit labeled NOT INDEPENDENT** (higher-assurance security challenge/negative tests and an explicit owner risk decision on HIGH_ASSURANCE). Optional third-party automated output is untrusted review material, not required and never converted into objective independent approval. A new head invalidates prior gate/audit receipts; exact-main postvalidation still applies. This supersedes old independent-human gate **only for future acceptance**, not historical completed checkpoints.

**Known external finding:** CodeRabbit's review on PR #96 at `a33f30c...` asked for the Criterion 2 source audit on the actual PR head rather than only its base. Only expand this Evidence Bundle within its existing path, with source blob hashes, concrete process-launch sites, bounded import/manifest/workflow evidence, explicit unknowns and the exact-final-head GitHub CI/owner review recorded after the final file commit in PR/Issue comments. Do not claim an impossible self-referential final commit SHA embedded inside that commit's own evidence bytes.

**STOP:** user consent does not authorize bypassing required CI, silently dismissing legitimate blocking findings, modifying immutable accepted history, removing internal product/Cua MCP, running local external-HIVE services, force push, or promoting a new capability without its own exact-head evidence.
