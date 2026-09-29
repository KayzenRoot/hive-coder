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
