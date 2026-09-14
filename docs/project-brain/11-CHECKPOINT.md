# Checkpoint — Hive Coder

**Checkpoint:** HCODER-CP-0001  
**Status:** APPROVED  
**Date:** 2026-09-14  
**Repository:** `KayzenRoot/hive-coder`  
**Approved Work Order:** `HCODER-WO-0001`  
**PR:** `#2`

## Proven canonical state
- The repository and governed Git history exist.
- The initial Source Pack is established, including Source Hierarchy, Overview, Requirements, Scope, Architecture, Security, Test/Benchmark Plan, Deployment, Backlog, Definition of Done, Decisions Ledger, UI/UX, Integration Contracts and License/Provenance.
- Prompt mode is `GEF_V1`.
- Review mode is `HEDS_DELTA`.
- Work Order, Context Lock, Correction Delta, Evidence Bundle and review templates exist.
- Executor, reviewer and correction prompt templates exist.
- GitHub issue/PR templates, CODEOWNERS and the `Governance` workflow exist.
- `HCODER-WO-0001-CR-001` was resolved inside the same Work Order/PR.
- Exact-head Governance evidence passed on the reviewed bootstrap candidate before checkpoint promotion.

## Product state
No Hive Coder product implementation has been proven yet. There is no proven desktop shell, OpenCode Go provider integration, Open Interpreter runtime adapter, Cua computer-use adapter, permission engine, product test suite, packaging or production deployment.

## Approved product direction
- Separate Hive Coder product/repository.
- Open Interpreter + Cua are preferred foundation candidates behind Hive-owned adapters, subject to license/provenance and prototype validation.
- Premium original Hive desktop UX, inspired by modern desktop qualities without copying proprietary Apple assets.
- Safe computer use with permission gating, visible control state, emergency stop and user takeover.

## Next necessary increment
Perform the license/provenance and foundation-integration assessment for Open Interpreter and Cua, then compile the smallest architecture spike. Do not treat either foundation as locked until that assessment is approved.
