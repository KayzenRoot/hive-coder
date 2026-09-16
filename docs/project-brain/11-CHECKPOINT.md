# Checkpoint — Hive Coder

**Checkpoint:** `HCODER-CP-0021`  
**Status:** APPROVED / CANONICAL  
**Date:** 2026-09-15  
**Repository:** `KayzenRoot/hive-coder`  
**Work Order:** `HCODER-WO-0021 — Trusted Workspace File Capability & Permit-Gated Mutation Boundary` — COMPLETE / CANONICAL  
**Issue:** `#57` — CLOSED / COMPLETED  
**Product PR:** `#58` — SQUASH MERGED  
**Closeout PR:** `#59` — SQUASH MERGED  
**Base checkpoint:** `HCODER-CP-0020` — APPROVED / CANONICAL  
**Canonical base main SHA:** `c1f4166497d07eea6758e00f8a6d201e2b9acc02`  
**Technical head:** `12d86579335c8f553bf77457739a6f2a7d287f10`  
**Technical HEDS:** `5217411336`  
**Promotion head:** `9f82d7211aa7ae304d4045623ab1c27911c12a14`  
**Promotion HEDS:** `5217449846`  
**Final reviewed product head:** `347dc69ab97e48d75f72d16df3bb34347da09c69`  
**Final product HEDS:** `5217471428`  
**Canonical product merge SHA:** `ee2e01e99aaea89deb2754ba8295fe34d7744541`  
**Canonical closeout HEDS:** `5217531877`  
**Canonical closeout main SHA:** `200540c2605ff4e5c32f54cd1c3be40dbd167520`

## Canonical product state
- All CP-0005 through CP-0020 permission/security/status boundaries remain authoritative and unchanged except where CP-0021 deliberately adds the bounded mutation authority below.
- Hive runtime has exactly one privileged workspace file mutation adapter admitted by CP-0021.
- The admitted operation is fixed `write_file_v1` under `Capability.FILESYSTEM_WRITE` and is create-only/no-clobber for a previously absent regular file.
- Permission & Control Plane remains the sole authorization choke point. Trusted approval is mandatory; model/tool/task/file content cannot mint permits.
- Approval binds canonical workspace identity, normalized target, live parent identity, target-absent state, content SHA-256 and byte length. Raw content is excluded from approval/audit metadata.
- Executor revalidates live session/workspace/parent/target state and consumes the short-lived request-bound single-use permit immediately before mutation.
- Traversal, `.git`, symlink/reparse, non-portable/confusing path forms, identity drift, target races, stale/replayed/wrong permits and payloads above 1 MiB fail closed.
- POSIX and Windows use platform-specific handle/no-follow/no-clobber publication paths; a concurrent target owner is preserved.

## Explicitly unapproved authority
Existing-file overwrite/edit/append/truncate, delete/rename-existing, generic filesystem mutation, Git mutation, shell/terminal/process execution, Tauri/desktop write commands, provider/model execution or credentials, Cua/computer-use mutation beyond prior governed boundaries, remote control, automatic skill activation and billing/purchase authority remain outside CP-0021.

## Correction closure
- Hosted Windows rejected the initial root-relative publication primitive. The same Work Order moved to native NT handle-relative no-clobber rename without weakening the contract.
- Real NTFS junction/reparse and publication-race tests were added.
- Independent audit closed `.git` mutation and Unicode/control path-confusion gaps.
- Unresolved HIGH/CRITICAL findings: **0**.

## Evidence chain
Technical head `12d86579335c8f553bf77457739a6f2a7d287f10` passed Governance #278 and Desktop Shell #114; HEDS `5217411336` approved promotion.

Promotion head `9f82d7211aa7ae304d4045623ab1c27911c12a14` passed Governance #281 and Desktop Shell #117; HEDS `5217449846` approved final approval mutation.

Final product head `347dc69ab97e48d75f72d16df3bb34347da09c69` passed Governance #282 and Desktop Shell #118; HEDS `5217471428` approved squash merge.

PR #58 squash-merged as `ee2e01e99aaea89deb2754ba8295fe34d7744541`. Exact product merge SHA passed Governance #283 and Desktop Shell #119.

Documentation-only closeout head `eec525cbf48439c5722cef624b25e8ff9203d9e0` passed Governance #284 and Desktop Shell #120; HEDS `5217531877` approved canonical closeout merge.

PR #59 squash-merged as `200540c2605ff4e5c32f54cd1c3be40dbd167520`. That exact `main` SHA passed Governance #285 and Desktop Shell #121, including Windows HIGH_ASSURANCE, locked Rust/Tauri build, launch smoke, frontend contracts and dependency/security audits.

## Canonical decision
`DEC-025 — Trusted Workspace File Capability & Permit-Gated Mutation Boundary` is **APPROVED / CANONICAL**. It canonicalizes only atomic create-only/no-clobber workspace file creation behind the Permission & Control Plane.

## Residual boundaries
- Existing-file replacement/edit remains unapproved.
- Git mutation and terminal/shell execution remain unapproved.
- Installer/signing/updater/release packaging and rollback/roll-forward proof remain open.
- Runtime-status sidecar packaging/signing/attestation and packaged live E2E remain open.
- RustSec warning-class dependency debt, stricter CSP, native/full desktop E2E, visual/accessibility automation and final license remain open.

## Next NECESSARY governed increment
Run a fresh source-check from this canonical checkpoint and select only the next objectively necessary product increment. Future implementation work should be prebuilt with contracts, skeletons, tests, fixtures, acceptance criteria and bounded context before execution-heavy coding.