# HCODER-WO-0013-CR-002 — EvidenceDNA repository/twin/stack transplant prevention

**Severity:** HIGH  
**Status:** RESOLVED  
**Work Order:** `HCODER-WO-0013`

## Finding
The CP-0011 `BenchmarkResult` schema intentionally measures competence but has no repository snapshot or Semantic Twin field. The first WO-0013 candidate could therefore convert valid trial receipts into a trusted BenchmarkResult and later present that result while requesting certification against a different repository snapshot. The CP-0012 Certification Authority would bind the final certificate to the requested snapshot, creating a potential benchmark-evidence transplant across repository states.

## Correction
- Added **EvidenceDNA Envelope** (`LabBenchmarkEvidence`).
- TrialReceipt now directly binds exact StackGenome fingerprint, repository snapshot, Semantic Twin fingerprint, SuiteLineage fingerprint and benchmark dimension in addition to profile/trial/response/chronology.
- BenchmarkAttestation aggregates only receipts with identical EvidenceDNA and returns an HMAC-sealed envelope around the CP-0011 BenchmarkResult.
- `ProviderCertificationLab.evaluate_and_certify()` accepts EvidenceDNA envelopes rather than naked BenchmarkResults.
- Before ExperienceRouter scoring, every envelope must verify and exactly match the sealed profile, current StackGenome, current repository snapshot and current Semantic Twin.
- AuditableCertificationReport records the EvidenceDNA envelope fingerprints, not only portable BenchmarkResult fingerprints.
- Added adversarial tests proving envelope tamper rejection and rejection of a valid benchmark result transplanted to a different repository/twin.

## Closure evidence
Exact implementation/documentation head `91fec0821f8cececed2cfeb44a18ce508aa03e42` passed Governance run `34953929007`: Ubuntu **241/241 PASS**, Windows Server 2025 HIGH_ASSURANCE **56/56 PASS**, both exact-head verified. HEDS review `5208260699` returned **APPROVED** with zero open HIGH/CRITICAL findings in scope.
