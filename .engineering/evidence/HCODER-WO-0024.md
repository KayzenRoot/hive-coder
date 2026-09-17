# Evidence Bundle — HCODER-WO-0024

**Status:** PREBUILT / IMPLEMENTATION PENDING — NO PROMOTION CLAIM  
**Canonical base:** `HCODER-CP-0023` / `b6aff55ac12c1d31a883878f1d8478d642fbe8e6`  
**Issue:** `#77`  
**Parent epic:** `#72`

## Claims allowed now
- A canonical product-version source of truth is **declared**: `apps/desktop/src-tauri/tauri.conf.json` → `version`, with `Cargo.toml` and `package.json` as exact mirrors.
- A deterministic, offline drift verifier exists (`tools/desktop/version_drift.py`) and reports `LOCKED` against the live manifests at the base.
- Strict SemVer parsing, the release-channel contract, the update-state model, the authenticity gate and the bounded redaction-safe error metadata are implemented as pure contract law.
- A Hive-owned `UpdateService` boundary exists whose production implementation is inert and exposes no mutating, transport or installation member.
- A bounded, read-only Settings/About read model exists.
- Contract tests, including the required negative proofs, are materialised.

## Claims explicitly NOT allowed
- That Hive Coder is installable, signed, notarized, auto-updatable or production-distributable.
- That any update, download, install, restart or release path exists or is authorised.
- That cryptographic verification is implemented. **No scheme is admitted**, so install-ready is structurally unreachable.
- That `DEC-028` is canonical. It is PROPOSED.
- That any platform's native distribution behaviour is proven. Only the contract lane is exercised.

## Base-state facts to re-verify
Re-read live files from the exact base before relying on these; repository source wins:
- `tauri.conf.json`: `productName="Hive Coder"`, `version="0.1.0"`, `bundle.active=false`.
- `Cargo.toml`: package version `0.1.0`, Tauri `=2.11.5`.
- `package.json`: version `0.1.0`, `@tauri-apps/api` `2.11.1`, `@tauri-apps/cli` `2.11.4`.

## Prebuilt acceptance state
- Version/channel/update-state/about contracts: MATERIALISED.
- Version drift verifier: MATERIALISED, reports `LOCKED` at base.
- `UpdateService` boundary + inert adapter: MATERIALISED.
- Negative proofs (malformed SemVer, unknown channel, drift, illegal transition, downgrade, cross-channel, install-ready without proof, oversized/credential-shaped detail, forbidden member, side-effect reachability): MATERIALISED.
- Native Windows/Linux/macOS distribution behaviour: **UNPROVEN**.
- Signing/notarization/release publication: **UNPROVEN** and unauthorised.
- HEDS: NOT YET RUN.

## Promotion evidence template
For each exact technical head record:
- commit SHA;
- workflow/run/job IDs;
- runner OS/version/architecture;
- focused test counts and zero implementation skips;
- version-drift gate result against live manifests;
- explicit confirmation that no updater plugin, HTTP client, download, install, restart, signing, release or credential path exists;
- explicit confirmation that `bundle.active` remains `false`;
- HEDS HIGH/CRITICAL counts.

## STOP
`UNKNOWN` never becomes `PASS`. Exact-head evidence proves only the exact SHA it names. Do not merge, do not declare the decision canonical, and do not begin HCODER-DIST-001B from this ledger.
