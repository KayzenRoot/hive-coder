# Repository Intelligence & Elite Evaluation Runtime

`HCODER-WO-0012` turns CP-0011's expert-agent certification machinery into a repository-aware and time-aware system. All components are descriptive/evaluative. None grants permissions, capabilities, permits, credentials or desktop authority.

## RepoDNA

**Purpose:** create a deterministic structural fingerprint of a repository without importing or executing repository code.

Properties:
- read-only text-file indexing;
- secret-like files and common binary artifacts excluded by default;
- symlinks are not followed;
- path traversal is rejected;
- file-count, per-file and total-byte ceilings fail closed;
- exact content SHA-256, language and file-kind metadata are captured;
- snapshot fingerprint changes when indexed content or classification changes.

RepoDNA is intentionally not a build system. It does not run package scripts, imports, tests, hooks or manifests.

## TruthWeave

**Purpose:** derive Code Truth facts from exact RepoDNA evidence.

TruthWeave currently extracts:
- exact file-content facts;
- Python import/dependency observations through `ast.parse` only;
- selected manifest dependency declarations from `package.json` and `pyproject.toml`.

Every generated fact is bound to:
1. the exact repository snapshot;
2. the exact file digest;
3. the extraction rule/version;
4. the fact predicate/object digest.

TruthWeave verifies facts by reproducing their expected fingerprint from the same indexed snapshot. Copying a provenance digest onto altered content does not make the altered fact trusted.

## GenomePulse

**Purpose:** mine architecture footprint invariants from verified repository facts plus the existing Project Digital Twin.

GenomePulse does not ask a model to invent architecture. A trusted host supplies node-to-path bindings. GenomePulse then binds each Digital Twin node to the exact verified facts underneath that repository prefix and produces `ArchitecturalInvariant` records. Any subsequent Code Truth or Digital Twin change can trigger deterministic genome drift.

## ShadowBench

**Purpose:** produce fresh hidden evaluation identities from the current repository rather than relying on a static public leaderboard.

ShadowBench uses a host-only key to deterministically select verified facts and create evaluation-case identities for dimensions such as debugging, architecture, testing, security, performance, code review, tool reliability and tamper resistance.

The runtime stores digests for prompts/oracles. It intentionally exposes no `oracle_text` field. A model/provider cannot self-verify its own benchmark result.

## Benchmark Novelty Ledger

A new case ID is not proof of novelty. The ledger rejects:
- exact case replay;
- semantic replay;
- trivial epoch/mutation churn over the same repository fact lineage.

This makes benchmark diversity depend on independent source lineages rather than cosmetic identifiers.

## Counterfactual Forge

**Purpose:** create architecture what-if probes without mutating source code.

A probe binds:
- repository snapshot;
- a verified Code Truth fact;
- a hypothetical replacement object digest;
- the GenomePulse invariants expected to drift.

The result is suitable for future hidden architecture/debugging tasks while keeping indexing side-effect free.

## Competence Half-Life & Recertification Clock

A `DISTINGUISHED` result is not immortal.

Certification evidence is bound to:
- exact sealed Agent Profile fingerprint, including execution-stack digest;
- exact Competence Standard fingerprint;
- exact repository snapshot;
- observation epoch;
- benchmark-family set.

The Recertification Clock returns:
- `CURRENT` while evidence is fresh and diverse;
- `DUE` after the warning age or negative operational feedback;
- `EXPIRED` after hard age limits, repository snapshot mismatch, missing evidence, stack/profile change or insufficient current benchmark diversity.

The clock can invalidate or demand re-certification. It cannot promote a rank.

## Outcome Echo

Operational outcomes are host-sealed and produce an **advisory-only** signal. Regressions/rollbacks may force earlier re-certification, but good production outcomes cannot mint trusted benchmark evidence or increase competence rank.

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
                Recertification Clock
                       |
                       v
                current / due / expired
```

Everything above remains subordinate to CP-0005 permission authority, CP-0007/0008 capability truth, CP-0009 execution truth, CP-0010 sealed planning/evidence and CP-0011 competence floors.
