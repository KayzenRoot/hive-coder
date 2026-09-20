# Evidence Bundle — HCODER-WO-0026

**Status:** SECRET-INDEPENDENT SUBSTRATE COMPLETE — CANDIDATE IN A DRAFT PR, NOT PROMOTED
**Canonical base:** `HCODER-CP-0025` / `1a56224eeb9bc07f032df1ede23bdda9d74f8d12`
**Issue:** `#85`
**Parent epic:** `HCODER-DIST-001` / Issue `#72`
**Slice:** `HCODER-DIST-001C`
**Decision:** `DEC-030` — PROPOSED / NOT CANONICAL, with no canonical force while this Work Order is unreviewed
**Correction authority:** `HCODER-WO-0026`; the canonical append-only delta history lives in `.engineering/context-locks/HCODER-WO-0026.md`, and no terminal delta number or range is mirrored here.

> **What this bundle is.** A record of what the repository now contains and of what was proven on the local host. It embeds **no** hosted receipt, and no sentence here is evidence that any credential, GitHub environment, protection rule, certificate or notarization account exists. Where a claim depends on that external state it is placed in `## Claims requiring external exact-head evidence` and left `UNKNOWN`.

## Source-materialized claims

These describe the repository as it exists and do not change as evidence advances:

- `docs/project-brain/contracts/RELEASE-PROVENANCE-V1.md` defines `hive-release-provenance-v1`: four guarantees held apart (artifact integrity, build provenance, publisher authenticity, platform trust) plus publication, each with its own closed ladder and its own admission rule; the transition law; the channel-coherence law; canonical serialization; and the environment-protection admission law.
- `tools/desktop/release_provenance.py` (832 lines) is the validator: standard-library only, offline, non-mutating, one exception class, closed ordered key tuples, and six modes — `--build`, `--verify`, `--gate`, `--transition`, `--channel-gate`, `--environment-protection`. It is an admission authority, not a claim-minting authority: `--build` hardcodes the credential-free baseline and exposes no flag capable of producing a signing, notarization, attestation or publication claim.
- `.github/workflows/protected-release.yml` (1358 lines) materializes eight jobs in a fixed order — `preflight`, `probe-release-protection`, `build-attest-windows`, `build-attest-linux`, `build-attest-macos`, `sign-windows`, `sign-and-notarize-macos`, `publish` — with workflow-level `permissions: contents: read`, all 23 action references pinned to full commit SHAs, and no `pull_request_target` and no `workflow_run` trigger.
- `tests/desktop/test_release_provenance.py` (1358 lines, 14 classes) and `tests/desktop/test_protected_release_workflow.py` (948 lines) are materialized adversarial lanes; the second is a stdlib text-and-AST audit of the workflow file and needs no runner, no network and no credential.
- The CP-0025 substrate is consumed, not redefined: a provenance document binds to the real inventory through the SHA-256 of `serialize_inventory`'s canonical bytes, so tampering with upstream packaging evidence changes the binding rather than being papered over.
- The ledger carries a `DEC-030` entry marked PROPOSED / NOT CANONICAL (authorized by Context Lock Delta 001, pure append), and the `DEC-030` ADR points at that ledger entry in both directions so neither can be mistaken for promotion.
- `AGENTS.md` and `docs/project-brain/07-DEPLOYMENT.md` carry the bounded source-truth corrections the Context Lock allows: `AGENTS.md` no longer states `HCODER-CP-0022` as current execution state, and `07-DEPLOYMENT.md` no longer states packaging as merely `PLANNED`. Both defer to `11-CHECKPOINT.md` as the authority.

## Verification executed locally

| What | Exact command | Result |
| --- | --- | --- |
| Provenance contract lane | `python -m unittest tests.desktop.test_release_provenance` | `Ran 132 tests … OK` |
| Workflow structural lane | `python -m unittest tests.desktop.test_protected_release_workflow` | `Ran 42 tests … OK` |
| Both lanes together | `python -m unittest tests.desktop.test_release_provenance tests.desktop.test_protected_release_workflow` | `Ran 174 tests … OK` |
| Full discovered suite, final candidate content | `PYTHONWARNINGS=error::ResourceWarning python -m unittest discover -s tests -p "test_*.py"` | `Ran 779 tests … OK (skipped=58)` |
| Same suite at the canonical base `1a56224` | identical command | `Ran 605 tests … OK (skipped=58)` |

The delta is exactly `+174`, which is this Work Order's two lanes, with no pre-existing test altered, skipped or deleted; the 58 skips are the base's own and are unchanged.

## Non-vacuity proofs

A green adversarial suite is worth nothing if the guard it tests cannot fail. Two independent mutation campaigns were run, both driven from scripts kept **outside** the repository (the Context Lock authorizes exactly one new path in-lane), and both verified afterwards that the mutated file had been restored byte-identically (`RESTORED_OK True`).

### Campaign A — validator guard neutralization

Method: every `if` / `elif` condition in `tools/desktop/release_provenance.py` is replaced, one at a time, with a constant-false condition, and the provenance lane is re-run. A guard whose removal leaves the suite green proves nothing.

- First campaign: **119 candidates, 115 killed, 4 survivors.**
- Three of the four survivors were real gaps — a guard with no test behind it, not a wrong guard — and are closed on this head by a test plus one truthfulness fix:

| Line | Neutralized guard | Disposition |
| --- | --- | --- |
| 345 | `elif asset_set:` — a `staged` publication pinning an artifact set it has not released | closed by `test_staged_publication_may_not_pin_an_artifact_set_it_has_not_released` |
| 595 | `not isinstance(record, dict)` — a non-object environment record read as an empty, passing gate | closed by `test_a_record_that_is_not_an_object_is_the_wrong_shape_not_an_empty_gate` |
| 766 | `report.status != "LOCKED"` — a drifting or versionless source admitted to a channel | closed by `test_a_drifting_or_versionless_source_is_never_admitted_to_a_channel` and `test_a_locked_source_that_names_no_version_is_incoherent_too`, and by splitting the combined drift/no-version condition so each refusal prints its own true reason instead of one message covering two different failures |
| 831 | `if __name__ == "__main__":` | **accepted survivor** — a module-entry condition that carries no admission decision. Recorded rather than silenced or excluded from the count |

- Final campaign on the shipped source: **120 candidates, 119 killed, 1 survivor** — the accepted `__main__` condition.

### Campaign B — workflow structural mutation

Method: throwaway degradations of `.github/workflows/protected-release.yml` — removed `if:` guards, widened permissions, an unauthenticated job reaching a credential stage, a dropped `--verify` step, a `--gate` reordered before `--verify`, an unpinned action, a weakened barrier — each expected to be caught by the workflow audit lane.

- **28 mutants: 26 killed.** The two survivors are deliberate controls that must survive because they change no structure: `control-comment-only` (comment text edited only) and `control-reworded-prose`.
- Two mutants exposed **defects in the audit itself**, and both were fixed by making the audit stronger, never by relaxing an assertion:
  1. Keyword-based step detection let a comment line plus an echoed `ATTESTATION_VERIFICATION=PASSED` satisfy an attestation guard. The lane now reads commands (`command_lines`, `step_with_command`, `validator_invocations` with line-continuation joining) instead of scanning prose for words.
  2. A comment merely *naming* `--environment-protection` satisfied a mode guard. Every mode guard now reads resolved invocations only, so the flag must actually appear in a command.
- A third fix was in the workflow's own text: the install/execute prohibition is now stated in the verb forms the audit checks (`msiexec`, `Start-Process`, `dpkg -i`, `rpm -i`, `snap install`, `install hive`, `hdiutil attach`, `open -a`, `systemctl`, updater plugin) rather than the noun `installer`, which appears in preserved CP-0025 law about structural, non-installing validation and so could not be banned.

## Externally gated stages — never executable in this increment

Re-verified on the host at the time of writing, read-only, with no value read or printed: repository **visibility `public`**, **environments total `0`**, **repository Actions secrets total `0`**, **repository variables total `0`**. Consequences, each stated without values:

| Stage | Held back by | Would require |
| --- | --- | --- |
| `preflight` | nothing — designed to run secret-free as exact-head evidence | hosted execution on the candidate head |
| `build-attest-*` | an OIDC token mint and the hosted attestation service, neither of which a local run can reach | `actions/attest` over the canonical inventory manifest, with the verification condition that `gh attestation verify` succeeds against the returned bundle under `--signer-repo`, `--signer-workflow`, `--source-ref` and `--deny-self-hosted-runners` |
| `sign-windows` | no publisher identity of any kind | Azure Artifact Signing certificate profile reached by federated OIDC, slots `AZURE_ARTIFACT_SIGNING_ENDPOINT` / `AZURE_ARTIFACT_SIGNING_ACCOUNT` / `AZURE_ARTIFACT_SIGNING_CERTIFICATE_PROFILE`; verification condition: each package's signature verifies with an independent authenticode verification whose signer identity matches the recorded certificate subject and fingerprint. The `signtool` + PKCS #12 fallback is recorded in `DEC-030` as the weaker option and is not used here |
| `sign-and-notarize-macos` | no signing certificate, no notarization credential | Developer ID Application certificate plus App Store Connect API key for `notarytool`, slots `APPLE_SIGNING_IDENTITY` / `APPLE_CERTIFICATE` / `APPLE_CERTIFICATE_PASSWORD` / `APPLE_TEAM_ID` / `APPLE_API_KEY_ID` / `APPLE_API_KEY`; verification condition: `codesign --verify --strict --deep` passes and `xcrun notarytool information` reports Acceptance for the submitted artifact |
| `probe-release-protection` | no named environment exists, so no protection semantics exist | GitHub environments `hive-release-signing` and `hive-release-publish`, each with a `required_reviewers` rule carrying at least one reviewer, `prevent_self_review` true and `can_admins_bypass` false, so the probe prints `RELEASE_PROTECTION=PROTECTED` for a real record. An environment name alone is never protection, and GitHub silently creates a named-but-missing environment unprotected rather than failing |
| `publish` | the unimplemented-signing barrier below, plus absent release authority | dispatch with `publish_intended=true`, a probe-verified protected environment, and every gate green |

**The signing barrier is intentional and cannot be satisfied by provisioning alone.** `sign-windows`, `sign-and-notarize-macos` and the publication stage each reach an unconditional refusal step emitting `RELEASE_SUBSTRATE_STOPPED=BLOCKED_EXTERNAL_CREDENTIALS_AND_UNIMPLEMENTED_SIGNING`. This increment builds the admission law for signing, not the signing executor. Supplying credentials would therefore not turn those lanes green, which is the point: a later head that *does* claim signing must add the executor as its own governed change, and a reviewer can see that the refusal was designed rather than discovered.

## Claims requiring external exact-head evidence

Each holds only against a named exact head; that mutable state belongs to the Draft PR and Issues #30 and #85, never here:

- `Governance`, `Desktop Shell` and `Native Package Matrix` remain green and unweakened on the final candidate head. They were not modified, re-triggered or path-filtered by this Work Order.
- The new `Protected Release` lane's `preflight` job is green on that head, including its `--environment-protection` adjudication of a record it fetches unauthenticated, and its refusal when the named environment has no enforced protection.
- The credential-bearing and publication stages are `UNKNOWN` / `BLOCKED` on that head and are never reported as passing.
- An independent HEDS review of that head returns unresolved HIGH/CRITICAL `0/0`, and a governed expected-head merge completes. The executor may not issue, and does not issue, any of these.

## Claims never admitted by this slice

- That any package is signed, notarized, stapled, trusted, published, installable or production-distributable.
- That the `Protected Release` lane is green, or that any release job is protected. No credential, environment, protection rule or notarization account was proven to exist, and `DEC-030` is explicitly not evidence that one does.
- That a build-provenance attestation, an inventory digest or a `REASON=`-printing gate substitutes for publisher authenticity on Windows or macOS. The workflow prints positive `SEPARATION_PROOF=` markers on Windows and macOS precisely because the substitution is the failure mode this slice exists to prevent.
- That this increment created a tag, a GitHub Release, an environment, a secret, a variable, an application, a certificate or an account. It created none, and no such creation was attempted.
- That Linux has an enforceable OS publisher-trust model. `NO_PUBLISHER_TRUST_PLATFORMS` skips the signing and platform-trust requirements there rather than faking them, and that skip is an honest absence, not a pass.
- That `HCODER-CP-0026` exists, that `DEC-030` carries canonical force, or that `HCODER-DIST-001D`-`G` (updater, endpoint, update UI, rollback, install end-to-end) were touched. They were not.

## Known deferrals and design boundaries

- **Attestation identity is document-level.** `actions/attest` is pointed at the canonical inventory manifest — the document every package digest in the release descends from — and the `attestation` block records one verified bundle identity per release document: `signerWorkflow`, `sourceRef`, `runId`, `bundleDigest`. Package-level trust is carried separately by `packages[].signing` and `packages[].notarization`. Per-package attestation subjects are not modelled, so a reviewer who wants a distinct attestation identity per artifact must treat that as a contract extension, not as a capability already present.
- **The `signing.identity` triple is structurally validated but not yet populated by any executor**, since no executor exists in this increment. Its immutability law (a certificate identity, once asserted, may not be swapped) is enforced and tested today so the first real signing stage cannot quietly change hands mid-release.
- **`environment-protection` adjudicates a record; it does not fetch one.** Keeping the validator offline and free of any network or token dependency was chosen over convenience: the workflow supplies the record, and the tool decides. The trust that the supplied record is genuine is therefore hosted-lifecycle evidence, and is listed above as such rather than assumed.

## Base-state facts to re-verify

Mutable external state decays. Re-read live before relying on any of these:

- `gh api` for `repos/…/environments`, `…/actions/secrets`, `…/actions/variables` — all zero at the time of writing.
- Repository visibility is `public`, which is the precondition for artifact attestation at no cost.
- Pinned toolchain inherited from CP-0025: `@tauri-apps/cli` 2.11.4, Node 24.21.0, Rust 1.98.1, and the six-target package matrix.
- `apps/desktop/src-tauri/tauri.conf.json` remains byte-unchanged by this Work Order with `bundle.active = false`.

## Promotion evidence template

For each exact technical head record: commit SHA; `Governance`, `Desktop Shell`, `Native Package Matrix` and `Protected Release` run and job IDs; whether `preflight` passed and what it adjudicated for each named environment, with `RELEASE_PROTECTION=` and `UNPROVEN_BECAUSE=` values; the per-lane `SEPARATION_PROOF=` markers actually emitted; HEDS unresolved HIGH/CRITICAL counts; and for any credentialed stage that ran, the credential class and verification condition only — never a value.

## STOP

`UNKNOWN` never becomes `PASS`. Exact-head evidence proves only the exact SHA it names, and a new head invalidates the old head's receipts. Mutable hosted receipts are recorded externally, never in this bundle. If external setup is required, report the credential class, the provider or mechanism, the documented slot name and the exact verification condition — never a value, and never a request for one. A missing secret is never a reason to downgrade to unsigned publication, and no green result obtained by weakening a gate, a guard or a test counts as a result. Canonical standing for this Work Order is determined only by its governed closeout, and this increment neither claims it nor can grant it.
