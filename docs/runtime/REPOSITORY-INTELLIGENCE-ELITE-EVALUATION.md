# Repository Intelligence & Elite Evaluation Runtime

`HCODER-WO-0012` turns CP-0011's expert-agent certification machinery into a repository-aware and time-aware system. All components are descriptive/evaluative. None grants permissions, capabilities, permits, credentials or desktop authority.

## RepoDNA

**Purpose:** create a deterministic structural fingerprint of a repository without importing or executing repository code.

Properties:
- read-only UTF-8 text indexing;
- known secret-like filenames and common binary artifacts excluded by default;
- root/file symlinks are rejected or skipped and repository symlinks are never followed intentionally;
- canonical relative paths and root containment are enforced;
- safe regular-file opening uses no-follow semantics where the platform exposes them, plus `fstat` and bounded reads;
- file-count, per-file and total-byte ceilings fail closed;
- exact content SHA-256, language and file-kind metadata are captured;
- snapshot fingerprint changes when indexed content or classification changes.

RepoDNA is intentionally not a build system. It does not run package scripts, imports, tests, hooks or manifests. Filename filtering is defense in depth, not a claim that every possible secret can be detected by name.

## TruthWeave

**Purpose:** derive Code Truth facts from exact RepoDNA evidence.

TruthWeave currently extracts:
- exact file-content facts;
- Python import/dependency observations through `ast.parse` only;
- selected manifest dependency declarations from `package.json` and `pyproject.toml`.

Every generated fact is bound to the exact repository snapshot, exact file digest, extraction rule/version and fact predicate/object digest. TruthWeave verifies facts by reproducing their expected fingerprint from the same indexed snapshot. Copying a provenance digest onto altered content does not make the altered fact trusted.

## GenomePulse

**Purpose:** mine architecture footprint invariants from verified repository facts plus the existing Project Digital Twin.

GenomePulse does not ask a model to invent architecture. A trusted host supplies canonical node-to-path bindings. GenomePulse binds each Digital Twin node to the exact verified facts underneath that repository prefix and produces immutable `ArchitecturalInvariant` relationships. Any subsequent Code Truth or Digital Twin change can trigger deterministic genome drift.

## ShadowBench

**Purpose:** produce fresh hidden evaluation identities from the current repository rather than relying on a static public leaderboard.

ShadowBench uses a host-only key to deterministically select verified facts and create evaluation-case identities for dimensions such as debugging, architecture, testing, security, performance, code review, tool reliability and tamper resistance.

The runtime stores digests for prompts/oracles. It intentionally exposes no `oracle_text` field. Verification recomputes lineage, nonce, prompt digest, oracle digest and case identity from trusted factory state and verified Code Truth.

## Benchmark Novelty Ledger

A new case ID is not proof of novelty. Before recording a case, the ledger requires an injected trusted case verifier. It then rejects:
- exact case replay;
- semantic replay;
- trivial epoch/mutation churn over the same repository fact lineage.

This makes benchmark diversity depend on verified independent source lineages rather than cosmetic identifiers. The novelty ledger is session-bounded in CP-0012; durable cross-restart novelty attestation belongs to the future Provider Certification Lab.

## Counterfactual Forge

**Purpose:** create architecture what-if probes without mutating source code.

A probe binds the repository snapshot, a verified Code Truth fact, a hypothetical replacement object digest and the immutable GenomePulse invariants expected to drift. The result is suitable for future hidden architecture/debugging tasks while keeping indexing side-effect free.

## ChronoSeal

**Purpose:** prevent callers from fabricating certification freshness.

`ChronoSealClock` is a trusted-host logical epoch that moves only forward within the runtime instance. Certification and outcome authorities obtain observation epochs from ChronoSeal instead of accepting a caller-provided current time. CP-0012 deliberately keeps ChronoSeal session-bounded; durable cross-restart time attestation is future work and restart ambiguity therefore fails closed rather than silently extending certification.

## Certification Authority, Competence Half-Life & Recertification Clock

A `DISTINGUISHED` result is not immortal, and arbitrary objects cannot become certification evidence merely by containing the right fields.

The HMAC-SHA256 `CertificationAuthority` issues evidence only for a passing `DISTINGUISHED` report bound to:
- exact trusted-host sealed Agent Profile fingerprint, including execution-stack digest;
- exact Competence Standard fingerprint;
- exact competence-report fingerprint;
- exact repository snapshot;
- ChronoSeal observation epoch;
- benchmark families derived from measured report scores.

`RecertificationClock` verifies that authority seal before considering evidence. It returns:
- `CURRENT` while evidence is fresh and diverse;
- `DUE` after the warning age or negative operational feedback;
- `EXPIRED` after hard age limits, repository snapshot mismatch, missing evidence, stack/profile change or insufficient current benchmark diversity.

The clock can invalidate or demand re-certification. It cannot promote a rank.

## Outcome Echo

Operational outcomes are HMAC-sealed by a trusted-host `OutcomeAuthority`, and their epoch also comes from ChronoSeal. Outcome Echo produces an **advisory-only** signal. Regressions/rollbacks may force earlier re-certification, but good production outcomes cannot mint trusted benchmark evidence or increase competence rank.

This one-way design prevents a successful agent from laundering ordinary task outcomes into its own certification authority.

## Expertise Capsule Extensions

Language/framework extensions add versioned descriptive doctrine and benchmark dimensions to an existing capsule fingerprint. They contain no permission or competence field and have no automatic activation path.

## Authority boundary

```text
Repository files
     |
     v
RepoDNA  -- no exec
     |
     v
TruthWeave --> Code Truth Map
     |              |
     v              v
GenomePulse     ShadowBench
     |              |
     v              v
Architecture    trusted benchmark execution (future host path)
     |              |
     +-------> CP-0011 Experience Ledger
                       |
                       v
                measured competence
                       |
              Certification Authority
                       |
                 ChronoSeal epoch
                       |
                       v
                Recertification Clock
                       |
                       v
                current / due / expired
```

Everything above remains subordinate to CP-0005 permission authority, CP-0007/0008 capability truth, CP-0009 execution truth, CP-0010 sealed planning/evidence and CP-0011 competence floors.
