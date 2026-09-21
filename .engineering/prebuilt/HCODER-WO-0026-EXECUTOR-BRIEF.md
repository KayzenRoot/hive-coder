# HCODER-WO-0026 — Executor Brief

**Status:** FROZEN EXECUTION BRIEF — the contract it describes is materialized in source; whether a given head satisfies its obligations is external evidence  
**Base:** `1a56224eeb9bc07f032df1ede23bdda9d74f8d12`  
**Issue:** `#85`  
**Prior reviewed-head facts:** historical only; mutable current review, gate, environment and secret state is external in the active Draft PR and Issues #30 and #85.

## Start here

Read, in order:
1. `.engineering/work-orders/HCODER-WO-0026.md`
2. `.engineering/context-locks/HCODER-WO-0026.md` — its append-only delta sequence is the authority for the ledger edit, for the additional test file, and for what the correction round may change; no terminal delta number is mirrored here
3. `.engineering/prebuilt/HCODER-WO-0026-IMPLEMENTATION-PACK.md`
4. `.engineering/prebuilt/HCODER-WO-0026-ACCEPTANCE-SECURITY-MAP.md`
5. `docs/project-brain/contracts/RELEASE-PROVENANCE-V1.md`
6. `.github/workflows/native-package-matrix.yml` (the build law the new lanes must parallel, not weaken)

## Mandatory order for completion work

A. Keep governance materialized **before** any secret-adjacent step: Work Order, Context Lock, ADR and ledger entry must exist and be internally consistent first.
B. Keep `hive-release-provenance-v1` closed: exact ordered key tuples, one exception type, unknown keys refused, ceilings applied before parsing. Any new field, state, edge or relaxed bound is a contract change requiring `hive-release-provenance-v2` and a governed Work Order.
C. Keep the validator an admission authority. Never add a flag, mode or default that emits `signed`, `verified`, `stapled` or `published`; a stage advances state only through `--transition` plus `--verify`.
D. Keep `hive-package-inventory-v1` the single packaging model. Bind to it by digest; do not fork a second inventory, digest or manifest. Let that same document, and nothing else, decide what an attestation is about: its subjects are the inventory's package identities, derived through the validated document rather than rediscovered from a directory walk or a glob, and the manifest file is never itself a subject.
E. Preserve the six-target matrix and the canonical config. No `bundle.active` change, no tracked icon, no reduced `--bundles`, no new dependency.
F. Keep credential-bearing lanes off the untrusted path: `workflow_dispatch` only, no `pull_request_target` or equivalent, job-level least privilege, and short-lived OIDC identity preferred over any long-lived secret.
G. Prove protection objectively or report it unproven. A referenced environment is not a protected environment; `RELEASE_PROTECTION=UNPROVEN` and `UNPROTECTED` are both refusal.
H. Report absent credentials as a blocker with class, mechanism, documented slot name and exact verification condition — never a value, never a request for one. A stage that has no authority to read a credential must also declare no binding and no presence test for it, because a binding resolves into the job's environment the moment anyone provisions the value; report what is required as static text.
I. Keep every existing Governance, Desktop Shell and Native Package Matrix lane green and unweakened, and keep the discovered `unittest` suite green under `PYTHONWARNINGS=error::ResourceWarning`, because `Governance` runs it on every promotion head.

## Forbidden shortcuts

No signing, codesign, notarization, stapling or publisher-authenticity claim; no release, tag or GitHub Release creation; no updater plugin, endpoint, artifact, download, install, restart or rollback path; no product network fetch; no Hive runtime capability, permission, permit or credential authority; no environment, secret, variable or ruleset creation in the hosting platform; no installer or package execution as acceptance; no test that relaxes an assertion to stay green; no non-vacuous-guard deletion hidden rather than recorded; no merge, no self-approval, no `HCODER-CP-0026` claim, and no canonical `DEC-030`.

## Definition of Done for execution

`tools/desktop/release_provenance.py` and its 159-case suite plus the 45-case workflow audit pass; the guard-neutralisation sweep and the workflow mutation sweep are recorded with their survivor lists; contract, ADR, ledger entry, Work Order, Context Lock, this pack and the evidence bundle are mutually consistent; the Draft PR is opened against `#85` and Issues #30 and #85 carry the exact-head evidence; and the terminal report names exactly one state — here `BLOCKED_EXTERNAL_CREDENTIALS` — without upgrading it to completion.

## External provisioning this slice cannot supply

| Need | Class and mechanism | Documented slots and configuration identities | Verification condition |
|---|---|---|---|
| Windows publisher identity | Azure Artifact Signing certificate profile reached by a federated Microsoft Entra identity; the private key never exists on the runner. Fallback: `signtool` with a PKCS #12, recorded as the weaker option and not used here. The chain that makes the preferred path exist is: an Entra application registration; a **federated identity credential** on that application trusting the runner's OIDC issuer with a subject identifier bound to this repository and the `hive-release-signing` environment; an **Artifact Signing account** and a **certificate profile** in it, in a region matching the signing endpoint; the **`Artifact Signing Certificate Profile Signer`** data-plane role assigned to that service principal at certificate-profile scope; and an RFC 3161 timestamp authority applied to every signature, without which the short-lived certificate invalidates the signature in days | Secret-class slots: `AZURE_ARTIFACT_SIGNING_ENDPOINT`, `AZURE_ARTIFACT_SIGNING_ACCOUNT`, `AZURE_ARTIFACT_SIGNING_CERTIFICATE_PROFILE`. Configuration identities, not key material: `ENTRA_APPLICATION_CLIENT_ID`, `ENTRA_DIRECTORY_TENANT_ID`, `ARTIFACT_SIGNING_SUBSCRIPTION_ID`, `FEDERATED_CREDENTIAL_SUBJECT_REPO_ENVIRONMENT_IDENTITY`, `CERTIFICATE_PROFILE_SIGNER_ROLE_ASSIGNMENT`, and the timestamp-authority URI the signing step names explicitly | each package's signature verifies with an independent authenticode verification whose signer identity matches the recorded certificate subject and fingerprint, and whose embedded RFC 3161 timestamp is present and in the certificate's validity window |
| macOS publisher identity and platform trust | Developer ID Application certificate imported into a keychain on the runner and used by `codesign` with Hardened Runtime and a secure timestamp, then `notarytool` submission over an **App Store Connect API key**, then stapling the accepted ticket. Tauri 2.11 reads its own variable names for this, and they are not the `notarytool` flag names | Signing: `APPLE_SIGNING_IDENTITY`, `APPLE_CERTIFICATE`, `APPLE_CERTIFICATE_PASSWORD`. API-key notarization: `APPLE_API_KEY` (the API **Key ID**), `APPLE_API_ISSUER` (the App Store Connect **issuer UUID**), `APPLE_API_KEY_PATH` (path to the downloaded `.p8`; Tauri reads the key by path, so its bytes are never a variable value). **Not on this list:** `APPLE_TEAM_ID`, which authenticates the Apple-ID notarization mode (`APPLE_ID` + app-specific `APPLE_PASSWORD` + Team ID) — a Team ID is not an issuer and cannot substitute for one, so a submission made with it in place of `APPLE_API_ISSUER` cannot be authorized | `codesign --verify --strict --deep` passes and `xcrun notarytool information` reports Acceptance for the submitted artifact, with the ticket stapled to the `.app` and to the `.dmg` |
| Protected release path | Two hosting-platform environments with enforced, non-bypassable required reviewers | `hive-release-signing`, `hive-release-publish` | the probe reads a real environment record whose `protection_rules` contain a `required_reviewers` rule with at least one reviewer, `prevent_self_review` true and `can_admins_bypass` false, and `RELEASE_PROTECTION=PROTECTED` is printed for that record |
| Scope the *next* slice needs and this one refuses to take | `id-token: write` on the credential-bearing signing job, so the runner's OIDC identity can be exchanged for an Azure token under the federated credential above | Not created here: `sign-windows` and `sign-and-notarize-macos` hold `contents: read` only | the slice that implements signing must state the grant, the job that receives it and the audit that keeps it scoped; provisioning a credential does not authorize the permission change, and adding the scope early to "save a round trip" would hand a token-minting capability to a stage that has no use for it yet |

This table is the complete external object list; a signing stage's own literals are narrower by design, because a stage names only what it would have to resolve at run time. The workflow text is authoritative for what a stage declares, this table is authoritative for what provisioning requires, and neither is a request for a value. Report a blocker in these terms — class, mechanism, slot or configuration identity, verification condition — and never a value, never an import, never a request for one.

## STOP

STOP if any of the above would require printing, persisting, committing or uploading a value. STOP if protection cannot be proven. STOP if a lane can only go green by pretending a signing operation happened. STOP with `BLOCKED_ATTESTATION_SUBJECT_MODEL` and the exact official-tool evidence if an inventory package identity cannot be represented truthfully as an attestation subject — never by omitting that subject, substituting another artifact, or presenting a directory-tree digest as a file digest. Do not begin `HCODER-DIST-001D`.
