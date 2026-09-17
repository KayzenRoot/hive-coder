# Evidence Bundle — HCODER-WO-0024

**Status:** IMPLEMENTED / CORRECTION REVIEW PENDING — NO PROMOTION CLAIM  
**Canonical base:** `HCODER-CP-0023` / `b6aff55ac12c1d31a883878f1d8478d642fbe8e6`  
**Issue:** `#77`  
**Parent epic:** `#72`  
**PR:** `#80` (Draft, unmerged)  
**Reviewed prebuild head:** `4710a47e2e099b03baa7fd3e5665bfbc882c4c8d`  
**Independent review:** `5236275753` — CORRECTION_REQUIRED, CRITICAL `0` / HIGH `4` / MEDIUM `2`  
**Correction authority:** Context Lock Delta `001`

## Correction state (why the previous "materialised" claims were withdrawn)

The prebuild head at `4710a47e2e099b03baa7fd3e5665bfbc882c4c8d` passed Governance `35224933911` and Desktop Shell `35224933743`, yet the independent review returned four HIGH and two MEDIUM findings and the following claims were therefore **false at that head** and have been withdrawn:

- "install-ready is structurally unreachable" — the gate sat on `ready -> installing` while `verifying -> ready` was ungated, and a direct `ready`/`installing` status snapshot was accepted (`H-20-01`).
- "version and channel are validated" — they were validated independently, so `0.1.0` + `beta` was accepted (`H-20-02`).
- the acceptance-map claim that status snapshots are closed and bounded — no event object was validated, no unknown key was rejected and the untrusted input was returned cast as `UpdateStatus` (`H-20-03`).
- exact SemVer precedence — numeric prerelease identifiers were compared through floating-point conversion (`H-20-04`).
- single-parser channel law — `versionMatchesChannel` carried a second, looser parser (`M-20-05`).
- the `DEC-028` reference — no ADR and no ledger entry existed (`M-20-06`).

The corrections are carried in the same Work Order. Their exact-head proof state is recorded below and is **not** claimed as proven: green gates on the reviewed head did not mean the properties held, and no gate result for the corrected head has been observed yet.

## Claims allowed now
- A canonical product-version source of truth is **declared**: `apps/desktop/src-tauri/tauri.conf.json` → `version`, with `Cargo.toml` and `package.json` as exact mirrors.
- A deterministic, offline drift verifier exists (`tools/desktop/version_drift.py`) and reports `LOCKED` against the live manifests at the base.
- Strict SemVer parsing, the release-channel contract, the update-state model, the authenticity gate and the bounded redaction-safe error metadata are implemented as pure contract law, with the six reviewed defects corrected in source.
- A Hive-owned `UpdateService` boundary exists whose production implementation is inert and exposes no mutating, transport or installation member.
- A bounded, read-only Settings/About read model exists.
- Contract tests, including the required negative proofs and the new adversarial regression cases for the six findings, exist in source.

## Claims explicitly NOT allowed
- That Hive Coder is installable, signed, notarized, auto-updatable or production-distributable.
- That any update, download, install, restart or release path exists or is authorised.
- That cryptographic verification is implemented. **No scheme is admitted**, so install-ready is structurally unreachable.
- That `DEC-028` is canonical. It is PROPOSED / NOT CANONICAL.
- That any platform's native distribution behaviour is proven. Only the contract lane is exercised.
- That the corrected contracts are *proven*: the corrected head has not yet been gated or independently reviewed.

## Base-state facts to re-verify
Re-read live files from the exact base before relying on these; repository source wins:
- `tauri.conf.json`: `productName="Hive Coder"`, `version="0.1.0"`, `bundle.active=false`.
- `Cargo.toml`: package version `0.1.0`, Tauri `=2.11.5`.
- `package.json`: version `0.1.0`, `@tauri-apps/api` `2.11.1`, `@tauri-apps/cli` `2.11.4`.

## Acceptance state at the reviewed prebuild head
- Version/channel/update-state/about contracts: MATERIALISED, but four HIGH and two MEDIUM findings open.
- Version drift verifier: MATERIALISED, reports `LOCKED` at base.
- `UpdateService` boundary + inert adapter: MATERIALISED.
- Negative proofs (malformed SemVer, unknown channel, drift, illegal transition, downgrade, cross-channel, install-ready without proof, oversized/credential-shaped detail, forbidden member, side-effect reachability): MATERIALISED.
- Install-ready unreachability, version/channel identity binding, closed/reconstructed status snapshots, exact numeric precedence, single-parser channel law: **NOT PROVEN** at the reviewed head; corrected in source, exact-head proof pending.
- Native Windows/Linux/macOS distribution behaviour: **UNPROVEN**.
- Signing/notarization/release publication: **UNPROVEN** and unauthorised.
- HEDS: NOT YET RUN on any head.

## Promotion evidence template
For each exact technical head record:
- commit SHA;
- workflow/run/job IDs;
- runner OS/version/architecture;
- focused test counts and zero implementation skips;
- version-drift gate result against live manifests;
- the desktop security gate result under CI conditions (`node_modules` absent, as the gate runs before `npm ci`);
- explicit confirmation that no updater plugin, HTTP client, download, install, restart, signing, release or credential path exists;
- explicit confirmation that `bundle.active` remains `false`;
- HEDS HIGH/CRITICAL counts.

## STOP
`UNKNOWN` never becomes `PASS`. Exact-head evidence proves only the exact SHA it names. Do not merge, do not declare the decision canonical, and do not begin HCODER-DIST-001B from this ledger.
