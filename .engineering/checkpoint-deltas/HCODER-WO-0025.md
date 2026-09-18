# Checkpoint Delta / Closeout — HCODER-WO-0025

**Status:** DURABLE CLOSEOUT DECLARATION — CONDITIONAL EFFECTIVENESS (`HCODER_CP_0025_EFFECTIVE`)  
**Work Order:** `HCODER-WO-0025 — Native Package Matrix Evidence Contract`  
**Declared decision state:** `DEC-029` — CANONICAL / SEALED under `HCODER-CP-0025`, effective under the predicate below  
**Issue:** `#82`  
**Parent epic:** `HCODER-DIST-001` / Issue `#72`  
**Slice:** `HCODER-DIST-001B`  
**Product PR:** `#83` — squash merged with expected-head protection  
**Canonical product merge:** `676138df041c4147df7a5fe3a42b481c0f5e7f13`  
**Disclosed conflicts:** none

## Effectiveness predicate

`HCODER_CP_0025_EFFECTIVE` is satisfied if and only if all three hold for one and the same closeout revision:

- (a) that exact closeout candidate revision was independently reviewed with unresolved HIGH/CRITICAL `0/0`;
- (b) that exact revision was governed-merged with expected-head protection;
- (c) the resulting exact `main` SHA passed fresh Governance, Desktop Shell **and** Native Package Matrix.

**Before** the predicate is satisfied, `HCODER-CP-0024` and the non-canonical `DEC-029` state remain authoritative. **Once** it is satisfied, `HCODER-CP-0025` and `DEC-029` are CANONICAL / SEALED under the declaration in this document, with no repository-document rewrite required merely to flip phase or status wording.

The predicate deliberately depends on no merge SHA, run ID, review ID, Issue state, PR state or moving `current main` field. Evidence of whether it is satisfied lives externally in the active closeout PR and Issues #30 and #82.

The Native Package Matrix belongs in this predicate and not in its predecessor's: this slice is the one that introduces a packaging lane, so a closeout that canonicalized it while its own gates could go unverified would assert a packaging capability on the strength of runs belonging to a different stage.

## Purpose

Declare the canonical outcome of the governed native-package-matrix slice. The **product** implementation is merged and exact-main postvalidated as recorded below; this document supplies the durable closeout declaration whose effect is governed by the predicate above.

This delta creates no new authority and changes no behaviour. It records lifecycle and canonical status only.

## What is admitted (already merged and postvalidated)

`HCODER-DIST-001B`, as deterministic native package **evidence** generation only:

- **One declared native package matrix per platform.** Windows produces `msi` and `nsis`; macOS produces `app` and `dmg`; Linux produces `appimage` and `deb`. The matrix is declared rather than discovered, and a lane that cannot produce its declared targets fails closed instead of quietly shipping a smaller set.
- **The pinned CLI's split-build model.** Packaging is a native compile with `--no-bundle` followed by an explicit `bundle --bundles` invocation naming its targets. `bundle.active` remains `false` in the canonical config, because explicit bundling does not require activating global bundling.
- **The canonical config is not packaging config.** `apps/desktop/src-tauri/tauri.conf.json` remains the canonical version source and is unmodified for packaging. The icon declaration the bundler requires and the canonical config does not carry is supplied as an **ephemeral, runner-local, non-tracked overlay** naming only already-generated deterministic icon inputs. Each lane proves tracked source and the canonical config's bytes are unchanged after bundling.
- **Closed, deterministic package evidence.** A generated package set is described by the closed schema `hive-package-inventory-v1`, carrying source SHA, canonical version, platform, architecture and one entry per package with type, relative path, byte size, digest algorithm, digest and the portable structural checks that passed. Discovery is bounded to one explicit package root created fresh per lane; ordering and serialization are deterministic. Absolute paths, traversal, symlink escape, artifacts outside the root, and missing, duplicate, unexpected or zero-size packages, wrong versions and wrong source SHAs are all refused.
- **Directory bundles are hashed as trees.** A macOS `.app` is described by a documented deterministic sorted-tree digest, never as a plain file hash, so a changed, added or removed file inside the bundle changes the recorded digest.
- **Non-installing, runner-native structural validation.** Each lane validates only what its platform can validate without installing: install metadata and version on Windows, `hdiutil verify` for disk images on macOS, package metadata for Debian archives on Linux, and format/magic/executable-bit checks for the file formats that carry them.
- **Internal evidence only.** Workflow artifacts carry generated packages and their inventory manifest under a short explicit retention window. There is no GitHub Release, no tag creation, no release-asset upload and no production publication, and no installer is ever executed to satisfy acceptance.

## What remains explicitly unapproved

No signing, codesign, notarization, stapling or any publisher-authenticity claim; no release or tag creation and no GitHub Release upload; no updater plugin, update endpoint, updater artifact or channel-promotion execution; no product network fetch; no artifact download, install, restart or rollback behaviour; no installer execution as acceptance; no tracked `bundle.icon` or any other canonical-config mutation for packaging; no new product dependency, plugin, permission or capability; no expansion of filesystem, Git, shell/process, Cua or credential authority; and no production-distributable claim. `bundle.active` remains `false`.

This checkpoint also does not approve any later `HCODER-DIST-001` slice. `HCODER-DIST-001C` remains explicitly unapproved.

## Evidence is not trust

A digest recorded by this slice proves **byte identity and integrity for evidence transport**. It is not signing, not notarization and not a publisher-authenticity proof. Packages produced by this pipeline are deliberately unsigned, and unsigned state is never reported as a security success. An unsigned package that passes every structural check in the matrix is evidence that a packaging pipeline works, not evidence that the artifact can be trusted to install.

## Lifecycle evidence (immutable stage facts)

| Stage | Fact |
|---|---|
| Independently reviewed product head | `a13f3097c47609fbf5dc34e4bab5134ee956b7e0` |
| Reviewed-head tree | `41eac2dc19bac61144e66226ce0432350b12a971` |
| Independent product HEDS | `5249394339` — APPROVED FOR GOVERNED PRODUCT MERGE, CRITICAL `0` / HIGH `0` / MEDIUM `0` |
| Pre-merge base `main` | `3e1e1af7596c56716825206587bf2a88e1b179d0` |
| Product merge (squash, expected-head protected) | `676138df041c4147df7a5fe3a42b481c0f5e7f13` |
| Merge tree | `41eac2dc19bac61144e66226ce0432350b12a971` — identical to the reviewed-head tree |
| Post-merge Governance | `35364805912` SUCCESS on that exact merge SHA |
| Post-merge Desktop Shell | `35364805928` SUCCESS on that exact merge SHA |
| Post-merge Native Package Matrix | `35364805920` SUCCESS on that exact merge SHA — all three lanes |

Post-merge exact-main validation covered Governance source-pack, governed-runtime Linux, control-plane Windows HIGH_ASSURANCE and workspace-replace macOS; Desktop web, Windows, Linux and macOS; and Native Package Matrix Windows, Linux and macOS with all six package targets produced at `VERSION_DRIFT=LOCKED` and `TRACKED_SOURCE_UNCHANGED=PASS`. Every required lane belonged to the merge SHA; none was inferred from an adjacent commit. Production lanes used runs triggered by the merged `main` itself, never the PR-head runs that preceded the merge.

These are immutable lifecycle-stage facts and are not live repository pointers. The *closeout* stage's own review, gates and merge evidence are deliberately **not** recorded here: they are the mutable inputs to `HCODER_CP_0025_EFFECTIVE` and live externally in the active closeout PR and Issues #30 and #82. This document therefore stays true whether or not the predicate has been satisfied.

## Not changed by this delta

No product behaviour, runtime authority, contract law, workflow behaviour, dependency state or test semantics changes. The matrix law, split-build law, overlay law, inventory law, tree-digest law and the evidence-is-not-trust boundary are exactly as independently reviewed at `a13f3097`. What this closeout declaration governs is lifecycle/canonical status only, and only through the predicate above.

## STOP CONDITION

This declaration grants no additional authority, capability, scope or behaviour change. `HCODER-CP-0025` and `DEC-029` carry canonical force only while `HCODER_CP_0025_EFFECTIVE` is satisfied, and no repository text asserts that it is. No further repository mutation under `HCODER-WO-0025` is authorised by it. Any new product behaviour requires a newly governed Work Order with its own Context Lock, allowed files and exact-head gates.
