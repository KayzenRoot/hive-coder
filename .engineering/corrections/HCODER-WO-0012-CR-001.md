# HCODER-WO-0012-CR-001 — Certification freshness and repository-intelligence integrity hardening

**Severity:** HIGH  
**Status:** RESOLVED IN IMPLEMENTATION, awaiting final exact-head evidence  
**Work Order:** `HCODER-WO-0012`

## Finding
The first WO-0012 candidate had strong functional tests but left several trust edges weaker than the intended contract:

1. `CertificationEvidence` was caller-constructible without a trusted seal and `RecertificationClock` accepted a caller-supplied current epoch. A caller could therefore fabricate recent-looking certification metadata even though CP-0011 competence itself remained separately measured.
2. `BenchmarkNoveltyLedger` validated case structure/replay history but did not require a host verification of the ShadowBench case before accepting its claimed lineage.
3. `GenomePulseResult.fact_to_invariants` and `IndexedRepository.texts` were structurally frozen dataclass fields backed by mutable mappings.
4. RepoDNA needed stronger canonical-path/root-symlink/open-time checks and a broader default set of known secret-like filenames.
5. ShadowBench verification did not originally recompute every identity-bearing component (`hidden_nonce_digest` and `case_id`) from the host key.

## Correction
- Added **ChronoSeal**, a trusted-host monotonic logical clock. Recertification no longer accepts caller-provided current time.
- Added HMAC-SHA256 **Certification Authority**. Certification evidence is issued from a passing `DISTINGUISHED` CompetenceReport bound to the exact sealed Agent Profile, exact Competence Standard, exact repository snapshot and ChronoSeal epoch. Benchmark families are derived from the report rather than caller input.
- `RecertificationClock` rejects unsigned/tampered certification evidence and derives current epoch from ChronoSeal.
- `OutcomeAuthority` also derives observation epoch from ChronoSeal.
- `BenchmarkNoveltyLedger` now requires a trusted case verifier before accepting any case into novelty state.
- ShadowBench verification recomputes lineage, nonce, prompt digest, oracle digest and case identity from trusted factory state plus verified Code Truth.
- Froze indexed repository text and GenomePulse fact/invariant maps with immutable mapping views.
- Hardened RepoDNA with root-symlink rejection, canonical path validation, root containment, no-follow file opening where the platform exposes it, regular-file `fstat`, bounded reads and additional secret-like filename exclusions.
- Added adversarial tests covering these paths.

## Residual boundary
ChronoSeal and Benchmark Novelty state are session-bounded in CP-0012. Durable cross-restart time/novelty attestation is intentionally deferred to a later governed persistence/certification-lab increment. This does not enable competence promotion because WO-0012 still has no provider-backed trusted benchmark runner/grader.

## Closure gate
This Correction Delta closes only after the corrected final head passes exact-head Governance and HEDS confirms no unresolved HIGH/CRITICAL finding.
