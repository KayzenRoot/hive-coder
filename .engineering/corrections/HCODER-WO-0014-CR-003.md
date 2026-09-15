# HCODER-WO-0014-CR-003 — TwinSeal certification transplant prevention

**Severity:** HIGH  
**Status:** RESOLVED IN CANDIDATE  
**Work Order:** `HCODER-WO-0014`

## Finding
HEDS found that ForgeSeal bound the Semantic Repository Twin into the resulting specialist blueprint, but the trusted certification-verifier contract received only AgentProfile, certification fingerprint and repository snapshot. A valid certification for the same repository snapshot could therefore be presented while asking ForgeSeal to bind a different Semantic Twin, without giving the verifier the requested Twin to compare against its CP-0013 EvidenceDNA/auditable certification record.

## Correction
- Extended the trusted `CertificationVerifier` contract to receive the exact `semantic_twin_fingerprint` in addition to profile, certification evidence and repository snapshot.
- `SpecialistForge.forge()` now requires certification verification against the exact requested repository + Semantic Twin context before issuing ForgeSeal.
- `ParetoCrown.select()` repeats the same repository + Twin certification verification at routing time, so stale/revoked/transplanted certification cannot survive through an old blueprint.
- Added an adversarial Semantic Twin transplant test.

## Closure gate
RESOLVED becomes final only after corrected exact-head Governance is green and final HEDS reports no unresolved HIGH/CRITICAL findings.
