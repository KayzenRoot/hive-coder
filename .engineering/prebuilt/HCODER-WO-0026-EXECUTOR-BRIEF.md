# HCODER-WO-0026 — Executor Brief

**Status:** FROZEN EXECUTION BRIEF — the contract it describes is materialized in source; whether a given head satisfies its obligations is external evidence  
**Base:** `1a56224eeb9bc07f032df1ede23bdda9d74f8d12`  
**Issue:** `#85`  
**Prior reviewed-head facts:** historical only; mutable current review, gate, environment and secret state is external in the active Draft PR and Issues #30 and #85.

## Start here

Read, in order:
1. `.engineering/work-orders/HCODER-WO-0026.md`
2. `.engineering/context-locks/HCODER-WO-0026.md` — including Deltas 001 and 002, which are the only authorities for the ledger edit and the additional test file
3. `.engineering/prebuilt/HCODER-WO-0026-IMPLEMENTATION-PACK.md`
4. `.engineering/prebuilt/HCODER-WO-0026-ACCEPTANCE-SECURITY-MAP.md`
5. `docs/project-brain/contracts/RELEASE-PROVENANCE-V1.md`
6. `.github/workflows/native-package-matrix.yml` (the build law the new lanes must parallel, not weaken)

## Mandatory order for completion work

A. Keep governance materialized **before** any secret-adjacent step: Work Order, Context Lock, ADR and ledger entry must exist and be internally consistent first.
B. Keep `hive-release-provenance-v1` closed: exact ordered key tuples, one exception type, unknown keys refused, ceilings applied before parsing. Any new field, state, edge or relaxed bound is a contract change requiring `hive-release-provenance-v2` and a governed Work Order.
C. Keep the validator an admission authority. Never add a flag, mode or default that emits `signed`, `verified`, `stapled` or `published`; a stage advances state only through `--transition` plus `--verify`.
D. Keep `hive-package-inventory-v1` the single packaging model. Bind to it by digest; do not fork a second inventory, digest or manifest.
E. Preserve the six-target matrix and the canonical config. No `bundle.active` change, no tracked icon, no reduced `--bundles`, no new dependency.
F. Keep credential-bearing lanes off the untrusted path: `workflow_dispatch` only, no `pull_request_target` or equivalent, job-level least privilege, and short-lived OIDC identity preferred over any long-lived secret.
G. Prove protection objectively or report it unproven. A referenced environment is not a protected environment; `RELEASE_PROTECTION=UNPROVEN` and `UNPROTECTED` are both refusal.
H. Report absent credentials as a blocker with class, mechanism, documented slot name and exact verification condition — never a value, never a request for one.
I. Keep every existing Governance, Desktop Shell and Native Package Matrix lane green and unweakened, and keep the discovered `unittest` suite green under `PYTHONWARNINGS=error::ResourceWarning`, because `Governance` runs it on every promotion head.

## Forbidden shortcuts

No signing, codesign, notarization, stapling or publisher-authenticity claim; no release, tag or GitHub Release creation; no updater plugin, endpoint, artifact, download, install, restart or rollback path; no product network fetch; no Hive runtime capability, permission, permit or credential authority; no environment, secret, variable or ruleset creation in the hosting platform; no installer or package execution as acceptance; no test that relaxes an assertion to stay green; no non-vacuous-guard deletion hidden rather than recorded; no merge, no self-approval, no `HCODER-CP-0026` claim, and no canonical `DEC-030`.

## Definition of Done for execution

`tools/desktop/release_provenance.py` and its 128-case suite plus the 42-case workflow audit pass; the guard-neutralisation sweep and the workflow mutation sweep are recorded with their survivor lists; contract, ADR, ledger entry, Work Order, Context Lock, this pack and the evidence bundle are mutually consistent; the Draft PR is opened against `#85` and Issues #30 and #85 carry the exact-head evidence; and the terminal report names exactly one state — here `BLOCKED_EXTERNAL_CREDENTIALS` — without upgrading it to completion.

## External provisioning this slice cannot supply

| Need | Class and mechanism | Documented slots | Verification condition |
|---|---|---|---|
| Windows publisher identity | Azure Artifact Signing certificate profile reached by federated OIDC identity (fallback: `signtool` with a PKCS #12, the weaker option) | `AZURE_ARTIFACT_SIGNING_ENDPOINT`, `AZURE_ARTIFACT_SIGNING_ACCOUNT`, `AZURE_ARTIFACT_SIGNING_CERTIFICATE_PROFILE` | each package's signature verifies with an independent authenticode verification whose signer identity matches the recorded certificate subject and fingerprint |
| macOS publisher identity and platform trust | Apple Developer ID Application certificate plus App Store Connect API key for `notarytool` | `APPLE_SIGNING_IDENTITY`, `APPLE_CERTIFICATE`, `APPLE_CERTIFICATE_PASSWORD`, `APPLE_TEAM_ID`, `APPLE_API_KEY_ID`, `APPLE_API_KEY` | `codesign --verify --strict --deep` passes and `xcrun notarytool information` reports Acceptance for the submitted artifact |
| Protected release path | Two hosting-platform environments with enforced, non-bypassable required reviewers | `hive-release-signing`, `hive-release-publish` | the probe reads a real environment record whose `protection_rules` contain a `required_reviewers` rule with at least one reviewer, `prevent_self_review` true and `can_admins_bypass` false, and `RELEASE_PROTECTION=PROTECTED` is printed for that record |

## STOP

STOP if any of the above would require printing, persisting, committing or uploading a value. STOP if protection cannot be proven. STOP if a lane can only go green by pretending a signing operation happened. Do not begin `HCODER-DIST-001D`.
