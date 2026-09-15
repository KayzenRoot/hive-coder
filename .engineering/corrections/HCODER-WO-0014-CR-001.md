# HCODER-WO-0014-CR-001 — SkillGenome transplant prevention

**Severity:** HIGH  
**Status:** RESOLVED IN CANDIDATE  
**Work Order:** `HCODER-WO-0014`

## Finding
The first Elite Specialist Forge candidate sealed both StackGenome and SkillGenome into the blueprint, but did not require the SkillGenome fingerprint presented at forge time to equal `ExecutionStackDescriptor.skillset_digest`. A caller could therefore present a different skill composition while retaining the same already-certified AgentProfile/StackGenome identity.

## Correction
- `SpecialistForge.forge()` now computes the SkillGenome fingerprint before sealing.
- ForgeSeal rejects unless `descriptor.skillset_digest == skill_genome.fingerprint()`.
- The resulting blueprint still binds both exact StackGenome and exact SkillGenome fingerprints.
- Added adversarial test `test_skill_genome_must_match_stack_genome_skillset`.

## Closure gate
RESOLVED becomes final only after corrected exact-head Governance is green and final HEDS reports no unresolved HIGH/CRITICAL findings.
