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
