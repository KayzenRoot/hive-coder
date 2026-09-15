# Evidence Bundle — HCODER-WO-0013

**Risk:** HIGH_ASSURANCE  
**Base:** `3dee30634f48420f7c7ffa1b2c2186066dad97d0`  
**PR:** `#27`

## Required invariants
- provider/model cannot grade or certify itself;
- runner/grader identities are host-sealed, role-bound, independence-lineage-bound and endpoint-bound;
- exact trial identity binds sealed Agent Profile plus StackGenome, provider/model, repository snapshot, Semantic Twin, SuiteLineage, ShadowBench case and evaluation protocol;
- model-visible material contains no oracle secret or oracle digest;
- trial lineage is atomically consumed before provider execution;
- chronology is HMAC-authenticated/hash-chained and rollback below an external monotonic floor fails closed;
- benchmark diversity derives from sealed suite independence roots rather than cosmetic family labels;
- GradeProof is mandatory before a TrialReceipt exists;
- EvidenceDNA binds every trusted BenchmarkResult to exact stack/repository/twin/suite context;
- semantic repository extraction is static/no-exec and deterministic;
- contamination is downgrade/block-only;
- no CP-0005..CP-0012 authority expansion.

## Technical candidate evidence
Corrected implementation head `bf2cf866dad70d63a0808545ce8aabd968b8ca64` passed Governance run `34929170906`.

### Ubuntu source-pack
- exact-head checkout: **PASS** (`EXACT_HEAD_OK=bf2cf866dad70d63a0808545ce8aabd968b8ca64`)
- foundation lock / inventory: **PASS**
- Python compileall: **PASS**
- full unit suite: **241/241 PASS**
- `PYTHONWARNINGS=error::ResourceWarning`: enabled

### Windows Server 2025 HIGH_ASSURANCE
- exact-head checkout: **PASS** (`EXACT_HEAD_OK=bf2cf866dad70d63a0808545ce8aabd968b8ca64`)
- compile: **PASS**
- existing permission/control/Cua HIGH_ASSURANCE regression: **56/56 PASS**

## HEDS correction history
### CR-001 HIGH — RESOLVED IN CANDIDATE
HEDS identified a non-atomic trial replay check, incomplete physical endpoint separation between runner/grader, missing grader rationale evidence and an unbounded provider response. The correction added atomic journal `reserve_once()`, EndpointSeal, GradeProof, a 4 MiB provider-response ceiling and adversarial concurrency/endpoint-collapse tests.

### CR-002 HIGH — RESOLVED IN CANDIDATE
HEDS identified that a CP-0011 BenchmarkResult by itself did not bind repository snapshot/Semantic Twin and could therefore be transplanted into a later certification request. The correction added the EvidenceDNA envelope and made certification accept only verified envelopes matching the current sealed profile, StackGenome, repository snapshot, Semantic Twin and SuiteLineage.

## HEDS adversarial coverage
Reviewed attack classes include provider self-grading, runner/grader lineage collapse, endpoint collapse, trial reroll after execution failure, concurrent duplicate reservation, cosmetic benchmark-family diversity, signed-journal rollback, journal tamper, oracle leakage, missing GradeProof, forged/tampered benchmark evidence, repository/twin/stack evidence transplant, contamination score inflation and paths that could convert evaluation/repository evidence into permission authority.

## Candidate verdict
**TECHNICAL CANDIDATE GREEN.** No unresolved HIGH/CRITICAL technical finding remained after CR-002 at `bf2cf866dad70d63a0808545ce8aabd968b8ca64`.

**FINAL HEDS VERDICT: PENDING.** The promotion/documentation head must pass a fresh exact-head Governance run. After that run, HEDS must review the exact promotion head before DEC-017 / CP-0013 can become APPROVED.

## Residuals not claimed as PASS
- Cross-process/distributed atomic reservation: **NOT APPROVED**.
- Production hardware/remote-backed monotonic anchor: **NOT IMPLEMENTED/UNKNOWN**.
- Real paid provider/model certification: **NOT EXECUTED**.
- Universal multi-language semantic extraction: **NOT IMPLEMENTED**.
- Dynamic taint/runtime dataflow proof: **NOT IMPLEMENTED**.
- Any real provider/model stack being `DISTINGUISHED`: **NOT CLAIMED**.
