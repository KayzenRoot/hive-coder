# Evidence Bundle — HCODER-WO-0012

**Risk:** ELEVATED  
**Base:** `f2db05d4b8d9a5b3cee54c22e325863ed2bfa748`

## Required invariants
- RepoDNA is read-only and never imports or executes repository code.
- Repository snapshots are deterministic, content-bound and fail closed on configured resource ceilings.
- Secret-like files, symlinks and common binary artifacts are not silently promoted into authoritative text context.
- TruthWeave trust is reproducible from exact snapshot/file/rule/fact identity; copied provenance cannot bless altered facts.
- GenomePulse invariants bind verified repository facts and explicit Digital Twin node/path bindings.
- ShadowBench oracle identity is host-keyed and model-visible case objects contain no plaintext oracle.
- New IDs/epochs/trivial mutations over one source lineage cannot fake benchmark novelty.
- Counterfactual Forge creates probes without mutating repository source.
- Production certification remains `DISTINGUISHED` and exact-profile/exact-standard/exact-repository bound.
- Competence Half-Life makes stale evidence due/expired under deterministic policy.
- Changed execution stack/profile fingerprint cannot reuse older certification.
- Outcome Echo may force re-certification but cannot mint competence evidence or promotion.
- Expertise Capsule extensions remain descriptive and contain no permission/rank authority.
- Existing CP-0005/0007/0008/0009/0010/0011 authority boundaries remain unchanged.

## Deterministic evidence target
RepoDNA path/symlink/secret/no-exec/resource/determinism tests; TruthWeave provenance/tamper/content-change tests; GenomePulse verified-fact/drift tests; ShadowBench deterministic hidden-case/tamper/novelty tests; Counterfactual Forge binding tests; Recertification Clock freshness/snapshot/stack/rank tests; Outcome Echo seal/advisory tests; broad Linux regression; unchanged Windows HIGH_ASSURANCE regression.

## HEDS target
Search for filesystem escape, symlink traversal, secret leakage, arbitrary code execution during indexing, unstable snapshots, provenance spoofing, model-visible hidden oracle, benchmark replay or cosmetic novelty, stale snapshot/stack certification reuse, positive outcome self-promotion, language/framework extension authority creep and any path that weakens CP-0011 Distinguished floors. UNKNOWN is not PASS.
