# Evidence Bundle — HCODER-WO-0025

**Status:** PREBUILT / IMPLEMENTATION PENDING — NO PROMOTION CLAIM  
**Canonical base:** `HCODER-CP-0024` / `3e1e1af7596c56716825206587bf2a88e1b179d0`  
**Issue:** `#82`  
**Parent epic:** `#72`  
**Slice:** `HCODER-DIST-001B`  
**Correction authority:** `HCODER-WO-0025`; the canonical append-only delta history lives in `.engineering/context-locks/HCODER-WO-0025.md`, and no terminal delta number or range is mirrored here.

## Claims allowed now
- The Work Order, Context Lock, implementation pack, executor brief and this scaffold exist and define a bounded native package matrix slice.
- The pinned Tauri CLI (`@tauri-apps/cli` `2.11.4`) supports the split-build model (`build --no-bundle`, then `bundle --bundles`) and bundles on explicit request while the canonical `bundle.active=false` remains unchanged.
- The Windows `msi` target requires an icon declaration that the canonical config does not carry; an ephemeral, runner-local overlay supplying the already-generated `icons/icon.ico` is the authorised mechanism.
- The deterministic icon generator emits `icons/icon.ico` (64×64, 32-bit) and `icons/icon.png` (64×64, RGBA) only; no `.icns` exists.

## Claims explicitly NOT allowed
- That any platform's packages are produced, validated or uploaded yet.
- That packages are signed, notarized, trusted, production-ready or production-distributable.
- That a package digest establishes publisher authenticity. It establishes byte identity/integrity for evidence transport only.
- That the package matrix promotes anything: `DEC-029` is PROPOSED / NOT CANONICAL if retained, and no decision or checkpoint status changes in this slice.
- That the ephemeral overlay is canonical product config or a new authority surface.

## Reviewed-head record (historical)

Reviewed-head facts are recorded externally in the active PR and Issues #30 and #82. This scaffold deliberately mirrors **no** head SHA, run ID, review ID or merge SHA: those are mutable evidence and must not be embedded in a pre-CI commit.

## Implementation state and external promotion evidence

- Inventory/validator and workflow: **not yet implemented** at this scaffold stage.
- External promotion evidence is required and is not recorded here: hosted exact-head Governance, Desktop Shell and Native Package Matrix must be green, and an independent HEDS review must report unresolved HIGH/CRITICAL `0/0`, each against the exact promotion head a decision names.

## Base-state facts to re-verify
Re-read live files before relying on these; repository source wins:
- `tauri.conf.json`: `productName="Hive Coder"`, `version="0.1.0"`, `bundle = {"active": false}`, no `icon` key.
- `package.json`: `@tauri-apps/cli` `2.11.4`, `@tauri-apps/api` `2.11.1`.
- `Cargo.toml`: package version `0.1.0`, `tauri = "=2.11.5"`, `tauri-build = "=2.6.3"`.
- Existing desktop lanes build with `tauri build --no-bundle`; Linux adds `--features rfd/gtk3`.
- No `actions/upload-artifact` usage and no release/tag automation exists in the repository today.

## Promotion evidence template
For each exact technical head record: commit SHA; workflow run IDs and job IDs; runner OS/architecture per package lane; pinned CLI version and the `--bundles` targets that lane advertised; whether the ephemeral overlay was required; generated package paths; inventory manifest identity; workflow artifact name and retention; confirmation that `tauri.conf.json` and tracked source were unchanged; confirmation that no signing/notarization/release/updater path exists; and HEDS HIGH/CRITICAL counts.

## STOP
`UNKNOWN` never becomes `PASS`. Exact-head evidence proves only the exact SHA it names. Mutable receipts are recorded externally, never in this bundle. Do not merge, do not claim production distributability, and do not begin `HCODER-DIST-001C` from this ledger.
