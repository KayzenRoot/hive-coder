# HCODER-WO-0014-CR-004 — ProfileSeal routing spoof prevention

**Severity:** HIGH  
**Status:** RESOLVED IN CANDIDATE  
**Work Order:** `HCODER-WO-0014`

## Finding
`AgentProfile.fingerprint()` intentionally represents the canonical unsigned profile fields and excludes the HMAC `profile_tag`. ForgeSeal validated the profile at blueprint creation through StackGenomeAuthority, but the first Pareto Crown routing path only compared the candidate profile fingerprint with the blueprint. An unsealed profile carrying identical canonical fields could therefore reach certification/ranking checks if an injected certification verifier did not independently reject it.

## Correction
- `ParetoCrown.select()` now directly calls the trusted `AgentProfileAuthority.verify(profile)` exposed by SpecialistForge before accepting a routing candidate.
- Fingerprint equality with the ForgeSeal blueprint remains required after seal verification.
- Certification is still revalidated against exact repository + Semantic Twin after ProfileSeal verification.
- Added an adversarial test proving an unsealed profile with the exact same canonical fingerprint cannot enter selection.

## Closure gate
RESOLVED becomes final only after corrected exact-head Governance is green and final HEDS reports no unresolved HIGH/CRITICAL findings.
