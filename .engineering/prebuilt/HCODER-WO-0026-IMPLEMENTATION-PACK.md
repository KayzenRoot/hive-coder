# HCODER-WO-0026 — Prebuilt Implementation Pack

**Status:** FROZEN EXECUTION CONTRACT — satisfaction of its obligations is external exact-head evidence  
**Base:** `1a56224eeb9bc07f032df1ede23bdda9d74f8d12`  
**Issue:** `#85`  
**Prior reviewed-head facts:** historical only; this document is not the review index. Mutable current review, gate, environment and secret state is external in the active Draft PR and Issues #30 and #85.  
**Canonical authority history:** `.engineering/context-locks/HCODER-WO-0026.md` — the append-only delta sequence for this Work Order; no terminal delta number or range is mirrored here.

## Mission

Materialize the secret-independent half of `HCODER-DIST-001C`: a closed release-provenance contract, an offline fail-closed validator of it, adversarial tests for both, and a promotion-pipeline workflow whose credential-bearing stages are structurally gated. Stop at the credential boundary and report it, so the next slice is completion-oriented rather than discovery-oriented.

## Fixed contract identities

```text
PROVENANCE_SCHEMA   = "hive-release-provenance-v1"
CONTRACT_DOC        = "docs/project-brain/contracts/RELEASE-PROVENANCE-V1.md"
VALIDATOR           = "tools/desktop/release_provenance.py"
WORKFLOW_NAME       = "Protected Release"
WORKFLOW_PATH       = ".github/workflows/protected-release.yml"
UPSTREAM_BINDING    = "hive-package-inventory-v1 document, canonical_bytes digest"
DECISION            = "DEC-030 (PROPOSED / NOT CANONICAL)"
```

## Materialized substrate

- `tools/desktop/release_provenance.py` — standard library only, offline, one exception type (`ProvenanceError`), closed ordered key tuples at every level, `MAX_INPUT_BYTES` ceiling applied before parsing, and modes `--build`, `--verify`, `--gate`, `--transition`, `--channel-gate`, `--environment-protection`. It reuses `tools.desktop.package_inventory.serialize_inventory` instead of defining a second packaging model.
- `tests/desktop/test_release_provenance.py` — 132 cases: valid documents per platform, the full rejection set, ladder/transition law, gate-reason law, channel coherence, canonical byte stability, the foreign-record environment law and the offline law of the module itself.
- `tests/desktop/test_protected_release_workflow.py` — 42 cases of static audit over the workflow text (authorized by Context Lock Delta 002), each guard paired with a synthetic mutation of the same text; self-reference guards read the syntax tree rather than a substring list.
- `.github/workflows/protected-release.yml` — 8 jobs: `preflight`, `probe-release-protection`, `build-attest-{windows,linux,macos}`, `sign-windows`, `sign-and-notarize-macos`, `publish`.

## Five laws the substrate exists to enforce

1. **Separation.** Integrity, provenance, publisher signing and platform trust are four fields; the gate reads each separately, so a verified attestation can never clear a publisher-signing requirement and a digest can never clear either.
2. **Descent.** Every document binds the canonical-serialization digest of the exact inventory it describes; tampering with upstream packaging evidence breaks the downstream binding instead of surviving it.
3. **Timestamp-free determinism.** No wall-clock field exists in the contract, so the same facts serialize identically and a receipt cannot age into a different claim.
4. **Admission, not minting.** `--build` emits only the honest credential-free baseline and offers no flag that produces a signing, notarization, attestation or publication claim; a later stage must pass `--transition` and `--verify` to advance state.
5. **Observed protection.** Credential-bearing jobs depend on a runtime probe of the environment's actual `protection_rules`, `prevent_self_review` and `can_admins_bypass`, judged by the validator — never on a name written in YAML, because the platform creates a referenced-but-undefined environment unprotected.

## Preserved CP-0025 inputs

The six-target matrix (`msi`, `nsis`, `deb`, `appimage`, `app`, `dmg`), the split-build model, the ephemeral runner-local overlay, the canonical `tauri.conf.json`, `bundle.active=false`, and the pinned toolchain are inherited byte-for-byte in intent: `governance.yml`, `desktop-shell.yml` and `native-package-matrix.yml` are not touched by this Work Order, and the new lanes re-run the same build law rather than inventing a second one. The audit pins this by comparing the macOS bundle targets and the overlay non-upload rule against the preserved workflow text.

## Credential boundary

No signing identity, certificate, notarization credential, token or password exists in this repository's host state, and none is created, requested or printed here. The candidate workflow's Windows and macOS signing stages end in an unconditional refusal that is *independent of slot presence*, so provisioning a credential later cannot silently turn an unimplemented signing stage green. Provisioning requirements are reported as class, mechanism, documented slot name and verification condition only.

## Definition of Done for this pack

Validator and both test modules green under the repository's discovered `unittest` suite with `PYTHONWARNINGS=error::ResourceWarning`; every guard demonstrated non-vacuous by a mutation that makes its test fail; the contract document, ADR, ledger entry and governance records materialized and internally consistent; Draft PR opened against `#85`; and the terminal state reported as the objective credential blocker rather than as completion.

## STOP CONDITION

STOP before credential-backed execution, before any release, tag, environment, secret or variable creation, and before any merge. STOP rather than reducing the six-target matrix, faking a `not-applicable` on a platform that has a publisher-trust model, downgrading to unsigned publication, or converting an unproven gate into a passing one.
