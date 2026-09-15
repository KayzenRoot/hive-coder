# HCODER-WO-0013-CR-001 — Atomic trial reservation and independence hardening

**Severity:** HIGH  
**Status:** RESOLVED IN CANDIDATE  
**Work Order:** `HCODER-WO-0013`

## Finding
The first Provider Certification Lab candidate was functionally green but HEDS found trust edges that were not strong enough for HIGH_ASSURANCE:

1. trial replay prevention used a non-atomic check-then-append sequence, allowing a theoretical concurrent double reservation;
2. runner/grader independence was bound to logical lineage and Python object identity, but not to a host-sealed endpoint identity;
3. a grader could return a pass/fail decision without an evidence/rationale digest;
4. provider response size was unbounded in the certification path.

## Correction
- Added journal-level `RLock` and atomic `reserve_once()` so replay check and durable append are one critical section.
- Added **EndpointSeal** semantics by binding `endpoint_digest` into each HMAC-sealed `LabActor`; StackSeal and trial execution reject equal runner/grader endpoint digests even if labels differ.
- Added **GradeProof**: every `GradeDecision` must carry a SHA-256 rationale/evidence digest before a receipt can be issued.
- Added a 4 MiB provider-response ceiling to the certification path.
- Preserved **One-Shot Trial Law**: lineage is durably consumed before provider execution, so provider/grader errors cannot be exploited to reroll the same hidden case.
- Added concurrent adversarial reservation tests plus endpoint-collapse and missing-GradeProof tests.

## Closure gate
RESOLVED becomes final only after exact-head Governance passes on the corrected candidate and HEDS finds no remaining HIGH/CRITICAL issue in scope.
