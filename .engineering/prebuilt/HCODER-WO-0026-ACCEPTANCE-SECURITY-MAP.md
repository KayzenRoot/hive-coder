# HCODER-WO-0026 — Acceptance & Security Map

**Status:** PROPERTY CONTRACT — every row is an executable obligation, not an execution status  
**Issue:** `#85`  
**Canonical authority history:** `.engineering/context-locks/HCODER-WO-0026.md`

Required negative proofs are the point of this slice. A row is satisfied only by a test or gate that fails when the guard is removed; the two non-vacuity sweeps named in the last section are the evidence that "fails when removed" was actually demonstrated rather than asserted.

## How to read this map

The **Implementation** column is a durable statement about the repository, not about any CI run or review outcome:

- `REQUIRED` — the property is an obligation of this slice, satisfied in source by the named test or gate and enforced whenever that lane runs.
- `EXTERNAL PROOF` — the property can only be demonstrated by hosted exact-head evidence: the lanes must actually run, produce, or refuse their declared targets on a named head.

**External promotion evidence is required for every row and is deliberately not encoded per row.** Hosted exact-head `Governance`, `Desktop Shell`, `Native Package Matrix` and `Protected Release` results, plus an independent review with unresolved HIGH/CRITICAL `0/0`, must each be produced against whichever exact head a promotion decision names. That mutable state lives in the active Draft PR and Issues #30 and #85; this map records the property and its evidence path, never a current PASS claim.

## Separation of the four guarantees

| # | Property the law must enforce | Test location | Implementation |
|---|---|---|---|
| S1 | A verified build-provenance attestation never clears a publisher-signing requirement on any platform | `test_release_provenance.GateTests`; `test_protected_release_workflow.ProvenanceStageTests.test_a_verified_attestation_never_clears_publisher_signing` | REQUIRED |
| S2 | macOS demands platform trust **in addition to** publisher signing; both reasons appear independently | `GateTests`; `ProvenanceStageTests` | REQUIRED |
| S3 | Linux is never charged for a signature its install path would not consult, and the lane fails if the gate invents one | `GateTests.test_linux_*`; `ProvenanceStageTests.test_linux_is_never_charged_for_a_signature_it_cannot_have` | REQUIRED |
| S4 | A package digest is never representable as signing, notarization or publisher authenticity | `SchemaClosureTests`, `StateMachineTests`, `test_protected_release_workflow.SigningBarrierTests` | REQUIRED |
| S5 | Publication is its own ladder and its own gate; a document that already claims publication cannot re-authorize itself | `StateMachineTests`, `TransitionTests` | REQUIRED |

## Contract and validator law

| # | Property the law must enforce | Test location | Implementation |
|---|---|---|---|
| C1 | Closed schema: unknown keys, missing keys, extra levels and unknown enum values are refused | `SchemaClosureTests` | REQUIRED |
| C2 | Ceilings are applied before parsing; an oversized input is refused, never truncated | `BoundAndShapeTests` | REQUIRED |
| C3 | Same facts, same bytes: canonical serialization is stable across producers and key orders | `BaselineDocumentTests`, `BindingTests` | REQUIRED |
| C4 | Downstream binding is the digest of the upstream inventory's canonical bytes; tampering breaks or changes it | `BindingTests` | REQUIRED |
| C5 | Each ladder refuses regression and skipping, and a state may only be raised by the step that proves it | `StateMachineTests`, `TransitionTests`, `LadderPrimitiveTests` | REQUIRED |
| C6 | The validator is an admission authority: no flag, mode or default can emit `signed`, `verified`, `stapled` or `published` | `OfflineLawTests`, `CliTests` | REQUIRED |
| C7 | The module reaches no network, credential, execution or filesystem-walking surface, read from its syntax tree rather than from a substring list, so prose and identifiers are not conflated | `OfflineLawTests.test_module_reaches_no_network_credential_or_execution_surface` | REQUIRED |
| C8 | No field in the contract can hold secret material, and no field holds a moment in time | `OfflineLawTests` | REQUIRED |
| C9 | Path law: absolute paths, traversal and symlink escape are refused in every package entry | `PathAndSetTests` | REQUIRED |
| C10 | Channel/version coherence follows `hive-release-channel-v1` exactly, case-sensitively | `ChannelCoherenceTests`, `CliTests` | REQUIRED |
| C11 | The surface scan is itself falsified: a module that does reach such a surface is reported, so a broken scan cannot read as a passing guard | `OfflineLawTests.test_the_surface_scan_reports_a_module_that_does_reach_one` | REQUIRED |
| C12 | An attestation's subjects are the inventory's package identities: names taken verbatim from the validated document, `sha256` digests it records, `sorted-tree` identity only for the directory package and `file-bytes` otherwise with both misdeclarations refused, and the 1024-subject ceiling applied | `AttestationSubjectTests` | REQUIRED |
| C13 | The subject set is compared as an exact whole: a missing package, an extra neighbour, a differing digest, a repeated name, an empty or non-list set, a statement that is not in-toto v1 and a predicate that is not build provenance are each refused, and `--attest-subjects` refuses to answer when either side is missing | `AttestationSubjectEvidenceTests`, `CliTests` | REQUIRED |

## Workflow admission law

| # | Property the law must enforce | Test location | Implementation |
|---|---|---|---|
| W1 | No `pull_request_target` or equivalent path; triggers read from the mapping, not from prose | `WorkflowStructureTests.test_a_trigger_is_read_from_the_trigger_mapping_not_from_prose` | REQUIRED |
| W2 | Repository-wide `contents: read`; exactly one job may write repository content | `LeastPrivilegeTests` | REQUIRED |
| W3 | `id-token`, `attestations` and `artifact-metadata` reach only the three attestation jobs; the signing and publication jobs hold none of them, and the scope a future signing executor needs is not granted early | `LeastPrivilegeTests.test_release_identity_permissions_reach_only_the_attestation_jobs`, `.test_signing_jobs_hold_no_write_and_no_oidc_authority` | REQUIRED |
| W4 | Every credential-bearing and publication job is `workflow_dispatch`-only, depends on the probe output, and no secret ever appears in a command line | `CredentialReachabilityTests` | REQUIRED |
| W5 | Signing authority and publication authority are different environments; build and probe jobs hold none | `CredentialReachabilityTests.test_signing_authority_and_publication_authority_are_different_environments` | REQUIRED |
| W6 | The PR-reachable jobs fetch nothing with a token | `CredentialReachabilityTests.test_pull_request_reachable_jobs_fetch_nothing_with_a_token` | REQUIRED |
| W7 | Protection is judged by the validator from a fetched record, and an absent environment is named as absent rather than forgiven | `EnvironmentProbeTests`, `EnvironmentProtectionTests` | REQUIRED |
| W8 | An unproven gate blocks the promotion path with a hard failure; YAML intent is declared non-evidence | `EnvironmentProbeTests.test_an_unproven_gate_blocks_the_promotion_path` | REQUIRED |
| W9 | Attestation is generated **and** independently verified in two proved transitions, over the canonical inventory bytes, and the lane then decodes the signed statement and proves its subject set equals the inventory's package set exactly — the subjects are derived from that document rather than discovered from the filesystem, and the manifest is never itself a subject | `ProvenanceStageTests.test_attestation_generation_and_independent_verification_are_different_steps`, `.test_the_attested_subjects_are_the_packages_not_the_manifest`, `.test_the_attested_subject_set_is_proved_equal_to_the_package_set`, `.test_the_subjects_are_derived_from_inventory_and_never_discovered` | REQUIRED |
| W10 | The six CP-0025 targets are not reduced, the canonical config is guarded after bundling, and the overlay is never uploaded | `PackagingPreservationTests` | REQUIRED |
| W11 | No produced package is installed, launched, registered or updated by any lane | `PackagingPreservationTests.test_nothing_installs_executes_or_updates_a_produced_package` | REQUIRED |
| W12 | Each signing stage ends in an unconditional refusal that does not depend on slot presence, after re-verifying the handed-over document | `SigningBarrierTests` | REQUIRED |
| W13 | Slot reporting is static text: class, mechanism, documented name and verification condition only, with no secret expression, no presence test and no indirect expansion, so "nothing was read" stays true after someone provisions a value | `SigningBarrierTests.test_slots_are_reported_as_class_name_and_condition_without_values` | REQUIRED |
| W16 | A signing stage executes nothing but the whitelisted offline verifier and literal echoes: no token-minting scope, no cloud login, no certificate or key import, no signing command, no environment inspection | `SigningBarrierTests.test_a_signing_stage_executes_only_the_whitelisted_verifier_and_literals` | REQUIRED |
| W14 | Publication requires an explicit opt-in defaulting to false, re-queries the gate per platform without tolerating failure, and requires a protected tag | `PublicationGateTests` | REQUIRED |
| W15 | The audit can only read: its own imports, calls and paths are constrained from the syntax tree | `NoSelfReferenceTests` | REQUIRED |

## Non-vacuity of the guards

| # | Property | Evidence | Implementation |
|---|---|---|---|
| N1 | Every validator guard fails a test when neutralized | guard-neutralisation sweep over `tools/desktop/release_provenance.py`, recorded in `.engineering/evidence/HCODER-WO-0026.md` | REQUIRED |
| N2 | Every workflow guard can fire | mutation sweep over `.github/workflows/protected-release.yml`, recorded in the same evidence file, with comment-only controls that must survive | REQUIRED |
| N3 | Each audit guard is paired with an in-test synthetic mutation of the same text | `test_protected_release_workflow.py` (every test method) | REQUIRED |

## Externally gated and never claimed here

- Whether a Windows or macOS signing stage ever executes successfully: **no credential exists**, and the stages refuse unconditionally by design.
- Whether either release environment exists or is protected: the probe answers that at run time; `gh api` against this repository at source-check time reported no environments, no secrets and no variables.
- Whether the substrate could reach a credential if one existed: it cannot, by construction. The provisioning map in `.engineering/prebuilt/HCODER-WO-0026-EXECUTOR-BRIEF.md` states the Entra application, federated credential, Artifact Signing account, certificate profile, profile-scoped signer role, timestamp authority, Apple certificate and App Store Connect API-key objects that would have to exist first — including the `id-token: write` grant that the signing slice must ask for explicitly rather than inherit from this one.
- Whether any release, tag or GitHub Release exists: this slice creates none.
- Hosted green/red of `Governance`, `Desktop Shell`, `Native Package Matrix` and `Protected Release` on any head, and any HEDS verdict.

## STOP

STOP rather than converting an `EXTERNAL PROOF` row into a `REQUIRED` claim, relaxing an assertion to stay green, or deleting a guard whose mutation was not killed without recording why.
