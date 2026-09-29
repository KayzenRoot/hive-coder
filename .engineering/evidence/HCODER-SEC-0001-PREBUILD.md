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
