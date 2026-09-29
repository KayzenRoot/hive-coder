# HCODER-SEC-0001 — Initial source/risk evidence (prebuild candidate)

**Source main:** `4ee0894ad79bd869b1ed4668ea33e151f0ef18ff`; **Issue:** #97.
**Known source (not independently executed local cargo tree):**
- `Cargo.lock` Git blob `517f181e3c0e1e281e12e270ae2b5e23922c5f35` contains `glib 0.18.5`, `gtk 0.18.2`, `webkit2gtk 2.0.2`, `tauri 2.11.5`.
- `Cargo.toml` Git blob `2ab3c506dff4ff9c546a523941536678632fb2f9` directly pins `tauri=2.11.5` and `tauri-plugin-updater=2.12.0`.
- Optional Dependabot failed security-patch job `36579704036`, reported `security_update_not_possible`; patching `glib` alone must not be forced across incompatible gtk3 graph.
- RustSec RUSTSEC-2024-0429: unsound `glib::VariantStrIter` next/next_back/nth/nth_back/last in glib>=0.15,<0.20; patched >=0.20.0. Primary: https://rustsec.org/advisories/RUSTSEC-2024-0429.html ; identifier GHSA-wrw7-89jp-8q8g.
- The old pre-updater base already held glib 0.18.5, so the risk predates product PR #93 and was not introduced by it. **Real call-path reachability UNKNOWN**. Do not claim no exposure just because first-party Rust source did not directly mention the iterator.

**Accepted source/CI prerequisite:** CP-0027 now effective from docs-only promotion PR #98 reviewed `03870429b3d27c964c954e0e12528e0b8b799688`, guarded-squash-merged as `4ee0894ad79bd869b1ed4668ea33e151f0ef18ff`, reviewed and merged tree `7280ba1bdbe864cb2de9564378b4f0421e73060e`; FRESH main Governance 36582946882, Desktop Shell 36582946744, Native Package Matrix 36582946827, Protected Release 36582946781 SUCCESS; 13 protected contexts SUCCESS, six credential-bearing stages SKIPPED. This is base proof, NOT a security repair.

**Pending required evidence slots:** actual Linux `cargo tree -i glib@0.18.5 --locked` (verify exact CLI and feature graph), full current RustSec advisory output; variant iterator reachability/path tracing; supported upstream compatibility and patch/backport provenance; explicit migration/mitigation feasibility and negative-test matrix; exact-head hosted gates and scoped owner review for this prebuild; guarded merge, exact-main postvalidation; later separately approved real remediation proof.

**Current decision:** ANALYSIS ONLY; issue OPEN; Linux production distribution still withheld. Risk unresolved/production-gated. Do not claim prebuild CI or owner approval until they actually exist; PR/Issue to hold exact-final-head receipts after immutable docs commit.

## Static lockfile reverse dependency graph (reproducible bounded analysis)

The accepted base `Cargo.lock` Git blob `517f181e3c0e1e281e12e270ae2b5e23922c5f35` was parsed directly (483 `[[package]]` records), and each `dependencies` array was inverted to enumerate immediate parents of the sole locked `glib@0.18.5`. These are *locked-package relations*, **not** feature/target-resolved `cargo tree` output and not an executed Linux proof.

Immediate parents of `glib@0.18.5` in the lockfile: `atk@0.18.2`, `cairo-rs@0.18.5`, `gdk@0.18.2`, `gdk-pixbuf@0.18.5`, `gdkx11@0.18.2`, `gio@0.18.4`, `gtk@0.18.2`, `javascriptcore-rs@1.1.2`, `libappindicator@0.9.0`, `pango@0.18.3`, `soup3@0.5.0`, `webkit2gtk@2.0.2`.

Representative locked reverse chains into the desktop:
- `glib@0.18.5 <- gtk@0.18.2 <- tauri@2.11.5 <- hive-coder-desktop@0.1.0`.
- `glib@0.18.5 <- webkit2gtk@2.0.2 <- tauri@2.11.5 <- hive-coder-desktop@0.1.0`.
- `glib@0.18.5 <- gtk@0.18.2 <- tauri-runtime-wry@2.11.4 <- tauri@2.11.5`.
- `glib@0.18.5 <- soup3@0.5.0 <- wry@0.55.1 <- tauri-runtime-wry@2.11.4`.
- `glib@0.18.5 <- webkit2gtk@2.0.2 <- wry@0.55.1 <- tauri-runtime-wry@2.11.4`.

`webkit2gtk-sys@2.0.2` is present and is used by `webkit2gtk@2.0.2` and `wry@0.55.1`; `tao@0.35.3` and `muda@0.19.3` also depend on locked `gtk@0.18.2`. A public upstream Tauri issue (https://github.com/tauri-apps/tauri-docs/issues/3143) documents the larger GTK3/GTK4 transition and `glib<0.20` unsoundness motivation; it is design context, **not** proof that Hive Coder's pinned Tauri 2.11.5 graph can upgrade in place.

GitHub's indexed default-branch source search for literal `VariantStrIter` returned **0 matches**. This is only absence of that literal in indexed repository files; transitive GTK/WebKit use and dynamic runtime reachability **remain UNKNOWN**.

**Remaining source/evidence gap:** no actual target-resolved Linux `cargo tree -i glib@0.18.5 --locked` run, fresh full cargo-audit report capture, call-site analysis of all transitive crates or evidence of a supported fully compatible patched Tauri/GTK/WebKit dependency set. Those are required before implementation scope opens. No arbitrary partial package upgrade or suppression has been performed.


## Correction Delta 002 — new authenticated downstream backport *candidate* (public research, 2026-09-29)

**Source:** immutable accepted main `93f0cc314699788e7e405d46de62f8d8bab3c759` and current Critical Git blob fingerprints in the appended Context Lock. **No repo binary/manifest/source/workflow edits or local dependency commands were performed by this research.** Issue #97 remains OPEN. Previous diagnostic runner `36585888151` conclusively selects `glib 0.18.5` in the Ubuntu x86_64 Tauri 2/GTK3 graph and captured seven RustSec INFO warnings, but not reachability proof or mitigation.

### Evidence provenance and limitations

| Finding | Primary source | Evidence status | Important bound |
|---|---|---|---|
| Precise upstream fix | gtk-rs PR https://github.com/gtk-rs/gtk-rs-core/pull/1343 merged 2024-03-30 and RustSec https://rustsec.org/advisories/RUSTSEC-2024-0429.html; upstream fix SHA `b5a4071e439bef2b5eea76c3aa25e5ae84839e34` independently verified at https://github.com/gtk-rs/gtk-rs-core/commit/b5a4071e439bef2b5eea76c3aa25e5ae84839e34 (Debian tracker separately links the upstream PR) | PUBLIC_SOURCE_CONFIRMED | Defect in glib `VariantStrIter::impl_get`: `let mut p`/`&mut p` rather than immutable `&p`. RustSec version registry still marks all `0.18.x` unpatched without backport awareness. |
| Debian-maintained downstream backport candidate | Debian signed package changelog in https://bugs.debian.org/1143114 ; Debian sid `rust-glib-0.18 0.18.5-7` metadata https://packages.debian.org/sid/arm64/rust/librust-glib-0.18-dev ; Debian security tracker change https://salsa.debian.org/security-tracker-team/security-tracker/-/commit/49fedc7b621f6754fa9b8883a330a648aa4d2afc | PUBLISHED_DOWNSTREAM_PACKAGE_CONFIRMED | Debian explicitly records `d/patches: import fix for RUSTSEC-2024-0429` in its 2026-08-13 `0.18.5-7` release. Exact patch bytes/source signature/hash **NOT YET VERIFIED IN THIS REPOSITORY**. System package does not automatically patch crates.io Cargo resolution. |
| Latest stable Tauri 2 has not crossed gtk3 version ceiling | Published Tauri 2.12.0 source manifest https://docs.rs/crate/tauri/2.12.0/source/Cargo.toml | PRIMARY_PUBLISHED_MANIFEST | Its Linux target still names `gtk = 0.18`, `webkit2gtk = 2`, default `wry`; a Tauri-only version bump is NOT shown to fix our whole selected graph. Actual Tauri 2.12 graph/build not executed here. |
| Diagnostic retained | https://github.com/KayzenRoot/hive-coder/issues/97#issuecomment-5892750374 ; Ubuntu PR-only run https://github.com/KayzenRoot/hive-coder/actions/runs/36585888151 | PREVIOUS_EXACT_PR_RUN, NOT CURRENT_PR_CI | Locked `glib 0.18.5` selected; seven INFO warnings including UNSOUND; 13 literal references in glib's own crate only in bounded grep. Dynamic/transitive reachability remains UNKNOWN. |

### Feasibility choices under the SAME Issue/WO (no selected implementation)

| Candidate | Proof required before mutation | Current disposition |
|---|---|---|
| Officially supported patched full Linux graph | Published stable Tauri/GTK/WebKit/Wry/tao/tray graph `glib>=0.20`, MSRV, cross-OS runtime/packaging and updater signed-version invariants | NOT PROVEN. Published stable Tauri 2.12.0 still selects gtk 0.18 at manifest level. |
| Debian-authenticated scoped 0.18 backport applied to exact Cargo source | Official signed original+Debian source archive+patch SHA-256 verification; byte diff matches upstream security fix; explicitly audited local Cargo source/lock identity; optimized iterator regression+negative tests; full selected graph+cross-OS/CI evidence; patch maintenance/replacement policy | **NEW RESEARCH CANDIDATE**, not authorized to implement and not accepted as a release fix yet. |
| Threat-bounded Linux distribution restriction | Rigorous dynamic reachable-call proof or clearly documented risk bounds + separately accepted HIGH_ASSURANCE release decision | UNPROVEN; existing restriction remains in force. |
| Unresolved upstream-supported option | Preserve fail-closed Linux distribution gate and keep Issue #97 OPEN while upstream support evolves | CURRENT ACTUAL PRODUCT STATUS. |

### A0–A4 proof ledger for proposed next isolated executable amendment

- A0: exact source and immutable fingerprints documented. Public upstream + Debian release existence confirmed. **Actual downloaded source/signature/patch hashes: UNPROVEN**.
- A1: prior PR #100 target/feature-resolved `cargo tree`, pinned RustSec JSON and source grep are recorded on **its own** SHA; a patched Cargo graph is **NOT RUN**.
- A2: optimized patched-`VariantStrIter` regression and adverse provenance/graph mutation tests: **NOT RUN / NOT AUTHORIZED THIS DELTA**.
- A3: patched dependency full Rust/test/MSRV, updater v2 signed-version guard, Ubuntu/Windows/macOS desktop/package CI and all thirteen exact-head checks: **NOT RUN for any patch**. Four required workflows on this new docs PR: **PENDING**.
- A4: exact docs-only owner audit, guarded merge and fresh postmerge four workflow outcomes for this new docs research PR: **PENDING**. Risk acceptance for an eventual backport or Linux release: **NOT GRANTED**.

**Research conclusion:** Debian's dated packaged fix materially narrows the previous no-known-backport research gap but is neither an authenticated patch-bytes receipt nor upstream support for arbitrary vendoring. This analysis does not convert `cargo audit exit 0` into a clean security result, does not assert that vulnerable paths are unreachable, and does not unblock Linux production distribution. NEXT necessary gate: verify the actual Debian patch and source provenance on a bounded isolated runner under a separately accepted executable Correction Delta; if not verifiable, remain BLOCKED. Checkpoint Delta: NONE.


## Correction Delta 004 — patched Cargo overlay diagnostic A1/A2 reserved (TEMPORARY unmerged branch)

**Base:** protected main f4f000ec03c3fd96f73b1c6370c57c286557cee5; same HCODER-SEC-0001 Issue #97. A0 provenance independently VERIFIED in temporary PR #102 exact 146214f22687db3fe8d2220a989c35387a5554ec, run 36591726532/job 109486247334; PR CLOSED UNMERGED. Official Debian source .dsc signature verified with Debian distro keyring signer 796DB393DC3FF40222B6EA22D3EBB5966BB99196; exact Debian archive SHA256 9895cf4df3525224ee825477dc76c730566591528b9af9fc05c310706b61db5b; signed original tar SHA256 faddac41a88c061d4dd577b465ed24ef2b5173c2b0602fc97ae039bbe0079e5c; one series-listed patch 0007-glib-fix-UB-in-VariantStrIter-impl_get.patch SHA256 9a3b06ad9a7d5d459d44ee5ab05557720992b8d214bfea14c5e9b4ae4f5702eb matched upstream two-line security fix. Full A0 receipt: Issue #97 comment 5893528964.

**A1/A2 new exact runner evidence slots PENDING, NOT YET EXECUTED:** crates.io original glib 0.18.5 checksum verified against exact Cargo.lock; Debian signed-original vulnerable-file preimage equals registry locked source; copy-only strict application of exact security patch (no fuzz); only one changed patched file and adverse checks for patch preimage/reapply/corrupt hashes; precisely one patched glib instance in feature/target-resolved scratch Cargo graph; pinned Rust 1.98.1 check + product tests retaining updater v2 signed-version/no-downgrade compile guard; optimized direct VariantStrIter tests including forward, reverse, nth, nth_back, last and extreme index; no production source writes. Report any RustSec INFO warning truthfully.

**A3/A4 UNPROVEN:** patched-product cross-OS native packaging/desktop/build, full HIGH_ASSURANCE threat review and release recovery, actual signing/publishing, installer and live updater. Even positive A1/A2 is Linux-only feasibility, never a production Linux release claim. Issue #97 stays OPEN; CP-0027/DEC-031 unchanged; no new checkpoint. Temporary PR CLOSED UNMERGED after inspection.
