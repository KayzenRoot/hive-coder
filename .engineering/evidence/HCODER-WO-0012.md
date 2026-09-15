# Evidence Bundle — HCODER-WO-0012

**Risk:** ELEVATED  
**Base:** `f2db05d4b8d9a5b3cee54c22e325863ed2bfa748`

## Required invariants
- RepoDNA is read-only and never imports or executes repository code.
- Repository snapshots are deterministic, canonical-path/content-bound and fail closed on configured resource ceilings.
- Known secret-like files, symlinks and common binary artifacts are not silently promoted into authoritative text context.
- TruthWeave trust is reproducible from exact snapshot/file/rule/fact identity; copied provenance cannot bless altered facts.
- GenomePulse invariants bind verified repository facts and explicit Digital Twin node/path bindings; fact/invariant state is immutable after construction.
- ShadowBench oracle identity is host-keyed and model-visible case objects contain no plaintext oracle; verification recomputes lineage, nonce, prompt/oracle digests and case identity.
- Benchmark Novelty accepts only host-verified ShadowBench cases; new IDs/epochs/trivial mutations over one source lineage cannot fake novelty.
- Counterfactual Forge creates probes without mutating repository source.
- Production certification remains `DISTINGUISHED` and exact-profile/exact-standard/exact-report/exact-repository bound.
- Certification evidence is HMAC-sealed by the trusted host and obtains its observation epoch from monotonic ChronoSeal, never caller-provided freshness.
- Competence Half-Life makes stale evidence due/expired under deterministic policy.
- Changed execution stack/profile fingerprint cannot reuse older certification.
- Outcome Echo uses trusted-host sealed records and ChronoSeal epochs; it may force re-certification but cannot mint competence evidence or promotion.
- Expertise Capsule extensions remain descriptive and contain no permission/rank authority.
- ChronoSeal and novelty state are explicitly session-bounded in CP-0012; no durable cross-restart claim is made.
- Existing CP-0005/0007/0008/0009/0010/0011 authority boundaries remain unchanged.

## Deterministic evidence target
RepoDNA canonical-path/root-symlink/file-symlink/secret/no-exec/resource/immutability/determinism tests; TruthWeave provenance/tamper/content-change tests; GenomePulse verified-fact/drift/immutable-binding tests; ShadowBench deterministic hidden-case/full-identity/tamper/trusted-novelty tests; Counterfactual Forge binding tests; ChronoSeal monotonicity tests; Certification Authority seal/tamper/report-family tests; Recertification Clock freshness/snapshot/stack/rank tests; Outcome Echo seal/advisory tests; broad Linux regression; unchanged Windows HIGH_ASSURANCE regression.

## HEDS target
Search for filesystem escape, symlink race/traversal, secret leakage, arbitrary code execution during indexing, unstable/mutable snapshots, provenance spoofing, model-visible hidden oracle, forged ShadowBench lineage/case identity, unverified benchmark novelty, caller-controlled certification freshness, unsigned/tampered certification evidence, stale snapshot/stack reuse, positive outcome self-promotion, language/framework extension authority creep and any path that weakens CP-0011 Distinguished floors. UNKNOWN is not PASS.

## Correction evidence
`HCODER-WO-0012-CR-001` records the HIGH certification-freshness/integrity finding and related hardening. Closure requires a corrected exact-head Governance run and final HEDS verdict.
