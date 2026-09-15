# Checkpoint — Hive Coder

**Checkpoint:** HCODER-CP-0008  
**Status:** CANDIDATE  
**Date:** 2026-09-14  
**Repository:** `KayzenRoot/hive-coder`  
**Work Order:** `HCODER-WO-0008`

## Candidate canonical state
- CP-0007 capability/skills boundary remains authoritative.
- Hive-owned provider/model contracts and normalized catalog exist.
- Provider probes are converted into capability evidence; only verified evidence qualifies a required capability.
- Deterministic router refuses capability downgrade and fails closed when no model qualifies.
- OpenCode Go is a first-class provider identity with zero implied capability.
- Credentials have an explicit redacted scope and are not placed into model/skill metadata.
- Open Interpreter ACP now has bounded `session/prompt` lifecycle with strict result validation.
- Prompt execution creates no desktop capability grant or Cua permit.
- No remote control, billing, automatic skill install or new desktop mutation is introduced.

## Promotion gate
Promote to APPROVED only after exact-head Governance and HEDS approval with no unresolved HIGH/CRITICAL findings.

## Next direction after promotion
Build the resumable Agent Task Runtime: task graph/state machine, checkpoints, budgets, provider/model selection, skill invocation under policy, cancellation/recovery and observable execution history. Remote Hive Control remains a separate HIGH_ASSURANCE subsystem.
