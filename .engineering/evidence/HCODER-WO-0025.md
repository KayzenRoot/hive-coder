# Evidence Bundle — HCODER-WO-0025

**Status:** SOURCE MATERIALIZED — EXACT-HEAD PROMOTION EVIDENCE EXTERNAL  
**Canonical base:** `HCODER-CP-0024` / `3e1e1af7596c56716825206587bf2a88e1b179d0`  
**Issue:** `#82`  
**Parent epic:** `#72`  
**Slice:** `HCODER-DIST-001B`  
**Correction authority:** `HCODER-WO-0025`; the canonical append-only delta history lives in `.engineering/context-locks/HCODER-WO-0025.md`, and no terminal delta number or range is mirrored here.

## Source-materialized claims

These statements describe the repository as it exists and do not change as evidence advances:

- The Work Order, Context Lock, implementation pack, executor brief, acceptance/security map and this ledger exist and define a bounded native package matrix slice.
- `.github/workflows/native-package-matrix.yml` is materialized: one additional exact-head proof lane per platform that neither replaces nor weakens `Governance` or `Desktop Shell`, with no `pull_request` path filter, runtime derivation of the canonical version and identifier, a bounded two-attempt bundle retry, bounded artifact upload with short retention, and a tracked-source guard.
- `tools/desktop/package_inventory.py` is materialized: standard-library only, offline, root-bounded discovery, closed `hive-package-inventory-v1` schema, exact numeric-free hashing, documented sorted-tree digest for directory bundles, and a closed-manifest verification law.
- `tests/desktop/test_package_inventory.py` is materialized: valid inventories per platform, the full rejection set, mutation and determinism proofs, symlink containment decisions, and workflow-trigger assertions.
- The pinned Tauri CLI supports the split-build model (`build --no-bundle`, then an explicit `bundle --bundles`), and explicit bundling does not require `bundle.active=true`.
- The deterministic icon generator emits `icons/icon.ico` and `icons/icon.png`; the Windows `msi` target requires an icon declaration that the canonical config does not carry, so an ephemeral runner-local overlay supplies it.
- The canonical `tauri.conf.json` is byte-unchanged by this slice, `bundle.active` remains `false`, and no tracked `bundle.icon` exists.

## Claims requiring external exact-head evidence

Whether any of these holds is satisfied only against a named exact head, and that mutable state lives in PR #83 and Issues #30 and #82 rather than here:

- Every lane produces its declared targets on a native runner — Windows `msi`+`nsis`, macOS `app`+`dmg`, Linux `appimage`+`deb` — with the inventory valid and the structural checks passing.
- Hosted `Governance`, `Desktop Shell` and `Native Package Matrix` are green on that head, and `TRACKED_SOURCE_UNCHANGED` passes on every lane.
- An independent review of that head reports unresolved HIGH/CRITICAL `0/0`, and a governed expected-head merge completes.

## Claims never admitted by this slice

- That packages are signed, notarized, trusted, production-ready or production-distributable.
- That a package digest establishes publisher authenticity. A digest proves byte identity and integrity for evidence transport only.
- That the ephemeral overlay is canonical product config or a new authority surface.
- That this slice admits any installer execution, release or tag publication, updater behaviour, network fetch by product code, or new dependency, plugin, permission or capability.
- That `DEC-029` is canonical. It is PROPOSED / NOT CANONICAL.

## Reviewed-head records (historical)

Reviewed-head facts are recorded externally in the active PR and Issues #30 and #82. This ledger deliberately mirrors **no** head SHA, run ID, review ID or merge SHA: those are mutable evidence and must not be embedded in a pre-CI commit. The Prompt 33 preflight STOP and the Prompt 35/36 HIVE bootstrap STOPs are historical records and are preserved as such.

## Base-state facts to re-verify
Re-read live files before relying on these; repository source wins:
- `tauri.conf.json`: `productName="Hive Coder"`, `version="0.1.0"`, `identifier="dev.hive.coder"`, `bundle = {"active": false}`, no `icon` key.
- `package.json`: `@tauri-apps/cli` `2.11.4`, `@tauri-apps/api` `2.11.1`.
- `Cargo.toml`: package version `0.1.0`, `tauri = "=2.11.5"`, `tauri-build = "=2.6.3"`.
- Existing desktop lanes build with `tauri build --no-bundle`; Linux adds `--features rfd/gtk3`.

## Promotion evidence template
For each exact technical head record: commit SHA; workflow run IDs and job IDs; runner OS/architecture per package lane; pinned CLI version and the `--bundles` targets that lane advertised; whether the ephemeral overlay was required; generated package paths; inventory manifest identity; workflow artifact name and retention; confirmation that `tauri.conf.json` and tracked source were unchanged; confirmation that no signing/notarization/release/updater path exists; and HEDS HIGH/CRITICAL counts.

## STOP
`UNKNOWN` never becomes `PASS`. Exact-head evidence proves only the exact SHA it names. Mutable receipts are recorded externally, never in this bundle. Do not merge, do not claim production distributability, and do not begin `HCODER-DIST-001C` from this ledger.
