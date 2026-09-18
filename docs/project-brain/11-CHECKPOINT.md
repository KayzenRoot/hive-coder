# Checkpoint — Hive Coder

**Declared checkpoint:** `HCODER-CP-0025` — effective under `HCODER_CP_0025_EFFECTIVE`  
**Predecessor checkpoint:** `HCODER-CP-0024` — effective whenever `HCODER_CP_0025_EFFECTIVE` is unsatisfied and `HCODER_CP_0024_EFFECTIVE` is satisfied  
**Earlier checkpoint:** `HCODER-CP-0023` — effective only while both later predicates are unsatisfied  
**Declaration source:** `.engineering/checkpoint-deltas/HCODER-WO-0025.md`, `.engineering/evidence/HCODER-CP-0025-CANONICAL-CLOSEOUT.md`  
**Repository:** `KayzenRoot/hive-coder`

> **Conditional effectiveness.** `HCODER_CP_0025_EFFECTIVE` is satisfied if and only if, for one and the same closeout revision: (a) that exact revision was independently reviewed with unresolved HIGH/CRITICAL `0/0`; (b) that exact revision was governed-merged with expected-head protection; and (c) the resulting exact `main` SHA passed fresh Governance, Desktop Shell **and** Native Package Matrix. The packaging lane belongs in this predicate because this is the slice that introduces packaging: without it a closeout could assert a packaging capability whose own gates were never verified at the closeout stage.
>
> **Checkpoint ladder.** This document selects the authoritative checkpoint by predicate, never by phase. If `HCODER_CP_0025_EFFECTIVE` holds, `HCODER-CP-0025` is authoritative and `DEC-029` is canonical. Otherwise, if `HCODER_CP_0024_EFFECTIVE` holds, `HCODER-CP-0024` is authoritative and `DEC-029` is non-canonical. Otherwise `HCODER-CP-0023` is authoritative. **No edit here is required to flip any status**, and evidence of whether each predicate holds is external lifecycle evidence referenced by Issues #30, #77 and #82 and by the closeout PR carrying the evaluated revision.

## Declared checkpoint: `HCODER-CP-0025` — Native package matrix evidence

**Work Order:** `HCODER-WO-0025` — product implementation MERGED / POSTVALIDATED (immutable product-stage fact)  
**Issue:** `#82`  
**Decision:** `DEC-029` — CANONICAL / SEALED under `HCODER-CP-0025` while `HCODER_CP_0025_EFFECTIVE` is satisfied, non-canonical while it is unsatisfied  
**Slice:** `HCODER-DIST-001B` of parent epic `HCODER-DIST-001` / Issue `#72`  
**Product PR:** `#83` — SQUASH MERGED (expected-head protected)  
**Canonical product merge:** `676138df041c4147df7a5fe3a42b481c0f5e7f13`  
**Reviewed product head:** `a13f3097c47609fbf5dc34e4bab5134ee956b7e0` (tree `41eac2dc19bac61144e66226ce0432350b12a971`, identical to the merge tree)  
**Independent product HEDS:** `5249394339` — APPROVED FOR GOVERNED PRODUCT MERGE, CRITICAL `0` / HIGH `0` / MEDIUM `0`  
**Post-merge exact-main gates:** Governance `35364805912` SUCCESS; Desktop Shell `35364805928` SUCCESS; Native Package Matrix `35364805920` SUCCESS  
**Unresolved HIGH/CRITICAL:** `0/0`

Admits exactly one thing and nothing more: `HCODER-DIST-001B`, as deterministic native package **evidence** generation on Windows, macOS and Linux. A **declared** matrix in which Windows produces `msi`+`nsis`, macOS produces `app`+`dmg` and Linux produces `appimage`+`deb`, with a lane that cannot produce its declared targets failing closed rather than shipping a smaller set; the pinned CLI's **split-build** path (`build --no-bundle`, then an explicit `bundle --bundles`) with canonical `bundle.active` preserved as `false`; the canonical config left unmodified for packaging, with the bundler's required icon declaration supplied as an **ephemeral, runner-local, non-tracked overlay** naming only already-generated deterministic icon inputs and never committed or uploaded; a **closed, deterministic** `hive-package-inventory-v1` manifest bounded to one explicit per-lane package root that refuses absolute paths, traversal, symlink escape, artifacts outside the root, and missing, duplicate, unexpected or zero-size packages, wrong versions and wrong source SHAs; directory bundles hashed as **sorted trees** rather than plain file hashes; non-installing, runner-native structural validation per platform; and short-retention internal workflow artifacts with no release, tag or publication.

Admits **no** signing, codesign, notarization, stapling or publisher-authenticity claim; no release or tag creation and no GitHub Release upload; no updater plugin, endpoint, updater artifact or channel-promotion execution; no product network fetch; no artifact download, install, restart or rollback execution; no installer execution as acceptance; no tracked `bundle.icon` or other canonical-config mutation for packaging; no new dependency, plugin, permission or capability; no expansion of filesystem, Git, shell/process, Cua or credential authority; and no production-distributable claim. `bundle.active` remains `false`.

A digest recorded by this slice proves **byte identity and integrity for evidence transport** only. It is not signing, notarization or publisher authenticity. Packages produced here are deliberately unsigned, unsigned state is never a security success, and nothing in this checkpoint is evidence that Hive Coder is installable, signed, notarized, auto-updatable or production-distributable. `HCODER-DIST-001C` remains explicitly unapproved.

## Predecessor checkpoint: `HCODER-CP-0024` — Distribution version, channel and update boundaries

The record below describes the `HCODER-CP-0024` state, which is authoritative whenever `HCODER_CP_0025_EFFECTIVE` is unsatisfied and `HCODER_CP_0024_EFFECTIVE` is satisfied, and remains preserved as history after that.

**Work Order:** `HCODER-WO-0024` — product implementation MERGED / POSTVALIDATED (immutable product-stage fact)  
**Issue:** `#77`  
**Decision:** `DEC-028` — CANONICAL / SEALED under `HCODER-CP-0024` while `HCODER_CP_0024_EFFECTIVE` is satisfied, non-canonical while it is unsatisfied  
**Product PR:** `#80` — SQUASH MERGED (expected-head protected)  
**Canonical product merge:** `c7f2a5f21369fd92b3493bea0be0192bbd7298b4`  
**Reviewed product head:** `81bdd283dfd299d5ad5035301d06501f6b953a56` (tree `99151781a7cd4a886bf0ea43bb9e29ca44b16cb1`, identical to the merge tree)  
**Independent product HEDS:** `5239135676` — CRITICAL `0` / HIGH `0` / MEDIUM `0`  
**Post-merge exact-main gates:** Governance `35252975365` SUCCESS; Desktop Shell `35252975322` SUCCESS  
**Unresolved HIGH/CRITICAL:** `0/0`

Admits exactly one thing and nothing more: the first governed slice of `HCODER-DIST-001A` as **contracts and inert seams**. A single canonical product-version source with exact mirrors and an offline drift verifier; a toolchain-compatible bounded SemVer 2.0.0 profile with core identifiers within `0..9007199254740991`, a 128-character overall bound, exact decimal-string comparison and one acceptance set shared by the product TypeScript parser and the Python gate through a cross-language parity vector file; release channels `stable`, `beta` and `dev` with version+channel as one identity and no implicit movement; a closed update-state model whose authenticity-dependent states cannot be entered, asserted as a current status, used as a persisted event source or claimed as successfully entered while no scheme is admitted; a semantically closed persisted-event law; closed plain-own-data validation with a zero-getter rule; a bounded read-only About read model; and a Hive-owned inert `UpdateService` boundary.

It admits **no** runtime authority, capability, permission or control-plane path, and no updater plugin, endpoint, network request, download, install, restart, signing, notarization, release publication or `bundle.active=true`. `bundle.active` remains `false`. Packaging, installer generation, updater transport, channel promotion execution, rollback policy and every later `HCODER-DIST-001` slice remain unapproved.

## Earlier checkpoint: `HCODER-CP-0023` — Governed Git Staging Capability

The record below is history: it describes the `HCODER-CP-0023` state, which is authoritative only while `HCODER_CP_0025_EFFECTIVE` and `HCODER_CP_0024_EFFECTIVE` are both unsatisfied, and remains preserved as history after either becomes satisfied.

**Checkpoint:** `HCODER-CP-0023`  
**Status:** SEALED / CANONICAL  
**Date:** 2026-09-16  
**Repository:** `KayzenRoot/hive-coder`  
**Work Order:** `HCODER-WO-0022 — Governed Existing-File Replacement Capability` — COMPLETE / CANONICAL
**Canonicalized increment:** `HCODER-WO-0023 — Governed Git Staging Capability` — COMPLETE / CANONICAL / SEALED; Issue #68 CLOSED / COMPLETED  
**Issue:** `#61` — CLOSED / COMPLETED  
**Product PR:** `#62` — SQUASH MERGED  
**Correction PR:** `#64` — SQUASH MERGED  
**Base checkpoint:** `HCODER-CP-0022` — APPROVED / CANONICAL  
**Canonical base main SHA:** `9c2623f8b335cf29b63b5db5f43e694bfd77938e`  
**CR-001 final exact head:** `12e38e98bb690e29494bab5e7a1c597a64b49765`  
**Correction squash merge:** `35745aa56e203fa819751aee4b70cce57a9600e7`  
**Promotion / final reviewed product head:** `35745aa56e203fa819751aee4b70cce57a9600e7`  
**Canonical product merge SHA:** `06c68611a42e07b85ae765145d94bb613110ac14`  
**Closeout exact head:** `a777ac207b42059a33ce9d73d8287122ff43c0a9`  
**Canonical closeout main SHA:** `795ed101eaf5d770f63a96db7f01a82369be34f1`

## Canonical product state
- All CP-0005 through CP-0021 permission/security/status boundaries remain authoritative and unchanged except where CP-0022 deliberately adds the bounded mutation authority below.
- Hive runtime now has exactly two privileged workspace file mutation adapters behind the Permission & Control Plane: create-only `write_file_v1` admitted by CP-0021 and replacement `replace_file_v1` admitted by CP-0022.
- The CP-0022 admitted operation is fixed `replace_file_v1` under `Capability.FILESYSTEM_WRITE`. Approval binds canonical workspace identity, normalized target, live parent identity, exact observed old target identity, old content SHA-256/length, new content SHA-256/length and contract version. Raw old/new content is excluded from approval/audit metadata.
- The executor revalidates live workspace, parent, target identity and old content as late as safely possible, then consumes a short-lived request-bound single-use permit at the mutation-ready boundary and publishes by platform-proven atomic namespace replacement.
- Capability-created temporary objects are cleaned up only after their identity/ownership is verified and ownership of the live pathname can be proven.
- `.git`, traversal, non-regular targets, symlink/reparse traversal, outside-workspace mutation, permit bypass and authority expansion fail closed. Unsupported platform/filesystem combinations expose capability unavailability and fail closed.
- CP-0021's `write_file_v1` create-only/no-clobber boundary remains canonical and preserved.

## Explicit residual-race law
CP-0022 canonicalizes **bounded-race atomic replacement**, explicitly **not** strict expected-target or expected-inode CAS. An uncooperative external process may alter the destination pathname after Hive's final successful observable revalidation and before the native atomic publication call where the platform interface exposes no expected-target predicate. This interval is explicit and bounded by the selected contract and must never be renamed or represented as strict CAS.

## Explicitly unapproved authority
Append, truncate-in-place, delete, arbitrary rename/move, recursive mutation, chmod/chown, Git mutation, generic filesystem mutation, shell/terminal/process execution, Tauri/desktop write commands, provider/model execution or credentials, Cua/computer-use mutation beyond prior governed boundaries, remote control, automatic skill activation and billing/purchase authority remain outside CP-0022.

## Correction closure
- `.engineering/corrections/HCODER-WO-0022-CR-001.md` and `.engineering/evidence/HCODER-WO-0022-CAS-FEASIBILITY.md` record the transition from an unprovable strict-CAS claim to the bounded-race contract.
- Unresolved HIGH/CRITICAL findings: **0**.

## Evidence chain
CR-001 exact head `12e38e98bb690e29494bab5e7a1c597a64b49765` passed Governance #322 and Desktop Shell #158 with native Windows HIGH_ASSURANCE and dedicated macOS proof; HEDS CR-001 review `5222036573`, H/C `0/0`; correction squash-merged as `35745aa56e203fa819751aee4b70cce57a9600e7`.

Product exact head `35745aa56e203fa819751aee4b70cce57a9600e7` passed Governance #323 and Desktop Shell #159; HEDS final product review `5222076357`, H/C `0/0`; PR #62 squash-merged as `06c68611a42e07b85ae765145d94bb613110ac14`. That exact `main` SHA passed post-merge Governance #324 and Desktop Shell #160.

CP-0022 closeout exact head `a777ac207b42059a33ce9d73d8287122ff43c0a9` passed Governance #325 and Desktop Shell #161 with HEDS closeout review `5222180870`, H/C `0/0`; merged as `795ed101eaf5d770f63a96db7f01a82369be34f1`. Post-closeout `main` validation passed Governance #326 and Desktop Shell #162.

## Canonical decision
`DEC-026 — Governed Existing-File Replacement Capability` is **CANONICAL**, promoted by `HCODER-CP-0022` with closeout merge `795ed101eaf5d770f63a96db7f01a82369be34f1`. It canonicalizes only bounded-race atomic replacement of one already-existing regular workspace file behind the Permission & Control Plane.

## Downstream increments in flight
- `HCODER-WO-0025` native package matrix is the declared checkpoint above: its product implementation is **MERGED / POSTVALIDATED**, and its canonical standing is governed entirely by `HCODER_CP_0025_EFFECTIVE`. Its closeout is the documentation-only revision declared in `.engineering/checkpoint-deltas/HCODER-WO-0025.md` and `.engineering/evidence/HCODER-CP-0025-CANONICAL-CLOSEOUT.md`; that revision's own review, gates and merge are the predicate's mutable inputs, whose evidence is external lifecycle evidence referenced by Issues #30 and #82, not here.
- `HCODER-PLATFORM-001` (Issue #63) first-class native validation matrix is materialized on `main` at `22b56b0f3111158cbf50789b1647c5a578a171c1` and its evidence ledger reconciled at `ccfed1f960c80dc58e4f45cb627451e77c7d5a79`. Its evidence ledger remains **PREBUILT / NATIVE MATRIX INCOMPLETE**: Linux and macOS native desktop/Tauri exact-head evidence is still required. It is **not** a checkpoint and must not be represented as complete.
- `HCODER-WO-0023` governed Git staging is **SEALED / CANONICAL** under `HCODER-CP-0023`. Product PR #69 squash-merged with expected-head protection as `1f09520fbd92c7e65f9726b65a854f918507c895`, validated on that exact `main` by Governance `35171215292` and Desktop Shell `35171215429`. The documentation-only closeout PR #75 squash-merged with expected-head protection as `1b83666699acc8fdbd5270d811f1bf263d55ef47`, validated on that exact `main` by Governance `35204919678` and Desktop Shell `35204919616`. Native Linux, Windows HIGH_ASSURANCE and macOS governed Git staging proof passed on each exact `main`. The final-seal PR #76 squash-merged with expected-head protection as `b6297fbe4de4681fc92093f3691f693dc2de0dc1`, validated on that exact `main` by Governance `35210910407` and Desktop Shell `35210910423`. `b6297fbe...` is the **final-seal merge SHA** and the **validated `main` at final-seal validation** — an immutable lifecycle-stage fact, not a live repository pointer. Independent technical HEDS `5229345968` at `b827cb2e`: CRITICAL `0` / HIGH `0`. Issue #68 is CLOSED / COMPLETED.

  Its admitted authority is exactly `Capability.GIT_WRITE` / `git_stage_paths_v1` (HIGH, materially sensitive, mandatory trusted approval, request-bound single-use permit) for explicit regular files in the already-proven ordinary local SHA-1 envelope. The independent A4/HEDS review `5229345968` at the reviewed head `b827cb2eaa04eb2efa3ffb0b9aa7a82cbb7c672a` returned CRITICAL `0` / HIGH `0`, and native governed Git staging proof passed independently on Windows HIGH_ASSURANCE, Linux and macOS at that head.

  The Work Order is **merged and post-seal validated**, and Issue #68 is **CLOSED / COMPLETED**. Publication is atomic publication, explicitly not strict CAS. No commit, ref, branch, remote, credential, shell, generic Git argv or arbitrary `.git` write authority is approved by it.

## Preserved downstream lanes
Distribution/update: Issue #72.
Premium UX/UGAS/themes/i18n/notifications/project navigator: Issue #71.

## Residual boundaries
- Append/truncate-in-place, delete and arbitrary rename/move remain unapproved.
- Git mutation beyond the canonical bounded `Capability.GIT_WRITE` / `git_stage_paths_v1` staging authority remains unapproved, as does terminal/shell execution. Commit, ref/branch/tag, remote, network, credential, generic Git argv and arbitrary `.git` write authority remain unapproved.
- Internal unsigned native package **evidence generation** is admitted under `HCODER-CP-0025` while `HCODER_CP_0025_EFFECTIVE` is satisfied. Signing, codesign, notarization, stapling, release/tag publication, updater transport and rollback/roll-forward proof remain open, as does any production-distributable claim.
- Runtime-status sidecar packaging/signing/attestation and packaged live E2E remain open.
- RustSec warning-class dependency debt, stricter CSP, native/full desktop E2E, visual/accessibility automation and final license remain open.
- Linux and macOS desktop-native validation remain open under `HCODER-PLATFORM-001`.

## Next NECESSARY governed increment
Run a fresh source-check from this canonical checkpoint and select only the next objectively necessary product increment. Future implementation work should be prebuilt with contracts, skeletons, tests, fixtures, acceptance criteria and bounded context before execution-heavy coding.
