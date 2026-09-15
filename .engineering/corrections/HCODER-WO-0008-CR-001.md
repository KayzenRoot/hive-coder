# Correction Delta — HCODER-WO-0008-CR-001

## Finding
**HIGH · provider-controlled verification authority.** The initial provider probe DTO contained a `verified` boolean supplied by the provider adapter. A compromised/buggy adapter could therefore self-promote arbitrary capabilities into CP-0007 VERIFIED evidence and become routing-eligible.

## Correction
- Raw `CapabilityProbeResult` no longer has a verification field.
- `ProviderCatalog` requires a trusted host `CapabilityVerifier` dependency at construction.
- Only the trusted verifier can convert a raw observation to VERIFIED evidence.
- Provider names, model names, source/detail prose and raw probe content carry no verification authority.
- Added adversarial test where a malicious provider/model/probe claims computer use and remains unverified.
- Duplicate capability observations fail closed.

## Residual boundary
Production verifier implementations must themselves use deterministic/attested evidence appropriate to each capability. WO-0008 defines the authority boundary but does not claim live OpenCode Go capability probes have been executed with credentials.
