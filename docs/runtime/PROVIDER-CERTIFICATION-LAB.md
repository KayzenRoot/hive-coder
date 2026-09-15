# Provider Certification Lab & Semantic Repository Twin

`HCODER-WO-0013` extends HCODER-CP-0012 with two new intelligence surfaces: a static semantic repository twin and a trusted exact-stack provider certification laboratory. Neither surface grants execution authority.

## Semantic Repository Twin

The twin is compiled from RepoDNA content without importing or executing repository code.

Hive-native components:
- **SchemaSense**: conservative JSON/TOML schema-shape observations.
- **APIVein**: static Python HTTP-style decorator route observations.
- **Dataflow Echo**: local Python read/write observations, explicitly not dynamic taint analysis.
- **Dependency Cortex**: bounded traversal over the semantic graph for impact/context reasoning.
- **Semantic Twin Drift**: deterministic node/edge change detection across repository snapshots.

The twin fingerprints the exact RepoDNA repository snapshot plus all semantic nodes/edges. Nodes include files, modules, symbols, external dependencies, unresolved symbol references, API routes, schema/property shapes and conservative dataflow symbols. Edges include defines, contains, imports, calls, exposes, declares, reads and writes.

Repository semantics remain descriptive evidence. A graph edge cannot create a permission, capability, trusted benchmark result or architecture decision by itself.

## Provider Certification Lab

The laboratory separates four duties:
1. Hive host seals identities and exact stack/trial contracts.
2. A provider runner executes only model-visible trial material.
3. An independent blind grader sees the response and host oracle digest but no provider/model identity.
4. Host evidence authorities seal trial/benchmark/certification reports.

### StackSeal
`StackSealAuthority` binds a trial to the exact sealed Agent Profile fingerprint and execution-stack digest, provider/model identity, repository snapshot, Semantic Twin, benchmark dimension/family, ShadowBench case, runner/grader identities and evaluation protocol.

Runner and grader identities are HMAC sealed and must use distinct independence lineages.

### TrialForge
`TrialForge` verifies the ShadowBench case and repository/twin bindings before creating a bounded model-visible task. Oracle material remains host-side; model output cannot mark itself correct.

### BlindGrader
The grader contract receives an opaque grade packet rather than provider credentials or provider identity. The host combines runner incidents and grader findings into a signed TrialReceipt.

### Contamination Radar
Known exposure fingerprints cause a block. Contamination Radar has no API that can increase successes, confidence or competence rank.

## Durable Chronology

`DurableAttestationJournal` is an HMAC-authenticated append-only logical journal. A host-injected `MonotonicAnchor` stores a trusted minimum sequence outside the journal. On restart, an older but otherwise valid signed journal is rejected when its sequence falls below the anchor floor.

`DurableChronoSealClock` persists logical epochs through this journal. The journal is intentionally generic; a production monotonic anchor may later be backed by an OS secure store, TPM, remote attestation service or another approved host mechanism.

## Benchmark and certification evidence

Sealed TrialReceipts can be aggregated by `BenchmarkAttestationAuthority` into CP-0011 `BenchmarkResult` objects. `ExperienceLedger` can therefore verify laboratory evidence without trusting provider prose.

A future exact stack that earns the irreducible `DISTINGUISHED` standard can pass through the CP-0012 Certification Authority and receive an `AuditableCertificationReport` bound to:
- exact Agent Profile / execution stack;
- exact competence report;
- exact certification evidence;
- exact repository snapshot;
- exact Semantic Repository Twin;
- exact benchmark-result fingerprints;
- ChronoSeal epoch.

WO-0013 does not claim any real provider/model stack has earned that certification. CI uses deterministic mocks and contains no production provider credentials.

## Trust map

```text
RepoDNA
  |
  v
Semantic Repository Twin
  |         \
  |          -> Dependency Cortex / Drift
  v
ShadowBench case
  |
  v
StackSeal + independent actors
  |
  v
TrialForge ---- oracle stays host-side
  |
  +----> Provider Runner
  |             |
  |             v
  |        response only
  |             |
  v             v
Host Oracle -> Blind Grader
       \        /
        v      v
       TrialReceipt
            |
            v
 Benchmark Attestation
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

All execution permissions remain subordinate to the existing Hive control planes.
