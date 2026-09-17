# Checkpoint — Hive Coder

**Checkpoint:** `HCODER-CP-0023`  
**Status:** CANONICAL (closeout seal pending this closeout PR)  
**Date:** 2026-09-16  
**Repository:** `KayzenRoot/hive-coder`  
**Work Order:** `HCODER-WO-0022 — Governed Existing-File Replacement Capability` — COMPLETE / CANONICAL
**Canonicalized increment:** `HCODER-WO-0023 — Governed Git Staging Capability` — PRODUCT MERGED / POST-MERGE VALIDATED; closeout pending  
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
- `HCODER-PLATFORM-001` (Issue #63) first-class native validation matrix is materialized on `main` at `22b56b0f3111158cbf50789b1647c5a578a171c1` and its evidence ledger reconciled at `ccfed1f960c80dc58e4f45cb627451e77c7d5a79`. Its evidence ledger remains **PREBUILT / NATIVE MATRIX INCOMPLETE**: Linux and macOS native desktop/Tauri exact-head evidence is still required. It is **not** a checkpoint and must not be represented as complete.
- `HCODER-WO-0023` governed Git staging is **CANONICAL on `main`** under `HCODER-CP-0023`. Product PR #69 squash-merged with expected-head protection as `1f09520fbd92c7e65f9726b65a854f918507c895`, whose exact-`main` push validation passed Governance `35171215292` and Desktop Shell `35171215429`, including native Linux, Windows HIGH_ASSURANCE and macOS governed Git staging proof. The closeout may be sealed only after the documentation-only closeout PR merges and post-closeout `main` is validated.

  Its admitted authority is exactly `Capability.GIT_WRITE` / `git_stage_paths_v1` (HIGH, materially sensitive, mandatory trusted approval, request-bound single-use permit) for explicit regular files in the already-proven ordinary local SHA-1 envelope. The independent A4/HEDS review `5229345968` at the reviewed head `b827cb2eaa04eb2efa3ffb0b9aa7a82cbb7c672a` returned CRITICAL `0` / HIGH `0`, and native governed Git staging proof passed independently on Windows HIGH_ASSURANCE, Linux and macOS at that head.

  This checkpoint records an **approval on this branch only**. The Work Order is **not merged**, canonical main has **not** received it, no post-merge validation has occurred, and the Work Order is **not closed**. Publication is atomic publication, explicitly not strict CAS. No commit, ref, branch, remote, credential, shell, generic Git argv or arbitrary `.git` write authority is approved by it.

## Preserved downstream lanes
Distribution/update: Issue #72.
Premium UX/UGAS/themes/i18n/notifications/project navigator: Issue #71.

## Residual boundaries
- Append/truncate-in-place, delete and arbitrary rename/move remain unapproved.
- Git mutation and terminal/shell execution remain unapproved.
- Installer/signing/updater/release packaging and rollback/roll-forward proof remain open.
- Runtime-status sidecar packaging/signing/attestation and packaged live E2E remain open.
- RustSec warning-class dependency debt, stricter CSP, native/full desktop E2E, visual/accessibility automation and final license remain open.
- Linux and macOS desktop-native validation remain open under `HCODER-PLATFORM-001`.

## Next NECESSARY governed increment
Run a fresh source-check from this canonical checkpoint and select only the next objectively necessary product increment. Future implementation work should be prebuilt with contracts, skeletons, tests, fixtures, acceptance criteria and bounded context before execution-heavy coding.
