# Provider Certification Lab & Semantic Repository Twin

`HCODER-WO-0013` extends HCODER-CP-0012 with a static semantic repository twin and a HIGH_ASSURANCE exact-stack provider certification laboratory. Neither surface grants execution authority.

## Semantic Repository Twin

The twin is compiled from RepoDNA content without importing or executing repository code.

Hive-native components:
- **SchemaSense**: conservative JSON/TOML schema-shape observations.
- **APIVein**: static Python HTTP-style decorator route observations.
- **Dataflow Echo**: local Python read/write observations, explicitly not dynamic taint analysis.
- **Dependency Cortex**: bounded traversal over the semantic graph for impact/context reasoning.
- **Semantic Twin Drift**: deterministic node/edge change detection across repository snapshots.

The twin fingerprints the exact RepoDNA repository snapshot plus immutable semantic nodes/edges. Nodes include files, modules, symbols, external dependencies, unresolved symbol references, API-route observations, schema/property shapes and conservative dataflow symbols. Edges include defines, contains, imports, calls, exposes, declares, reads and writes.

Repository semantics remain descriptive evidence. A graph edge cannot create a permission, capability, trusted benchmark result or architecture/security decision by itself. APIVein may observe framework-like decorators conservatively, and Dataflow Echo is not runtime or taint analysis.

## StackGenome

`ExecutionStackDescriptor` is the canonical execution-stack DNA. Its fingerprint covers provider, model, exact model-revision digest, toolset, Expertise Capsule, skillset, Hive runtime and StackGenome protocol version. A production lab trial is rejected unless that fingerprint exactly equals the HMAC-sealed Agent Profile `execution_stack_digest` and the descriptor capsule fingerprint equals the profile capsule fingerprint.

This prevents competence evidence from silently migrating when the model, tools, skills, capsule or runtime materially changes.

## SuiteLineage Authority

An `EvaluationSuite` is HMAC sealed with suite/version, family label, **independence root**, generator identity/version and protocol digest. CP-0011 competence-family diversity is derived from the sealed independence root, not the human-friendly family label.

Renaming the same evaluation lineage, changing its displayed family or versioning the same lineage cannot manufacture additional benchmark-family diversity.

## Provider Certification Lab

The laboratory separates four duties:
1. the trusted Hive host seals identities, suites and exact StackGenome/trial contracts;
2. a provider runner receives only model-visible trial material;
3. an independent blind grader evaluates the response using host-side oracle material;
4. trusted evidence authorities seal TrialReceipt, EvidenceDNA and certification reports.

### EndpointSeal and independent actors

`LabActor` identity is HMAC sealed and binds role, independence lineage and `endpoint_digest`. Runner and grader must be different roles, different logical lineages and different endpoint digests. The same runtime object cannot act as both endpoints in one trial.

This is stronger than merely naming two prompts "runner" and "reviewer".

### StackSeal

`StackSealAuthority` binds a trial to:
- exact sealed Agent Profile;
- exact StackGenome;
- provider/model identity;
- exact repository snapshot;
- exact Semantic Repository Twin;
- benchmark dimension;
- exact SuiteLineage;
- exact ShadowBench case;
- exact runner/grader identities;
- evaluation protocol.

Unknown or tampered identity fails closed.

### TrialForge and oracle boundary

`TrialForge` verifies the ShadowBench case plus repository/twin bindings before materializing a bounded provider-visible task. `TrialMaterial` contains the trial fingerprint, prompt and prompt digest only. It contains no oracle digest or host secret.

The oracle digest enters only the host-side `BlindGradePacket` after provider execution.

### One-Shot Trial Law

A hidden trial lineage is atomically reserved in `DurableAttestationJournal.reserve_once()` **before** provider execution. The reservation key binds profile + StackGenome + hidden-case lineage.

The reservation is consumed even when provider execution, grading or GradeProof later fails. This prevents repeated attempts at one hidden case from being used to fish for a favorable answer.

Reservation is thread-safe/atomic within one process. Cross-process or distributed trial reservation is explicitly not approved in CP-0013.

### GradeProof

Every `GradeDecision` requires a SHA-256 `rationale_digest`. A bare boolean pass/fail cannot become a TrialReceipt. Provider incident counters are validated and provider response material has a 4 MiB ceiling.

The GradeProof digest is evidence identity, not permission authority and not a substitute for future richer grader provenance.

### Contamination Radar

Known exposure fingerprints block a trial. Contamination Radar has no API that increases success count, confidence or competence rank. Suspicion only reduces trust.

## Durable chronology

`DurableAttestationJournal` is an HMAC-authenticated append-only logical journal with a hash chain, bounded entry count and atomic file replacement. A host-injected `MonotonicAnchor` stores a trusted minimum sequence outside the journal. On restart, an older but otherwise correctly signed journal is rejected when its sequence is below the external floor.

`DurableChronoSealClock` persists monotonic logical epochs through this journal.

The monotonic anchor in CP-0013 is a host contract. CI uses a deterministic mock. A production deployment still needs an independently reviewed OS secure-store, TPM, remote attestation service or comparable monotonic authority.

## EvidenceDNA

A CP-0011 `BenchmarkResult` alone intentionally does not contain repository/twin fields. Therefore WO-0013 never treats a naked BenchmarkResult as portable certification evidence.

`LabBenchmarkEvidence` is Hive's **EvidenceDNA Envelope**. It HMAC-binds:
- the complete CP-0011 BenchmarkResult fingerprint;
- exact StackGenome fingerprint;
- exact repository snapshot;
- exact Semantic Twin fingerprint;
- exact SuiteLineage fingerprint.

TrialReceipts carry the same DNA. `BenchmarkAttestationAuthority` aggregates receipts only when all DNA fields match and returns a sealed EvidenceDNA envelope.

`ProviderCertificationLab.evaluate_and_certify()` accepts EvidenceDNA envelopes, verifies their HMACs and requires them to match the current exact profile, StackGenome, repository snapshot and Semantic Twin before the ExperienceRouter sees the underlying BenchmarkResults.

This prevents the **benchmark transplant** failure mode where valid evidence from repository state A is reused to certify repository state B.

## Auditable certification report

Only an exact stack that satisfies the irreducible CP-0011 `DISTINGUISHED` standard can reach CP-0012 Certification Authority. The final `AuditableCertificationReport` is sealed and binds:
- exact Agent Profile;
- exact competence report;
- exact CP-0012 certification evidence;
- exact repository snapshot;
- exact Semantic Repository Twin;
- exact EvidenceDNA envelope fingerprints;
- Durable ChronoSeal epoch.

WO-0013 does not claim any real provider/model stack has earned this status. Hosted CI uses deterministic mock runner/grader objects and contains no production provider credentials.

## Trust map

```text
RepoDNA
  |
  v
Semantic Repository Twin
  |         \
  |          -> Dependency Cortex / Drift
  v
ShadowBench hidden case
  |
  +--> SuiteLineage Authority
  |
  v
StackGenome + StackSeal
  |
  +--> EndpointSeal runner
  +--> EndpointSeal grader
  |
  v
One-Shot Trial Reservation
  |
  v
TrialForge ---- oracle remains host-side
  |
  v
Provider Runner
  |
  v
response
  |
  +------> Blind Grader + GradeProof
              |
              v
        sealed TrialReceipt
              |
              v
      Benchmark Attestation
              |
              v
        EvidenceDNA Envelope
              |
              v
      CP-0011 Experience Ledger
              |
              v
        measured competence
              |
              v
      CP-0012 Certification Authority
              |
              v
    Auditable Certification Report
```

All execution permissions remain subordinate to the existing Hive permission, capability, planning and runtime control planes.
