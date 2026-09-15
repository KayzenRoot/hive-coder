# Checkpoint — Hive Coder

**Checkpoint:** HCODER-CP-0009  
**Status:** CANDIDATE  
**Date:** 2026-09-14  
**Repository:** `KayzenRoot/hive-coder`  
**Work Order:** `HCODER-WO-0009`

## Candidate canonical state
- CP-0005 permission authority and CP-0007/0008 capability truth remain authoritative.
- Hive has a deterministic sequential Agent Task Runtime over model-prompt and governed-skill nodes.
- Task plans are validated as acyclic DAGs and bound to checkpoints by canonical fingerprints.
- Checkpoints are atomically persisted and HMAC-authenticated with a trusted host key.
- Checkpoint payload contains workflow metadata only, not credentials, approvals, permits, capability grants, skill content, raw prompts or model output.
- Model tasks route through CP-0008 verified capabilities.
- Skill tasks execute only through a trusted host `SkillExecutionPort`; the runtime does not activate skills or grant permissions.
- Per-node attempt and global execution/failure budgets are bounded.
- Pause, continue, cancellation, terminal-state invariants and structured execution history exist.
- Crash recovery never auto-replays an interrupted skill. Explicit trusted-host retry/fail disposition is required and remains attempt-budget bounded.
- Task snapshots exposed to callers are immutable views rather than promotion/state authority.
- No remote-control listener, real provider credential, parallel scheduler or new desktop mutation capability is introduced.

## Promotion gate
Promote only after exact-head Governance and HEDS approval with no unresolved HIGH/CRITICAL findings.

## Next direction after promotion
Implement the **Agent Orchestrator & Work Loop** over CP-0009: decomposition/planning contracts, task creation from an approved objective, model/skill selection policies, bounded self-correction, repository/test evidence hooks, progress/ETA telemetry and explicit STOP CONDITION evaluation. Remote Hive Control remains a separate HIGH_ASSURANCE subsystem.
