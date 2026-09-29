# HCODER-SEC-0001 — Linux glib advisory dependency/reachability prebuild

**Status:** PROPOSED / ANALYSIS ONLY / NOT YET CANONICAL
**Issue:** #97
**Exact base:** `main 4ee0894ad79bd869b1ed4668ea33e151f0ef18ff` / `HCODER-CP-0027` effective.
**Risk:** ELEVATED dependency-security analysis; production Linux security posture withheld.
**Source lock:** `.engineering/context-locks/HCODER-SEC-0001.md`.
**Review:** `KayzenRoot` substantive exact-head `OWNER_SELF_AUDIT / NOT_INDEPENDENT`; no other account mandatory; 13 hosted status contexts and guarded merge.

## OBJECTIVE
Establish a reproducible, bounded dependency chain and vulnerability/reachability assessment for the pre-existing Linux GTK3 `glib 0.18.5` advisory RUSTSEC-2024-0429 (GHSA-wrw7-89jp-8q8g) before selecting a separately authorized migration or qualified mitigation. Avoid swapping unsound cargo versions, disabling checks, accepting production Linux distribution, or expanding the already canonical but inert Rust updater bridge.

## CONTEXT / EVIDENCE
The immutable audited source base has `apps/desktop/src-tauri/Cargo.lock` `glib=0.18.5`, `gtk=0.18.2`, `webkit2gtk=2.0.2`, `tauri=2.11.5`. `apps/desktop/src-tauri/Cargo.toml` directly pins `tauri=2.11.5` and `tauri-plugin-updater=2.12.0`. Optional Dependabot security update failed at run 36579704036. The upstream RustSec advisory identifies affected `glib>=0.15,<0.20` iterator implementations and patched `glib>=0.20.0`; this fact is upstream security evidence, not proof that Hive Coder exercises the affected iterator.

Official upstream: https://rustsec.org/advisories/RUSTSEC-2024-0429.html
Issue: https://github.com/KayzenRoot/hive-coder/issues/97

## ANALYSIS-ONLY SCOPE / DELIVERABLES
1. Read source authority in order: accepted CP-0027/DEC-031 and preserved CP-0026, Decisions Ledger, Scope, DoD, Architecture/Security, this Work Order and exact lock, protected CI workflows and unchanged product tree. Confirm no separate installed HIVE service, no collaborator required, and no actual signing/provisioned updater.
2. Record exact current local/dependency fingerprints and path-scoped `cargo tree -i glib@0.18.5` on a supported Linux runner or local read-only cargo environment, the complete relevant cargo-audit advisory set and `Cargo.lock` transitive graph. If unavailable, mark `UNPROVEN`, not PASS.
3. Trace reachable calls of the affected `glib::VariantStrIter` iterator from first-party Rust source and, where trustworthy source tools allow, the actual shipped transitive GTK/WebKit graph. Distinguish `not referenced by first-party source` from `proved unreachable`; the latter requires evidence, never assumption. Mark dynamic transitive use UNKNOWN when not provable.
4. Compare **supported** upstream Tauri/wry/webkit2gtk/GTK alternatives and published compatibility for Rust/MSRV, Linux system packages, updater plugin v2.12, signed-version guarantee, Windows/macOS packaging and the frozen foundation contracts. Consider a maintained upstream fix or approved vendor backport only if evidence can establish support and security provenance. Do not cherry-pick unreviewed crate versions.
5. Produce a deterministic decision matrix of at least: supported full-graph migration, upstream-published backport, justified restricted Linux distribution, unresolved/blocked with Linux release withheld. State tests/negative cases, changed-path proposal, expected impact and STOP for each, avoiding a made-up compatibility winner.
6. Record A0-A4 proof map: source, cargo tree/audit, focused unit/negative tests, native three-OS package/desktop workflows, source security review, all 13 required protected checks, postmerge proof. Real Linux reachability/distribution proof stays UNKNOWN until executed.

## CLOSED TRACKED FILE SCOPE OF THIS PREBUILD
- `.engineering/work-orders/HCODER-SEC-0001.md` (this document)
- `.engineering/context-locks/HCODER-SEC-0001.md`
- `.engineering/evidence/HCODER-SEC-0001-PREBUILD.md`

GitHub Issue #97 and prebuild PR conversation may receive factual evidence/comments without creating tracked runtime changes. Product source, Cargo.toml/lock, GitHub Actions, current Checkpoint/Decisions Ledger, signing/trust/updater config, Windows/macOS release behavior, local Docker or external HIVE remain FROZEN. Real remediation requires a **separate bounded correction delta under the same Issue/Work Order** naming exact code/dependency paths, evidence and tests before any implementation edits.

## ACCEPTANCE / REVIEW
Prebuild acceptance requires: exact source match, reproduced dependent graph or explicit external runtime blocker, upstream advisory confirmation, bounded reachability/alternatives and no claim of a clean Linux release, all 13 applicable exact-head GitHub status contexts SUCCESS, zero unresolved HIGH/CRITICAL/scope findings, owner semantic audit labeled NOT INDEPENDENT, guarded expected-head squash and fresh exact-main required checks. No new semantic security authority or release is minted by analysis-only prebuild. Freeze any migration execution until this prebuild's own accepted checkpoint/proof and delta scope.

## STOP CONDITION
STOP on unverified dependency graph, unspecified local test result, forced mixed GTK ABI, undocumented audit suppression, missing upstream provenance, updater-trust/authz expansion, source/branch drift, failed required CI, false clean-Linux claim or another unreviewed Work Order collision. If migration is blocked, preserve issue #97 OPEN and withhold Linux production-distributable status; do not reduce the security bar to achieve a green review.


## Correction Delta 002 — authenticated-backport feasibility research (documentation only; 2026-09-29)

**Same Work Order:** HCODER-SEC-0001 / Issue #97. **Source main:** `93f0cc314699788e7e405d46de62f8d8bab3c759`. **Branch:** `security/HCODER-SEC-0001-debian-backport-provenance`. CP-0027/DEC-031 remains CANONICAL; no runtime authority or new checkpoint is requested. **Classification:** NECESSARY to determine whether a concrete maintained-backport candidate exists after accepted Linux diagnostic PR #100 (closed UNMERGED).

### OBJECTIVE / CONTEXT

Resolve the prior research gap without pretending Linux is secure: collect primary upstream patch provenance and authenticated Debian downstream release evidence for `glib 0.18.5` and specify a separately gated local feasibility probe before any product or Cargo mutation. The Linux feature-resolved diagnostic at PR #100 exact `58edc952503713aef8d6c798b25c5d482c0899fa`, Actions run `36585888151`, already proved the affected GTK3 graph is selected, `cargo audit` returns seven INFO warnings including RUSTSEC-2024-0429, and literal source references outside glib were not observed. Dynamic reachability remains UNKNOWN. No new Linux build is claimed for this Delta.

### NEW PRIMARY PUBLIC SOURCES (research, NOT implementation proof)

- Upstream gtk-rs/gtk-rs-core PR #1343, MERGED 2024-03-30: https://github.com/gtk-rs/gtk-rs-core/pull/1343 ; original correction changes `VariantStrIter::impl_get` from immutable `&p` to mutable `&mut p`, with `let mut p`. Upstream commit independently verified in gtk-rs repository: `b5a4071e439bef2b5eea76c3aa25e5ae84839e34` (https://github.com/gtk-rs/gtk-rs-core/commit/b5a4071e439bef2b5eea76c3aa25e5ae84839e34); Debian security tracker links the upstream PR.. Upstream advisory: https://rustsec.org/advisories/RUSTSEC-2024-0429.html ; registry's fixed-range remains `glib>=0.20`.
- Debian **official packaged backport candidate**: `rust-glib-0.18 0.18.5-7` published in Debian sid on 2026-08-13 by DebianOnMobile Maintainers / Arnaud Ferraris. Debian signed changelog explicitly says `d/patches: import fix for RUSTSEC-2024-0429` and closes Debian bug #1143114: https://bugs.debian.org/1143114 ; public package index https://packages.debian.org/sid/arm64/rust/librust-glib-0.18-dev ; Debian security-tracker commit https://salsa.debian.org/security-tracker-team/security-tracker/-/commit/49fedc7b621f6754fa9b8883a330a648aa4d2afc. **The published downstream Debian patch and its source archive have not yet been downloaded, signature/hash-verified, compared byte-for-byte with the upstream fix or executed in this repository.** Debian package version does NOT upgrade crates.io `glib 0.18.5` by itself.
- Official published `tauri 2.12.0` Cargo manifest STILL declares Linux `gtk=0.18`, `webkit2gtk=2`, default `wry`: https://docs.rs/crate/tauri/2.12.0/source/Cargo.toml . Therefore a Tauri 2.12 bump alone is not a demonstrated full-graph resolution; Tauri 3 alpha/GTK4/CEF is not a supported production drop-in.

### SCOPE / OUT OF SCOPE / FILES TO READ

**This Delta authorizes only three append-only documentation changes** on this branch: the present Work Order, `.engineering/context-locks/HCODER-SEC-0001.md`, `.engineering/evidence/HCODER-SEC-0001-PREBUILD.md`. Read Issue #30 current header; accepted CP-0027 predicate and DEC-031/032/033; Scope, DoD, Architecture, Security; exact original security Work Order/Context Lock; Issue #97 and Linux runner evidence; upstream PR/advisory; Debian signed changelog, source metadata and any subsequently authenticated actual patch. Source base and critical blob fingerprints are in the appended lock. No product source, `Cargo.toml`, `Cargo.lock`, vendoring, CI/workflows, signing, updater trust, install/restart, publication, external HIVE, collaborator, or unrestricted access change is authorized by THIS Delta.

### NEXT GATED PROBE (proposal only, requires its OWN accepted executable correction amendment)

1. Obtain Debian `0.18.5-7` `.dsc` and matching original+Debian source archives via the official Debian source mirror. Verify Debian signature/key chain where available, hashes from the `.dsc`, patch paths, licensing, exact Debian backport diff and equality to the upstream fix's security-critical lines. Pin provenance and archive/patch SHA-256; reject unverifiable or broader changes. A distribution source package is evidence of a maintained backport, NOT permission to substitute its system crate into a Cargo build.
2. In an isolated, nonrelease diagnostic branch, compare two **possible** fully specified techniques rather than selecting one by assumption: a repository-local, audited `[patch.crates-io]` copy of only `glib 0.18.5` with authenticated patch, versus an official upstream-supported end-to-end GTK4/Tauri graph when one exists. Verify Cargo resolves precisely one intended patched glib source across GTK3/WebKit/tray/tao/Wry, and validate source checksum/SBOM. No unauthenticated Git forks, version spoofing, dynamic registry override or unreviewed mixed GTK ABI.
3. For any proposed patch branch, require security regression exercising `VariantStrIter` in optimized Rust (including `next`, `next_back`, `nth`, `nth_back`, `last`) and negative/integrity tests for forged patch/checksum, missing patch, mismatched source, forced conflicting glib, mismatched resolved graph and version/status misrepresentation. Compare Rust 1.98.1, Tauri 2/updater 2.12 signed-version and no-downgrade law, three-OS desktop/native packaging and 13 exact-head protected contexts. Run real commands before claiming PASS. Keep RustSec advisory visible even if its semver-only check cannot recognize a documented backport; never turn an ignored INFO finding into clean-audit proof.
4. Record a source-security threat assessment, source/provenance licensing and longer-term patch ownership/upgrade policy. Retain Linux production-distribution BLOCK until the **implemented exact tree** is rigorously tested, reviewed and production acceptance separately governed; no actual signing or release implied.

### ACCEPTANCE / TESTS / DELIVERABLES / REVIEW / STOP

**This research-only Delta's acceptance:** exactly three append-only docs; sources and limitations accurately attributed; exact-base fingerprints; no code/config/workflow diffs; all 13 applicable exact-head checks/four workflows SUCCESS; substantive exact-head `OWNER_SELF_AUDIT / NOT_INDEPENDENT` with 0 unresolved HIGH/CRITICAL, no blocking threads; expected-head guarded squash; four fresh postmerge exact-main workflow SUCCESS. Proposed Checkpoint Delta = NONE. This authorizes candidate feasibility research, not implementation or Linux distribution.

**STOP** on main/source drift, missing authentic patch bytes/signature/hash, broader or unmaintained backport, an unsupported Tauri/GTK migration, unverified Cargo source substitution, feature/MSRV/ABI incompatibility, missing optimized regression or cross-OS proof, suppressed advisories, any unresolved HIGH/CRITICAL or missing required CI. Keep Issue #97 OPEN and all external signing/provisioning/unconfigured updater restrictions unchanged.
