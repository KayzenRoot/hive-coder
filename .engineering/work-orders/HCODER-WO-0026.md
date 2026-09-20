# HCODER-WO-0026 — Signing, Notarization, Release Provenance And Protected Release Workflow

**Status:** ACTIVE / CANDIDATE — PRODUCT IMPLEMENTATION IN DRAFT PR, NOT PROMOTED  
**Promotion law:** This Work Order is satisfied only against a named exact head. Canonical standing requires the governed closeout sequence: exact-head `Governance` + `Desktop Shell` + `Native Package Matrix` + the new `Protected Release` lane, an independent HEDS review with unresolved HIGH/CRITICAL `0/0`, an approved Checkpoint Delta, and a merge under repository policy with expected-head protection. No wording in this file promotes itself, and no green gate on an earlier head transfers to a later head.  
**Risk:** HIGH_ASSURANCE (release authority, code-signing identity, notarization, supply-chain provenance, CI permissions)  
**Task class:** T3  
**Context radius:** C4  
**Canonical base:** `HCODER-CP-0025` / `1a56224eeb9bc07f032df1ede23bdda9d74f8d12`  
**Decision:** `DEC-030` — PROPOSED / NOT CANONICAL while this Work Order is unreviewed  
**Issue:** `#85`  
**Parent epic:** `HCODER-DIST-001` / Issue `#72`  
**Slice:** `HCODER-DIST-001C`  
**Predecessor:** `HCODER-WO-0025` / `HCODER-DIST-001B` — Issue `#82` CLOSED / COMPLETED, `HCODER-CP-0025` and `DEC-029` CANONICAL / SEALED  
**Authorization:** Prompt 43. Prompt 42 sealed `CP-0025` and queued this Work Order as a governance pointer only; the queued Issue `#85` granted no implementation authority, and Prompt 43 is the first authorization to create the Work Order and begin `HCODER-DIST-001C`.

> **Scope of this record.** This file states the law of the increment. Whether a given head satisfies that law is mutable hosted evidence and lives in the active Draft PR and Issues #30 and #85, never here. `IMPLEMENTED` is not a promotion claim, and `UNKNOWN` never becomes `PASS`.

## Objective

Establish the release trust chain for Hive Coder's already-proven native packages without collapsing distinct guarantees into one label: source SHA → CP-0025 package evidence → build provenance → platform publisher signing and platform trust → separately gated protected publication. Materialize the secret-independent substrate for that chain — a closed deterministic release-provenance contract, an offline fail-closed validator, and a protected release workflow whose credential-bearing stages exist as provable structure rather than as YAML intent — and stop cleanly at the external credential boundary when the credentials or the protected environment that the design requires do not exist.

## Context

`HCODER-CP-0025` admitted deterministic unsigned native package evidence only. It produced the declared six-target matrix (Windows `msi`+`nsis`, macOS `app`+`dmg`, Linux `appimage`+`deb`) with the canonical config unmodified, and froze `hive-package-inventory-v1`, whose digest proves byte identity and integrity for evidence transport. It explicitly did not admit signing, notarization, release publication, updater transport, installation, restart, rollback, credential authority, or a production-distributable claim.

The repository state this Work Order starts from was re-verified rather than assumed:

- `origin/main` equals the expected canonical `1a56224eeb9bc07f032df1ede23bdda9d74f8d12`; the working tree is clean; the predecessor remains accepted.
- Post-closeout exact-main evidence on that SHA is green across all eleven published check jobs, including `Governance`, the `Desktop Shell` lanes and the `Native Package Matrix` lanes.
- `#85` is OPEN / QUEUED and remains the governance pointer for this slice; `#82` is CLOSED; parent epic `#72` is OPEN. No competing active successor exists for `HCODER-DIST-001C`.
- The repository is **public**, which is the condition under which GitHub artifact attestations are available at no cost.
- Hosted protection state at source-check time: **zero environments, zero repository Actions secrets, zero repository variables**, and an environment named `production` does not exist. This is mutable external state and must be re-proved before any credentialed claim.
- Pinned toolchain at source-check time: `@tauri-apps/cli` 2.11.4, Node 24.21.0, Rust 1.98.1.

Source drift reconciled by this Work Order: `AGENTS.md` still declared `HCODER-CP-0022` as current execution state while the canonical Checkpoint and Issue #30 prove `CP-0025`. `AGENTS.md` is corrected to match the canonical source; the canonical Checkpoint wins, and no historical Decision or append-only Context Lock is rewritten.

## Scope

- One new closed contract: `hive-release-provenance-v1`, documented as a contract and enforced in code.
- One new stdlib-only, offline, non-mutating validator/admission gate: `tools/desktop/release_provenance.py`.
- One new focused adversarial test module: `tests/desktop/test_release_provenance.py`.
- One new workflow: `.github/workflows/protected-release.yml`, designed as a promotion pipeline with a secret-free preflight lane that can run as exact-head evidence.
- The governed documents named in `## Deliverables`, plus `DEC-030` at status PROPOSED / NOT CANONICAL.
- A bounded source-accuracy correction to `AGENTS.md`, and a bounded source-truth note where `07-DEPLOYMENT.md` would otherwise misstate proven packaging status as merely planned.

## Out of scope

`HCODER-DIST-001D` Tauri updater integration and any update endpoint or network transport. `HCODER-DIST-001E` update UI and notifications. `HCODER-DIST-001F` rollback/roll-forward execution and post-update health recovery. `HCODER-DIST-001G` install/update/restart end-to-end proof. Generic Git commit/ref/branch/tag authority inside the Hive runtime — a CI release action does not expand `Capability.GIT_WRITE`. Generic shell, process, Cua, filesystem or credential authority inside the product. A tracked `bundle.icon` or any other canonical `tauri.conf.json` product-configuration mutation. Changing the six-target package matrix, reducing targets, replacing Tauri with Electron, or adding dependencies. Calling Hive Coder production-distributable, which remains forbidden until the parent epic STOP CONDITION is satisfied. Creating or reconfiguring GitHub environments, secrets, protection rules or immutable-release settings, which is external shared-state provisioning and is reported as a blocker rather than performed here.

## Files/sources to read

`docs/project-brain/11-CHECKPOINT.md`; `docs/project-brain/10-DECISIONS-LEDGER.md` (DEC-028, DEC-029); `docs/project-brain/adrs/DEC-029-NATIVE-PACKAGE-MATRIX-EVIDENCE-CONTRACT.md` and `DEC-028-DISTRIBUTION-VERSION-CHANNEL-CONTRACT.md`; `docs/project-brain/03-SCOPE.md`; `docs/project-brain/02-REQUIREMENTS.md`; `docs/project-brain/09-DEFINITION-OF-DONE.md`; `docs/project-brain/04-ARCHITECTURE.md`; `docs/project-brain/05-SECURITY.md`; `.engineering/context-locks/HCODER-WO-0025.md`; `tools/desktop/package_inventory.py`; `tools/desktop/version_drift.py`; `apps/desktop/src/contracts/releaseChannel.ts`; `.github/workflows/native-package-matrix.yml`; `.github/workflows/governance.yml`; then Issues #30, #72 and #85, `AGENTS.md`, and this Work Order with its Context Lock.

## Requirements

1. **Four guarantees, never conflated.** The contract keeps artifact integrity, build provenance, publisher authenticity and platform trust/notarization as separate fields with separate admission rules. Provenance attestation must never satisfy a publisher-signing requirement, and a digest must never satisfy either one.
2. **Deterministic and closed.** Unknown keys, duplicate entries, absolute paths, path traversal, wrong source SHA, wrong version or channel, digest mismatch, package-set mismatch, impossible state combinations and fabricated publication claims are refused. The document contains no wall-clock timestamp; mutable timing stays external.
3. **Channel law agrees across languages.** `hive-release-channel-v1` semantics are reused exactly: `stable` admits no prerelease identifier, `beta` and `dev` require the first prerelease identifier to equal the channel name, case-sensitively.
4. **Fails closed on absent credentials.** Absent signing material is reported as `unavailable`, never as success, and never downgrades to unsigned publication.
5. **Protection is proved, not asserted.** A job that touches credentials or publication must depend on an objective probe of the named environment's actual protection semantics. Referencing an environment that does not exist is prohibited as evidence, because GitHub creates it unprotected rather than failing.
6. **Least privilege by construction.** Repository-wide workflow permissions stay read-only; `id-token`, `attestations`, `artifact-metadata` and `contents: write` are granted only to the single job that needs each, and only on the promotion path. No `pull_request_target` or equivalent, so release credentials are never exposed to pull-request code.
7. **No publication from this increment.** A real tag or GitHub Release is not created from this Draft PR. Publication remains structurally present and disabled, with the external gate reported.
8. **CP-0025 preserved exactly.** The six-target matrix, the pinned-CLI split-build, the ephemeral non-tracked overlay law, the canonical-config immutability and `hive-package-inventory-v1` are reused, not redefined; the provenance document descends from a real inventory digest rather than a parallel packaging model.

## Architecture rules

- The provenance tool is an **admission authority, not a claim-minting authority**. Producers may emit candidate documents; only the validator decides. The tool's build mode can emit honest credential-free baseline state and structurally cannot emit `signed`, `verified` or `published`.
- Release provenance binds to the CP-0025 inventory by the SHA-256 of the inventory's canonical serialization, so tampering with the upstream evidence changes the binding.
- Verification of a signed, notarized or attested artifact requires an independent verification result. Performing an operation is not evidence that it succeeded.
- The validator is standard-library only and offline, matching `package_inventory.py`: it must remain safe under `PYTHONWARNINGS=error::ResourceWarning` and must not open network, write outside an explicit `--json-out`, mutate a package root, or execute a package.
- Per-lane duplication is the established workflow style; a `strategy.matrix` is not introduced.
- Deviation from the prevailing mutable-tag action pinning is deliberate and must be stated: promotion-path third-party actions are pinned by full commit SHA because they run with release authority, and the pin is recorded with its upstream release identity so it remains auditable.

## Constraints

`HIGH_ASSURANCE` evidence law applies: exact-head gates, independent HEDS, and no self-issued approval. Secrets are never printed, echoed, persisted, committed, uploaded as ordinary artifacts, placed in test fixtures, exposed in command traces, or written into provenance manifests or HIVE. Private key material, certificates, notarization credentials and tokens are not read, requested, decoded, imported or configured by this increment; only their **class**, the documented slot name and the exact verification condition are reported. Governance, Desktop Shell and Native Package Matrix are not modified, weakened, re-triggered or path-filtered by this Work Order. Models and tools cannot mint approvals, permissions, trusted evidence or competence.

## Acceptance criteria

- A complete Work Order and Context Lock exist before any credential-backed operation, and `DEC-030` is materialized and internally consistent first.
- `DEC-030` is PROPOSED / NOT CANONICAL and separates integrity, provenance, publisher signing, notarization and publication authority.
- `AGENTS.md` no longer misstates `CP-0022` as current execution state; no historical Decision or append-only Context Lock is rewritten.
- The provenance contract and validator are closed, deterministic, offline-verifiable, fail-closed, and bind exact source, version, channel and package identities.
- Adversarial tests prove rejection of: tampered digest, tampered source SHA, wrong version, wrong channel, fabricated signing state, fabricated notarization state, duplicate entry, extra entry, traversal path, absolute path, package-set mismatch, impossible transition, provenance-as-signing substitution, and fabricated publication claim; each guard is proven non-vacuous by a mutation that fails only when the guard is removed.
- A protected-release workflow exists with least-privilege permissions, no secret exposure on pull requests, exact-SHA preflight, isolated per-OS signing stages, provenance generation **and** verification, an objective environment-protection probe, and a separately gated publication stage.
- The workflow never treats provenance attestation as a substitute for Windows or macOS publisher signing.
- No production release is published; the unsigned or merely attested path is never presented as publisher authenticity.
- Required credentials and protected environment are objectively absent, so this increment stops after the secret-independent substrate with a precise external-provisioning blocker and no degraded unsigned publication.
- `Governance`, `Desktop Shell` and `Native Package Matrix` remain green and unweakened on the final technical head, and the new `Protected Release` preflight lane is green on that head.
- Independent HEDS is not self-issued; the Draft PR remains unmerged awaiting review.

## Tests

Iterate on the focused provenance module only. Before commit run the focused release suite plus the existing version-drift and desktop security gates the workflow relies on. Run the full discovered `tests/` suite once on the final technical candidate, because `Governance` executes `python -m unittest discover -s tests -p "test_*.py"` and therefore runs this Work Order's tests on every promotion head. Hosted final exact-head evidence is `Governance` + `Desktop Shell` + `Native Package Matrix` + the new `Protected Release` preflight lane; these are not looped unnecessarily. A credentialed native job that cannot run because external material is absent is recorded `UNKNOWN`/`BLOCKED`, never converted to `PASS`.

## Deliverables

`.engineering/work-orders/HCODER-WO-0026.md`; `.engineering/context-locks/HCODER-WO-0026.md`; `.engineering/prebuilt/HCODER-WO-0026-IMPLEMENTATION-PACK.md`; `.engineering/prebuilt/HCODER-WO-0026-EXECUTOR-BRIEF.md`; `.engineering/prebuilt/HCODER-WO-0026-ACCEPTANCE-SECURITY-MAP.md`; `.engineering/evidence/HCODER-WO-0026.md`; `docs/project-brain/adrs/DEC-030-SIGNING-NOTARIZATION-RELEASE-PROVENANCE.md`; `docs/project-brain/contracts/RELEASE-PROVENANCE-V1.md`; `tools/desktop/release_provenance.py`; `tests/desktop/test_release_provenance.py`; `.github/workflows/protected-release.yml`; the bounded `AGENTS.md` and `07-DEPLOYMENT.md` source-truth corrections; and the `DEC-030` ledger entry authorized by Context Lock Delta 001.

## Review format

Verdict is `APPROVED | CORRECTION_REQUIRED | BLOCKED`, issued by the independent reviewer against the exact candidate head, with the standard review packet including the next executable Codex prompt as a generated PDF. The executor reports in Brazilian Portuguese using only `READY_FOR_REVIEW`, `BLOCKED_EXTERNAL_CREDENTIALS`, `BLOCKED_PROTECTED_ENVIRONMENT`, `BLOCKED_TOOLCHAIN` or `BLOCKED_SOURCE_TRUTH`, and never calls this Work Order `COMPLETE` or `CANONICAL`. `CORRECTION_REQUIRED` stays in this Work Order; no new increment begins until the reviewed predecessor is objectively accepted.

## STOP CONDITION

STOP before any credential-backed execution if `DEC-030`, this Work Order or the Context Lock is absent or internally inconsistent. STOP if any secret, private key, certificate, notarization credential, token or password would need to be printed, committed, stored in HIVE, uploaded as an ordinary artifact or passed through an unsafe channel. STOP if release protection cannot be objectively proven; a protected release must never be claimed from YAML intent alone. STOP if Windows or macOS signing requires an external account, certificate or service that is not already provisioned, finish the secret-independent substrate and report the exact provisioning blocker without values. STOP if a platform target can succeed only by reducing the six-target matrix or weakening an existing gate. STOP if the work requires updater, download, install, restart or rollback authority, generic Hive credential authority, or unrelated runtime capability. STOP if any HIGH or CRITICAL remains unresolved, a required exact-head gate is red, or the candidate head moves after evidence was collected. STOP before merge: independent review is mandatory, and only the review/promotion flow may declare this increment canonical.
