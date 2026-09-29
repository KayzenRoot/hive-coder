# HCODER-SEC-0001 — Bounded source/context lock

**Stage:** ANALYSIS-ONLY PREBUILD / PROPOSED; **Issue:** #97.
**Branch:** `security/HCODER-SEC-0001-glib-reachability-prebuild`.
**Source base:** `main 4ee0894ad79bd869b1ed4668ea33e151f0ef18ff`.
**Source checkpoint:** CP-0027 / DEC-031 EFFECTIVE by PR #98 stage A+B+C, with historically canonical CP-0026/DEC-030 retained; evidence in Issues #30/#89, PR #98.
**Scope:** three exact prebuild documentation files; no runtime/manifest/workflow/security code changes.
**External HIVE:** NOT REQUIRED; all source lives in Git, GitHub and internal repos.
**Reviewer:** owner-only KayzenRoot, always `OWNER_SELF_AUDIT / NOT_INDEPENDENT` with objective CI.

## Locked base Git blobs
- `apps/desktop/src-tauri/Cargo.lock`: `517f181e3c0e1e281e12e270ae2b5e23922c5f35`.
- `apps/desktop/src-tauri/Cargo.toml`: `2ab3c506dff4ff9c546a523941536678632fb2f9`.
- `docs/project-brain/11-CHECKPOINT.md`: `1f7f8323ae08687ab727fdbb84ae9849c3b889d1`.
- `docs/project-brain/05-SECURITY.md`: `1cede4091b2f27523eccca4e3febe1eb3c1bc248`.
- `docs/project-brain/08-BACKLOG.md`: `6577b7636a6b6440d4c8aeb4fc99217204300f3b`.
- `docs/project-brain/09-DEFINITION-OF-DONE.md`: `ab4f81b4c1fdc70b0ab4c69e2026f14bd46e11d1`.
- `docs/project-brain/10-DECISIONS-LEDGER.md`: `399dd2278ec9439a2d2ace466bd6b61cd91a76b2`.
- `apps/desktop/src-tauri/tauri.conf.json`: `3cc63516a5065bcc115e3274a66eed74f15f0cab`.
- `apps/desktop/src-tauri/src/update_admission.rs`: `234e40fdd5d805e30d44f824a3cea416d348b7c9`.

## Observed risk and unknowns
Git lock graph includes `glib=0.18.5`, `gtk=0.18.2`, `webkit2gtk=2.0.2`, `tauri=2.11.5`. RustSec RUSTSEC-2024-0429 fixed in glib>=0.20.0. Optional Dependabot patch run 36579704036 reported `security_update_not_possible`. First-party/transitive GTK `VariantStrIter` call reachability is UNKNOWN. Hosted CI for the merged inert updater, including Rust and package builds, has passed, but this does NOT prove that the vulnerable iterator is unreachable or that Linux release security is clean.

## Frozen/security boundaries
Entire product tree, manifests/lock, source/checkpoint historical receipts, approved trust, protected CI configuration and security gates. No production distribution, external HIVE preflight or collaborator approval. Owners may inspect; no code/lock modifications without an accepted scoped correction and compatible supported remediation. Treat alternate Tauri/GTK branches as unverified until objectively probed, never as already compatible.

## STALE / RECOMPILE
If actual `main`, advisory/upstream fix, dependency graph, ruleset, package semantics or accepted CP changes materially, refresh the fingerprints and re-evaluate the bounded Work Order before any edit. Only current proof on exact HEAD carries. The issue remains OPEN until the actual security risk is remediated or a separately governed bounded disposition is proven. GitHub automation or signed artifact credentials must never be enabled to make this prebuild pass.


## Correction Delta 002 Context Lock — authenticated-backport candidate research, 2026-09-29

**No retroactive change to the initial prebuild or temporary diagnostic Delta 001.** This append-only Delta is documentation research, not product implementation. Same HCODER-SEC-0001 / Issue #97. Branch: `security/HCODER-SEC-0001-debian-backport-provenance`; immutable source `main 93f0cc314699788e7e405d46de62f8d8bab3c759` (postvalidated prebuild PR #99). CP-0027/DEC-031 effective, DEC-032/033 owner-only/no external HIVE effective. Temporary diagnostic PR #100 remains CLOSED/UNMERGED; its exact successful Linux runner run `36585888151` belongs to its candidate HEAD and is contextual evidence only, not this branch's CI.

**Critical immutable source Git blob SHA:**
- `apps/desktop/src-tauri/Cargo.lock`: `517f181e3c0e1e281e12e270ae2b5e23922c5f35`.
- `apps/desktop/src-tauri/Cargo.toml`: `2ab3c506dff4ff9c546a523941536678632fb2f9`.
- `docs/project-brain/11-CHECKPOINT.md`: `1f7f8323ae08687ab727fdbb84ae9849c3b889d1`.
- `docs/project-brain/10-DECISIONS-LEDGER.md`: `399dd2278ec9439a2d2ace466bd6b61cd91a76b2`.
- `docs/project-brain/03-SCOPE.md`: `5413f15135fc19ddebf9aa86e4be722cd9aa83df`.
- `docs/project-brain/09-DEFINITION-OF-DONE.md`: `ab4f81b4c1fdc70b0ab4c69e2026f14bd46e11d1`.
- `docs/project-brain/04-ARCHITECTURE.md`: `10ac18d2d187e8f13ca2a4071499a667fe13cc35`.
- `docs/project-brain/05-SECURITY.md`: `1cede4091b2f27523eccca4e3febe1eb3c1bc248`.

**Exact allowed tracked paths** on THIS draft candidate:
1. `.engineering/work-orders/HCODER-SEC-0001.md` — append Correction Delta 002.
2. `.engineering/context-locks/HCODER-SEC-0001.md` — append this lock.
3. `.engineering/evidence/HCODER-SEC-0001-PREBUILD.md` — append new externally sourced research, explicitly unexecuted.

All other tracked files are FROZEN. No source archive download/execution, `[patch.crates-io]`, glib vendoring, Cargo update, CI workflow, GTK transition, unconfigured trust or credential/provisioning mutation is permitted by this DOCS-ONLY Delta. Public upstream Debian metadata and upstream gtk-rs patch are research inputs, not approvals. Require a second separately bounded executable correction amendment before any local Cargo/security branch.

**STALE predicate:** compare actual `main` SHA and critical fingerprints before review/merge; if they drift, STOP and recompile. Never reuse exact-head protected CI, owner audit or postmerge evidence from prior candidate or PR #100 as this PR's proof. Linux production distribution remains blocked; real `VariantStrIter` transitive reachability remains UNKNOWN; six credential-bearing protected-release lanes remain SKIPPED. No new canonical checkpoint.


## Correction Delta 005 Context Lock — HIGH_ASSURANCE actual patched Cargo product branch (not merged)

**Immutable source:** protected main f4f000ec03c3fd96f73b1c6370c57c286557cee5; **branch** security/HCODER-SEC-0001-glib-patched-product, same active HCODER-SEC-0001 / Issue #97. CP-0027/DEC-031 CANONICAL, owner self-review NOT_INDEPENDENT, no separate HIVE service. No source/ruleset/decision drift may be silently rebased. Previous A0 source-signed provenance PR #102 CLOSED UNMERGED run 36591726532 and A1/A2 patched Linux Cargo proof PR #103 CLOSED UNMERGED exact run 36593636245/job 109492833532 passed 49 desktop Rust and four release-optimized direct VariantStrIter tests. Original product remains unpatched and blocked for Linux distribution.

**Critical protected-main source blobs at preflight:**
- apps/desktop/src-tauri/Cargo.lock = 517f181e3c0e1e281e12e270ae2b5e23922c5f35;
- apps/desktop/src-tauri/Cargo.toml = 2ab3c506dff4ff9c546a523941536678632fb2f9;
- apps/desktop/src-tauri/src/update_admission.rs = 234e40fdd5d805e30d44f824a3cea416d348b7c9;
- docs/project-brain/11-CHECKPOINT.md = 1f7f8323ae08687ab727fdbb84ae9849c3b889d1;
- docs/project-brain/10-DECISIONS-LEDGER.md = 399dd2278ec9439a2d2ace466bd6b61cd91a76b2;
- docs/project-brain/03-SCOPE.md = 5413f15135fc19ddebf9aa86e4be722cd9aa83df;
- docs/project-brain/09-DEFINITION-OF-DONE.md = ab4f81b4c1fdc70b0ab4c69e2026f14bd46e11d1;
- docs/project-brain/04-ARCHITECTURE.md = 10ac18d2d187e8f13ca2a4071499a667fe13cc35;
- docs/project-brain/05-SECURITY.md = 1cede4091b2f27523eccca4e3febe1eb3c1bc248;
- docs/project-brain/14-LICENSE-PROVENANCE.md = 63d63836412b75e76d54152d4f35a5bde3a5bb4b;
- .gitignore = 609d28e2925f664f21b400d37e664d54665efff2;
- .github/workflows/desktop-shell.yml = 7eb76979345c554dacc1b3a5fac0a26a0019367e;
- .github/workflows/native-package-matrix.yml = 118bbbe8f453dd130852d97a40b2e0781ab71d92;
- .engineering/work-orders/HCODER-SEC-0001.md = 298acad6fbefd50731e02c0d890e883900515d7b;
- .engineering/context-locks/HCODER-SEC-0001.md = 3746641337e6ebc2b812ab43c94f112f68bd2846;
- .engineering/evidence/HCODER-SEC-0001-PREBUILD.md = faa212ccda55baf3044984aa178f7602b1b604a6.

**External immutable source anchors:** crates.io glib 0.18.5 archive SHA256 233daaf6e83ae6a12a52055f568f9d7cf4671dabb78ff9560ab6da230ce00ee5; Debian 0.18.5-7 .dsc SHA256 a5079dd1f0cdcdb82b512feab81fe9afab6d79918fe70523015224afa8de0221 signed by distro keyring fingerprint 796DB393DC3FF40222B6EA22D3EBB5966BB99196; signed Debian orig SHA256 faddac41a88c061d4dd577b465ed24ef2b5173c2b0602fc97ae039bbe0079e5c; Debian .debian.tar.xz SHA256 9895cf4df3525224ee825477dc76c730566591528b9af9fc05c310706b61db5b; unique series-listed security patch 0007-glib-fix-UB-in-VariantStrIter-impl_get.patch SHA256 9a3b06ad9a7d5d459d44ee5ab05557720992b8d214bfea14c5e9b4ae4f5702eb; independently verified upstream gtk-rs commit b5a4071e439bef2b5eea76c3aa25e5ae84839e34. Signed source proof belongs to earlier Ubuntu run; each platform's production build must separately verify pinned checksums before a local patch overlay may exist. Upstream glib 0.18.5 license MIT; system library licenses/attribution need separate source/distribution evaluation.

**Twelve-path closed mutation list:** .engineering/work-orders/HCODER-SEC-0001.md, .engineering/context-locks/HCODER-SEC-0001.md, .engineering/evidence/HCODER-SEC-0001-PREBUILD.md, docs/project-brain/14-LICENSE-PROVENANCE.md, .gitignore, apps/desktop/src-tauri/Cargo.toml, apps/desktop/src-tauri/Cargo.lock, tools/desktop/bootstrap_glib_patch.py, tools/desktop/glib_rustc_wrapper.rs, tests/desktop/test_glib_patch_provenance.py, .github/workflows/desktop-shell.yml, .github/workflows/native-package-matrix.yml. All product Rust/TS/frontend and existing security gate, canonical checkpoint/decisions, release/governance and no other files are FROZEN.

**CI/review STOP:** real modified Cargo graph must be tested on all three OS for Desktop Shell and Native Package Matrix, with per-run actual archive and lock provenance receipts and original source reproducibility; all 13 protected contexts exact same product HEAD SUCCESS; six credential jobs truthful SKIPPED; no unresolved HIGH/CRITICAL; owner exact-head NOT_INDEPENDENT security challenge and protected expected-head squash retaining reviewed tree, fresh exact resulting-main four workflows SUCCESS before any accepted product claim. Separate explicit production Linux distribution risk gate after source acceptance; never silently clear or close Issue #97 just from this proposal.


## Correction Delta 005 C01 Context Lock — original registry advisory shadow

**Same immutable parent** main f4f000ec03c3fd96f73b1c6370c57c286557cee5, same branch security/HCODER-SEC-0001-glib-patched-product, unchanged twelve-path allowlist and critical blob fingerprints recorded above. Underlying source remains the exact hash-pinned crates.io glib 0.18.5 plus the authenticated Debian two-line security patch. NO modifications to runtime Rust/TS, original source Cargo vendor bytes, updater, protected Governance or Protected Release workflow, credentials, HIVE service or installed software.

**Objective reason:** first real product PR #104 initial head 2153f4b4aa7cbb1bd388610d395f31e27968bbf1 and optimized regression interim head 7c09615ecf33b83897eba5f3149f378b70477013 both finished all 13 exact-head required contexts. The latter's Windows ordinary patched-lock cargo audit emitted six informational warnings instead of seven in prior registry-original diagnostic; the missing known glib RUSTSEC-2024-0429 warning is a detection visibility gap caused by the local source identity, not grounds for a clean-security claim. This head cannot be merged without an explicit original-advisory shadow audit.

**Exact C01 sub-scope inside the already-approved twelve paths:** tools/desktop/bootstrap_glib_patch.py adds an offline runner-temp-only original registry lock reconstructor and strict parser of cargo-audit JSON; tests/desktop/test_glib_patch_provenance.py adds two adverse sentinel/reconstructor tests; Windows job ONLY in .github/workflows/desktop-shell.yml performs an additional pinned cargo audit on the reconstructed original registry identity lock and requires RUSTSEC-2024-0429 glib0.18.5 visible in warnings.unsound with settings.ignore=[] and zero new vulnerabilities. The ordinary current patched-lock audit still runs; no waiver of either scan, no new tracked path and no change to actual Cargo graph. App/updater/release authority frozen. Final evidence must come from NEW identical amended HEAD, not those previous approved CI runs. Linux production-distribution remains BLOCKED and Issue #97 OPEN after product source review.
