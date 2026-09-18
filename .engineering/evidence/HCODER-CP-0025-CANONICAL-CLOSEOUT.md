# HCODER-CP-0025 — Canonical Closeout

**Status:** DURABLE CLOSEOUT DECLARATION — CONDITIONAL EFFECTIVENESS (`HCODER_CP_0025_EFFECTIVE`)  
**Work Order:** `HCODER-WO-0025`  
**Decision:** `DEC-029`, CANONICAL / SEALED under `HCODER-CP-0025` while the predicate below is satisfied  
**Canonical predecessor:** `HCODER-CP-0024`  
**Product PR:** `#83` — SQUASH MERGED (expected-head protected)  
**Product merge SHA:** `676138df041c4147df7a5fe3a42b481c0f5e7f13`  
**Issue:** `#82`

## Effectiveness predicate

`HCODER_CP_0025_EFFECTIVE` is satisfied if and only if all three hold for one and the same closeout revision:

- (a) that exact closeout candidate revision was independently reviewed with unresolved HIGH/CRITICAL `0/0`;
- (b) that exact revision was governed-merged with expected-head protection;
- (c) the resulting exact `main` SHA passed fresh Governance, Desktop Shell **and** Native Package Matrix.

Before the predicate is satisfied, `HCODER-CP-0024` and the non-canonical `DEC-029` state remain authoritative. Once it is satisfied, `HCODER-CP-0025` and `DEC-029` are CANONICAL / SEALED under this declaration with no repository-document rewrite required. The predicate depends on no merge SHA, run ID, review ID, Issue state, PR state or moving `current main` field: evidence of whether it holds lives externally in the active closeout PR and Issues #30 and #82.

The third condition is specific to this checkpoint. `HCODER-CP-0024`'s predicate required Governance and Desktop Shell; a closeout of the slice that *introduces* packaging must additionally require the packaging lane on its own exact merged `main`, or it would canonicalize a packaging capability without ever having verified that capability at the closeout stage.

## Canonical boundary

`HCODER-CP-0025` closes `HCODER-DIST-001B`: deterministic generation of native package **evidence** across Windows, macOS and Linux with the declared six-target matrix. It canonicalizes an evidence contract and its generation pipeline, not a distribution capability.

It admits **no** signing, notarization, release, updater, installation or publication authority. Nothing in this checkpoint signs, notarizes, staples, publishes, tags, uploads a release asset, contacts an update endpoint, downloads an artifact, executes an installer, installs, restarts or rolls back. No filesystem, Git, shell, Cua, credential or runtime authority is broadened by it.

## Canonical matrix law

The package matrix is **declared, not discovered**: Windows produces `msi` and `nsis`, macOS produces `app` and `dmg`, and Linux produces `appimage` and `deb`. A lane that cannot produce one of its declared targets fails closed; the matrix is never silently reduced to whatever a lane happened to build. All six targets, on their native runners and architectures, are part of the contract rather than a best-effort aspiration.

## Canonical split-build and overlay law

Packaging uses the pinned CLI's split path: a native compile with `--no-bundle`, then an explicit `bundle --bundles` invocation naming its targets. `bundle.active` remains `false` in the canonical config, because explicit bundling does not require activating global bundling and flipping it would change how every existing desktop lane behaves.

`apps/desktop/src-tauri/tauri.conf.json` remains the canonical version source and is **not** packaging config. Where the bundler requires an icon declaration the canonical config does not carry, that declaration is supplied as an **ephemeral, runner-local, non-tracked overlay** naming only already-generated deterministic icon inputs. The overlay is never committed, never uploaded as an artifact, and never becomes a surface of authority. Each lane proves, after bundling, that canonical tracked source and the canonical config's bytes are unchanged.

## Canonical inventory law

Package evidence is closed and deterministic. A generated package set is described by the closed schema `hive-package-inventory-v1`, carrying the source SHA, canonical version, platform, architecture and exactly one entry per package with its type, relative path, byte size, digest algorithm, digest and the portable structural checks that passed. Discovery is bounded to one explicit package root created fresh per lane, and manifest ordering and serialization are deterministic, so the same artifact set always yields byte-identical output.

Absolute paths, traversal, symlink escape, artifacts outside the root, and missing, duplicate, unexpected or zero-size packages, wrong versions and wrong source SHAs are refused rather than tolerated. A macOS `.app` is hashed with a documented deterministic **sorted-tree** digest and never represented as a plain file hash, so a changed, added or removed file inside the bundle changes the recorded digest.

## Canonical evidence-is-not-trust law

A digest proves **byte identity and integrity for evidence transport**. It is not signing, not notarization and not a publisher-authenticity proof. Packages produced by this pipeline are deliberately unsigned, and unsigned state is never reported as a security success. Nothing in this checkpoint may be read as evidence that Hive Coder is installable, signed, notarized, auto-updatable, published or production-distributable.

## Explicitly unapproved authority

No signing, codesign, notarization, stapling or publisher-authenticity claim; no release or tag creation and no GitHub Release upload; no updater plugin, update endpoint, updater artifact or channel-promotion execution; no product network fetch; no artifact download, install, restart or rollback execution; no installer execution as acceptance; no tracked `bundle.icon` or any other canonical-config mutation for packaging; no new product dependency, plugin, permission or capability; no expansion of filesystem, Git, shell/process, Cua or credential authority; and no production-distributable claim. `bundle.active` remains `false`. `HCODER-DIST-001C` remains unapproved.

## Evidence chain (immutable stage facts)

- Independently reviewed product head `a13f3097c47609fbf5dc34e4bab5134ee956b7e0`, tree `41eac2dc19bac61144e66226ce0432350b12a971`; independent HEDS `5249394339` APPROVED FOR GOVERNED PRODUCT MERGE with unresolved CRITICAL `0` / HIGH `0` / MEDIUM `0`.
- Product PR #83 squash-merged with expected-head protection as `676138df041c4147df7a5fe3a42b481c0f5e7f13`; the merge tree equals the reviewed-head tree exactly, so the merge introduced no content change and the reviewed bytes are the shipped bytes.
- Post-merge exact-main validation: Governance `35364805912` SUCCESS, Desktop Shell `35364805928` SUCCESS and Native Package Matrix `35364805920` SUCCESS on that merge SHA, the last covering all three lanes with all six package targets produced at `VERSION_DRIFT=LOCKED` and `TRACKED_SOURCE_UNCHANGED=PASS`, and with the ephemeral overlay never uploaded.

The recorded preflight history of this slice — an initial STOP because the Windows `msi` target could not be produced from the canonical configuration, followed by a bounded continuation authorising an ephemeral overlay — is preserved in the Work Order, the Context Lock and the `DEC-029` ADR. Correction chronology and the reviewed-head record are likewise preserved there and are not restated here. The closeout stage's own review, gates and merge evidence are the mutable inputs to `HCODER_CP_0025_EFFECTIVE`; they are not recorded in this committed package and live externally in the active closeout PR and Issues #30 and #82, so this document remains true whether or not the predicate has been satisfied.

## Canonical decision

`DEC-029 — Native Package Matrix Evidence Contract` is declared **CANONICAL / SEALED** under `HCODER-CP-0025`, effective under `HCODER_CP_0025_EFFECTIVE` and non-canonical while that predicate is unsatisfied. This checkpoint canonicalizes the bounded matrix, split-build, overlay, inventory and evidence-is-not-trust law described above and nothing beyond it.

## Closeout promotion gates

This declaration becomes effective only through the predicate above. Concretely, the promotion requires:

1. exact-head Governance on the closeout revision to be SUCCESS;
2. exact-head Desktop Shell on that revision to be SUCCESS;
3. exact-head Native Package Matrix on that revision to be SUCCESS, documentation-only changes notwithstanding;
4. an independent review of that exact revision reporting unresolved HIGH/CRITICAL `0/0`;
5. a governed merge of that exact revision with expected-head protection;
6. the resulting exact `main` SHA to pass fresh Governance, Desktop Shell and Native Package Matrix;
7. every closeout change to remain documentation/governance only, without broadening runtime authority or altering the reviewed contract law.

While the predicate holds, `HCODER-WO-0025` is complete, `DEC-029` is CANONICAL with this checkpoint as its promotion evidence, and Issue #82 may be closed. Whether each of those has happened is external state recorded in the active closeout PR and Issues #30 and #82, not in this document.

## STOP CONDITION

Do not assert that `HCODER-CP-0025` or `DEC-029` carry canonical force except while `HCODER_CP_0025_EFFECTIVE` is satisfied. Do not begin `HCODER-DIST-001C` from this declaration. This document never claims a phase: it states the predicate and the conditional outcome, so it remains true both before and after the closeout merge.
