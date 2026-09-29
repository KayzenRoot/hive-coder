# License & Provenance — Hive Coder

Third-party foundations/dependencies must be evaluated before source import or distribution.

## Approved foundation records

### Open Interpreter
- Repository: `openinterpreter/openinterpreter`.
- Release: `0.0.43`.
- Tag: `rust-v0.0.43`.
- Commit: `6e7c4bb78bb1c349b82f584f7e21a529ec39a74f`.
- License verified at exact commit: Apache-2.0.
- Windows x64 artifact SHA-256: `be317ff01c8730f9a3623cb2f807d80414923ddedf5e31a3012403a1f6ba67c5`.
- Integration classification: external dependency, not copied source.

### Cua Driver
- Repository: `trycua/cua`.
- Selected component: `libs/cua-driver/rust`.
- Release: `0.28.1`.
- Tag: `cua-driver-rs-v0.28.1`.
- Commit: `d8028a7943087ee258dc1b4d19dc12a7cd27669c`.
- License verified at exact commit: MIT in the component workspace manifest and repository `LICENSE.md`.
- Windows x64 artifact SHA-256: `ab90418aa2efb5a48d6eea1481fb99ae6a93e3fe93c829ee5340d5c50fb5cb1a`.
- Integration classification: external dependency, not copied source.

## Desktop dependency record

### Rusty File Dialog (`rfd`)
- Repository: `PolyMeilex/rfd`.
- Release: `0.17.2`.
- Source ref reviewed: `0.17.2`.
- Upstream release manifest declares license: MIT.
- Hive declaration: exact `=0.17.2`, `default-features = false`.
- Integration classification: crates.io dependency, no copied/modified source.
- Purpose: operating-system native folder selection initiated by explicit user action; it receives no model/task-selected target from the Hive frontend.
- Cargo resolution is committed and RustSec-scanned in Desktop Shell CI.

## Explicit exclusions
OmniParser and Ultralytics are not part of the approved first foundation set. Optional/transitive components require independent provenance/license review before inclusion/distribution.

## Rules
Preserve required copyright/NOTICE/attribution; record source URL/version/commit or release ref and license for imported/dependent code; distinguish dependency use from copied/modified source; do not copy proprietary visual assets; scan transitive/optional dependencies before release; unresolved or incompatible licensing blocks distribution. Foundation binaries are not vendored and automatic install/download remains disabled under HCODER-WO-0002.

No final Hive Coder project license is selected by this checkpoint. A later governed decision must choose it after product/distribution requirements are defined.

## glib 0.18.5 authenticated two-line security backport (HCODER-SEC-0001 Delta 005)

**Classification:** Candidate reproducible, temporary build-time generated local third-party source copy, NOT new runtime download/install authority, NOT yet merged/released. gtk-rs glib 0.18.5 is under the MIT license, as documented by its published gtk-rs source documentation at https://docs.rs/crate/glib/0.18.5 and the upstream crate COPYRIGHT and LICENSE files. Retain all copyright/license files from the original, unchanged crates.io archive; the bootstrap refuses selective extraction. The native system GLib/GTK/WebKit libraries have their own separate licenses (including LGPL obligations): this record does not certify the final product's whole-binary licensing, notices, redistribution or dynamic-linking compliance. Final distribution must separately review that complete bill of materials and preserve attribution.

**Official unmodified source:** glib 0.18.5 registry archive https://static.crates.io/crates/glib/glib-0.18.5.crate pinned exact SHA-256 233daaf6e83ae6a12a52055f568f9d7cf4671dabb78ff9560ab6da230ce00ee5 (matches accepted Cargo.lock package checksum and first-party Ubuntu PR #103 executed proof).

**Security-only external patch:** Debian sid rust-glib-0.18 0.18.5-7 official archived quilt source https://deb.debian.org/debian/pool/main/r/rust-glib-0.18/rust-glib-0.18_0.18.5-7.debian.tar.xz pinned exact SHA-256 9895cf4df3525224ee825477dc76c730566591528b9af9fc05c310706b61db5b. Debian signed source metadata SHA-256 a5079dd1f0cdcdb82b512feab81fe9afab6d79918fe70523015224afa8de0221 authenticated by Ubuntu run 36591726532 against system Debian keyring fingerprint 796DB393DC3FF40222B6EA22D3EBB5966BB99196; signed original Debian source archive SHA-256 faddac41a88c061d4dd577b465ed24ef2b5173c2b0602fc97ae039bbe0079e5c. Only series-listed patch 0007-glib-fix-UB-in-VariantStrIter-impl_get.patch SHA-256 9a3b06ad9a7d5d459d44ee5ab05557720992b8d214bfea14c5e9b4ae4f5702eb is applied. Its sole source-code change is the two-line pointer-mutation correction in src/variant_iter.rs independently matched to https://github.com/gtk-rs/gtk-rs-core/commit/b5a4071e439bef2b5eea76c3aa25e5ae84839e34. The original Debian patch metadata identifies a downstream patch author and must not be republished without its upstream provenance and attribution.

**Supply-chain/build boundary:** project-pinned Python stdlib bootstrap accepts no caller-selected URL, script or key, pins both actual archive hashes and patch digest, inspects without executing downloaded Debian files, rejects archive traversal, unexpected source/code edits and stale existing vendor output. The generated original-with-two-line-patch source is stored in an untracked per-clone path under apps/desktop/src-tauri/vendor/glib-0.18.5; the entire original crate archive and Debian metadata are NOT committed in this repository. Any checkout/build without successful bootstrap must fail closed; verified provenance output itself is not a released signing attestation. No silent crates.io source fallback, proprietary artifact or unreviewed fork. Patch updates and removal must be separately governed once a compatible upstream GTK/Tauri graph fixes the advisory natively.

**Security warning disposition:** RustSec RUSTSEC-2024-0429 registry semver matching does not recognize external downstream two-line patches. Its warning remains visible and requires the actual source/provenance tests, patch maintenance and high-assurance source review here. Do not edit or suppress RustSec/Dependabot warnings to manufacture a clean dependency report. Linux production-distributable status remains BLOCKED until real patched graph package tests on all three OS and exact-head owner risk acceptance; no signing, release, installer or live updater granted by this record.
