# HCODER-WO-0014-CR-002 — Mandatory HorizonGate lineage enforcement

**Severity:** HIGH  
**Status:** RESOLVED IN CANDIDATE  
**Work Order:** `HCODER-WO-0014`

## Finding
HEDS found that `AntiOverfitHorizon` correctly rejected exact/prompt/source-lineage replay when explicitly called, but the first arena design did not mechanically require that call before `ArenaEvidence` entered `MasteryLattice`. A caller could create distinct ChallengeMorph variants from the same ShadowBench source lineage and submit them directly as separate mastery samples.

## Correction
- Added `source_lineage_root` to HMAC-sealed `ArenaEvidence`.
- `ArenaEvidenceAuthority.issue()` derives that lineage only from the verified `ArenaChallenge`; callers cannot supply it independently.
- Added mandatory **HorizonGate** inside `MasteryLattice`: one `(blueprint, source_lineage_root)` can contribute at most one mastery sample, regardless of morph, suite or challenge identity.
- Existing exact challenge replay rejection remains in place.
- Added adversarial test using two different challenges and two different suite families over the same source case, proving the second evidence item cannot enter mastery even when `AntiOverfitHorizon` is bypassed.

## Closure gate
RESOLVED becomes final only after corrected exact-head Governance is green and final HEDS reports no unresolved HIGH/CRITICAL findings.
