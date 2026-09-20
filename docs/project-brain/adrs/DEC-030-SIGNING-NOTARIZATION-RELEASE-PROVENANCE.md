# DEC-030 — Signing, Notarization, Release Provenance And Protected Release Workflow

**Status:** PROPOSED / NOT CANONICAL — this Decision has no canonical force whatsoever while `HCODER-WO-0026` is unreviewed; it becomes eligible for promotion only through the governed closeout of that Work Order, and nothing in this file promotes itself  
**Work Order:** `HCODER-WO-0026` — candidate implementation in a Draft PR, never merged by its executor  
**Issue:** `#85`  
**Parent epic:** `HCODER-DIST-001` / Issue `#72`  
**Slice:** `HCODER-DIST-001C`  
**Canonical base:** `HCODER-CP-0025` / `1a56224eeb9bc07f032df1ede23bdda9d74f8d12`  
**Predecessor decision:** `DEC-029` — CANONICAL / SEALED, which froze artifact integrity and explicitly withheld everything this proposal concerns  
**Ledger entry:** `docs/project-brain/10-DECISIONS-LEDGER.md` → `DEC-030`, carrying the same PROPOSED / NOT CANONICAL status; the ADR and the ledger entry are one decision recorded twice, and neither promotes the other  
**Materialised under:** `HCODER-WO-0026`; the canonical append-only authority and delta history for this Work Order lives in `.engineering/context-locks/HCODER-WO-0026.md`, and no terminal delta number or range is mirrored here.

> **Conditional non-effectiveness (must not be misread).** This is a proposal describing a trust model that the repository has not adopted. Citing it as though it were canonical would invert the promotion order this project exists to enforce: the Decision is promoted because reviewed, proven exact-head evidence already exists, never the other way round. Mutable review, gate, environment and secret state is external lifecycle evidence referenced by Issues #30 and #85 and by the closeout PR carrying the evaluated revision; it is deliberately not embedded here, because a pre-CI commit cannot contain its own future receipts. This ADR admits no signing, notarization, release, publication, updater or installation authority, is not evidence that any credential exists, and is not evidence that Hive Coder is signed, notarized, distributable or production-ready.

## Context

`HCODER-CP-0025` proved that Hive Coder can produce the declared six native package targets deterministically and bind them to a closed inventory whose digest means **byte identity and integrity for evidence transport**. That is the entire guarantee. A SHA-256 over bytes an attacker could also produce proves only that bytes are the bytes.

Reaching an installable release therefore requires four further guarantees that are routinely collapsed into the single word "signed", each with a different producer, a different verifier and a different failure mode. Separating them is the substance of this Decision:

| Guarantee | Question it answers | Who can verify it offline | Mechanism selected |
| --- | --- | --- | --- |
| Artifact integrity | Are these the bytes I was pointing at? | Anyone with the digest | `hive-package-inventory-v1` (already canonical, `DEC-029`) |
| Build provenance | Which build, from which source, produced these bytes? | Anyone with the attestation bundle and a trusted root | GitHub artifact attestation (SLSA provenance, Sigstore public-good instance, OIDC-minted) |
| Publisher authenticity | Which legal publisher stands behind this binary, per the operating system's own trust rules? | The OS, at execution/install time | Windows Authenticode; macOS Developer ID `codesign` |
| Platform trust | Will the platform let a user run this without a warning? | The platform operator | macOS notarization + stapling; Windows publisher reputation |

Publication is a fifth, separate act: making artifacts and a tag immutably available under a gated authority. It carries none of the four guarantees by itself.

Two facts fix the honest ceiling for this repository today. First, the host state observed at source-check time contains **no** GitHub environment, **no** Actions secret and **no** variable: there is no signing identity of any kind, so nothing in this increment can be credentialed. Second, the operating systems do not offer symmetric guarantees — Linux offers no enforceable publisher trust for third-party desktop packages at all, so a policy that pretend otherwise would be a false claim rather than a weaker guarantee.

Toolchain facts below were verified against current official documentation on 2026-09-20 rather than assumed from repository memory or from circulating blog posts, because this slice's tooling has already changed once out from under common guidance:

- Apple has refused `altool` notarization uploads since 2023-11-01; `xcrun notarytool` is the notarization tool, and notarization requires a Developer ID Application certificate, Hardened Runtime and a secure timestamp, with the ticket stapled to the `.app` and the `.dmg` (not to a ZIP).
- Microsoft renamed "Azure Trusted Signing" to **Azure Artifact Signing**; the `trusign` / `Azure.CodeSigning.Cli` tool no longer resolves as an installable package, and the current paths are the official GitHub action or `signtool` driven by the Artifact Signing DLib plugin with a metadata file. Certificates are short-lived, so RFC 3161 timestamping is mandatory. Microsoft's own current guidance states that an EV certificate no longer bypasses SmartScreen, so the historical "buy EV" shortcut is not a trust argument. Public Trust certificate profiles are geographically restricted and Brazil is not on the published list, which is a real provisioning constraint on this project's owners, not a code defect.
- `actions/attest` v4 is the current attestation surface; `actions/attest-build-provenance` is a wrapper over it at v4. Minimum scopes are `id-token: write`, `attestations: write`, `contents: read` **and `artifact-metadata: write`**; v4 ships no in-workflow verify action, so verification is `gh attestation verify` with explicit policy flags. Public repositories use the public-good Sigstore instance at no additional plan cost. Attesting is not verifying: generation without a verification receipt is not a security success.
- Tauri 2.11 performs macOS signing, notarization and stapling itself from its own `APPLE_*` environment variables. Its `TAURI_SIGNING_PRIVATE_KEY` is a **minisign updater key**, unrelated to codesigning; treating one as the other is the single most likely way this project could produce a "signed" claim that means nothing. The updater is out of scope for this slice, so that variable is out of scope too.
- **GitHub does not fail a workflow that references an environment which does not exist: it creates that environment with no protection rules and no secrets, and the job runs unprotected.** Any claim that a release job "is protected" because its YAML names an environment is therefore false by construction.
- `Governance` runs the full discovered `tests/` suite, so this repository's gates are code, and a workflow file is configuration that a reviewer cannot execute. That asymmetry argues for putting as much release law as possible into the offline validator rather than into YAML.

## Decision candidate

**1. Four guarantees stay in four fields, and admission is per-field.** `hive-release-provenance-v1` records integrity, provenance, publisher signing and platform trust as distinct closed blocks. No rule may infer one from another: provenance verification can never satisfy a publisher-signing requirement, a publisher signature can never satisfy notarization, and a digest can never satisfy either. Where a platform genuinely lacks the guarantee, the field's honest value is `not-applicable` with a stated reason, not a borrowed substitute.

**2. Release evidence descends from CP-0025 evidence; no second packaging model is created.** Every provenance document binds the SHA-256 of the canonical serialization of the exact `hive-package-inventory-v1` document it describes, plus that inventory's `sourceSha`, `canonicalVersion`, `platform` and `architecture`. Tampering with upstream packaging evidence therefore changes or breaks the downstream binding instead of silently surviving it. The six-target matrix and the split-build/overlay law are inherited unchanged.

**3. The contract is deterministic and timestamp-free.** No wall-clock field appears in the document, so a receipt cannot age into a different claim and the same facts always serialize identically. Timing is carried by the signature timestamp authority and the transparency log, externally, and is referenced only by opaque identity fields.

**4. Closed schema enforced in code, in the repository's existing idiom.** Exact ordered key tuples, one exception type, `additionalProperties`-style refusal of unknown keys, canonical serialization, and refusal of duplicate identity pairs before any comparison — mirroring `package_inventory.py`. No JSON Schema library is introduced and no new dependency is admitted, because the governed Python lock admits only `dulwich`.

**5. Signing state is a closed ladder with an admission rule, not an adjective.** `unavailable` → `unsigned-candidate` → `signed` → `verified`, where `verified` additionally requires an independent verification result and public identity metadata (certificate fingerprint/subject, timestamp authority identity), never private material. A regression or a skip is refused by the transition law. Only `verified` can ever contribute to a publication admission, and `unsigned-candidate` must carry `releasedDigest == unsignedDigest`: bytes that changed without an accounting are tampering, not an unsigned release.

**6. Attestation state is likewise closed, and its verification is mandatory for any claim.** `unavailable` → `generated` → `verified`, with `verified` requiring the bundle digest, signer workflow identity, source ref/run identity and a passed verification result. A workflow step may generate an attestation; only a verification step may raise the state.

**7. Notarization applies to macOS only, as its own state machine.** `not-applicable` (Windows, Linux), `pending`, `stapled`, `verified`, `failed`. `stapled` or `verified` requires prior real signing, and `verified` requires an independent verification result. A stapled ticket on an unsigned or unnotarized bundle is a contradiction the validator refuses.

**8. Publication is a separate act with a separate gate, and this slice performs none.** `not-published` → `staged` → `published`. The `published` state records a completed release and pins the exact immutable release identity, tag and artifact-set digest; a publication claim whose artifact set does not hash to that identity is refused as fabricated. Admission is the gate's separate decision, and it reads attestation verification on every platform, publisher signing exactly where the platform has a publisher-trust model, and platform trust on macOS — so a Linux release may honestly be recorded as published while holding `unsigned-candidate` signing, which is the truth rather than a relaxation. Encoding signing or attestation inside the publication state would be the very substitution the separation law forbids, and would make Linux permanently unpublishable. The candidate workflow leaves this stage disabled, and no tag or GitHub Release is created from the Draft PR.

**9. Protection is an observed property, never a declared one.** Any job that touches a credential or publication authority must depend on a runtime probe of the named environment's actual protection semantics: that the environment exists, that its `protection_rules` contain a `required_reviewers` rule with at least one reviewer, and that administrators cannot bypass it — because an admin-bypassable gate is not a gate for a solo-owner repository. Where the probe cannot prove protection, the pipeline fails closed. Referencing an undefined environment is prohibited as evidence, precisely because GitHub silently creates it unprotected.

**10. Credential selection is deferred honestly, and least-privilege is fixed now.** The mechanism is chosen where the identity is actually held: OIDC-federated Azure Artifact Signing is the preferred Windows publisher path because it needs no long-lived secret, with traditional `signtool` plus a PKCS #12 as the fallback that must be recorded as the weaker option; macOS uses a Developer ID Application certificate with `notarytool` and stapling; provenance uses GitHub artifact attestation with mandatory verification; Linux uses no OS publisher trust and instead records provenance plus, optionally, a detached signature whose limits are stated. What is *not* deferred: the permission scopes, the trigger law, the isolation of credential-bearing jobs, and the prohibition on `pull_request_target` are decided here and are enforceable now.

**11. Linux's authenticity claim is written as a limit, not a triumph.** For `.deb`, apt verifies the repository `Release` file and checks each package by checksum; embedded `.deb` signatures exist (`debsig-verify`) but are not consulted at install time and are documented as not widely used. For AppImage, an embedded GPG signature can be produced, but the runtime does not validate it. Therefore the Linux release claim is exactly: **artifact integrity plus build provenance, optionally plus a detached Sigstore `cosign` blob bundle that a user must explicitly choose to verify with network access to the transparency log.** It is not publisher authenticity, and the contract's schema makes that impossible to overstate, because a Linux entry cannot enter a publisher-authenticity state at all.

**12. Absent credentials are a reported blocker, never a downgrade.** A missing signing identity produces `unavailable` plus an external blocker naming the credential class, the documented slot and the exact verification condition. It never produces unsigned publication, never reduces the matrix, and never converts `UNKNOWN` into `PASS`.

## Non-decision

This Decision does not select a certificate vendor, account, price tier or legal entity, does not assert that any credential exists, does not adopt the updater plugin or any update endpoint, transport, UI, install, restart or rollback behaviour (those are `HCODER-DIST-001D`…`G`), does not grant any product runtime capability, does not authorize any GitHub environment/secret/ruleset change, does not enable immutable releases, and does not declare Hive Coder releasable or production-distributable.

## Security law carried by this proposal

1. Integrity, provenance, publisher authenticity, platform trust and publication are distinct claims; a document or a person may not use one to satisfy another.
2. A digest is byte identity, never publisher authenticity.
3. Performing an operation is not evidence that it succeeded; signing, notarization and attestation each require an independent verification result.
4. The validator is an admission authority, not a claim-minting authority; its emit path can produce honest credential-free baseline state and structurally cannot emit `signed`, `verified` or `published`.
5. No secret value may be printed, echoed, persisted, committed, uploaded as an ordinary artifact, exposed in a command trace, stored in a fixture, written into a provenance manifest, or placed in HIVE, a PR body or an Issue body.
6. `pull_request_target` and any equivalent untrusted-code credential path is prohibited.
7. Permissions are scoped at job level; `id-token`, `attestations`, `artifact-metadata` and `contents: write` are granted only to the one job that needs each, only on the promotion path.
8. Short-lived OIDC identity is preferred over a long-lived cloud credential wherever the selected service supports it.
9. Environment protection must be probed, and `can_admins_bypass` is part of the probe.
10. Only public, independently verifiable identity metadata (fingerprint, subject, timestamp authority, signer workflow, bundle digest) may be recorded.
11. The contract is timestamp-free and deterministic.
12. Every guard must be demonstrated non-vacuous by a failing test when removed.
13. A credential that a platform's admission rule requires, and that is missing, fails closed; publishing artifacts the gate denies is not an acceptable fallback. Linux is the documented case where no publisher credential exists to be missing at all, so its admission rule (provenance plus integrity) is applied as written — neither relaxed to look stricter nor inflated with a signature the platform would not consult.
14. Nothing here expands `Capability.GIT_WRITE`, `Capability.FILESYSTEM_WRITE`, the control plane or the desktop security gate; CI release authority is not product runtime authority.

## Promotion gate

| Condition | Requirement |
| --- | --- |
| Decision materialized before credential access | `DEC-030` and the Work Order/Context Lock exist and are internally consistent before any secret is requested, read, referenced by value, decoded, imported or configured |
| Four-way separation enforced in code | Contract plus validator keep integrity, provenance, publisher signing and platform trust as separate closed blocks, with attestation unable to satisfy signing |
| Adversarial coverage | Every refusal in the acceptance map has a test that fails when the guard is removed: tampered digest, source, version or channel, fabricated signing/notarization/attestation/publication state, duplicate or extra entry, traversal or absolute path, package-set mismatch, impossible transition, provenance-as-signing substitution |
| CP-0025 preservation | Six-target matrix, split-build, ephemeral non-tracked overlay law, canonical config immutability and inventory contract inherited unchanged and unweakened |
| Workflow assurance | Least-privilege permissions, no secret-bearing job on `pull_request`, exact-SHA preflight, isolated per-OS signing stages, attestation generation **and** verification, objective environment probe, separately gated publication, no updater/install/restart/rollback surface |
| Hosted exact-head gates | `Governance`, `Desktop Shell`, `Native Package Matrix` and the new `Protected Release` lane green on the candidate head; a credentialed native job that cannot run is recorded `UNKNOWN`/`BLOCKED`, never `PASS` |
| Independent review | HEDS on the exact candidate head with unresolved HIGH/CRITICAL `0/0`, not issued by the executor |
| Governed merge | Expected-head-protected merge and a checkpoint delta promoted only after review; no self-promotion, and no canonical `CP-0026` claim before that |
| External provisioning (out of repository control) | A Windows publisher identity, a macOS Developer ID plus notarization credential, and a protected release environment with enforced non-bypassable required reviewers; until each exists and is proven, publication remains disabled |

Until the last row is satisfied by evidence rather than intent, the maximum honest status of this Decision is PROPOSED, and the maximum honest status of any artifact produced under it is unsigned internal evidence.
