# DEC-025 — Trusted Workspace File Capability & Permit-Gated Mutation Boundary

**Status:** APPROVED / FINAL CANDIDATE — NOT CANONICAL  
**Work Order:** `HCODER-WO-0021`  
**Source checkpoint:** `HCODER-CP-0020`  
**Target checkpoint:** `HCODER-CP-0021`  
**Technical head:** `12d86579335c8f553bf77457739a6f2a7d287f10`  
**HEDS technical:** `5217411336`  
**Promotion head:** `9f82d7211aa7ae304d4045623ab1c27911c12a14`  
**HEDS promotion:** `5217449846`

## Decision
Hive Coder may introduce its first privileged Hive-owned workspace file mutation adapter behind the canonical Permission & Control Plane. The admitted authority is deliberately narrow: create exactly one previously absent regular file inside the trusted workspace using atomic no-clobber publication.

## Authority law
- Capability is exactly `FILESYSTEM_WRITE`; action is fixed `write_file_v1`.
- `FILESYSTEM_WRITE` remains HIGH and mandatory trusted-approval gated.
- Model, tool, task and file content cannot approve a challenge or mint a permit.
- The approved request binds workspace identity, normalized target, live parent identity, target-absent state, content SHA-256 and byte length.
- Raw file content is excluded from approval/audit metadata.
- Executor revalidates live session/workspace/parent/target state and consumes the matching short-lived single-use permit immediately before the first mutation.

## Filesystem law
- Authority is create-only/no-clobber. Existing-file overwrite/edit/append/truncate is forbidden.
- Targets are workspace-relative only. Absolute, traversal, backslash, drive/UNC/device-like and non-portable path forms fail closed.
- `.git` components are forbidden case-insensitively.
- Control, display-format/bidi, Windows-forbidden/reserved and ambiguous path forms fail closed.
- Existing traversed parents are opened/validated no-follow and must retain their approved identity.
- POSIX publication uses same-parent atomic no-clobber mechanics.
- Windows publication uses handle-relative NT no-clobber rename semantics with reparse-resistant traversal.
- A target appearing after approval or immediately before publication is preserved and the Hive operation fails closed.
- Payload is bounded to 1 MiB.

## Preserved boundaries
This decision does not approve existing-file replacement/edit, delete, rename-existing, Git mutation, generic filesystem APIs, shell/terminal/process execution, Tauri/desktop write commands, provider/model execution or credentials, Cua/computer-use mutation, remote control, automatic skill activation or billing/purchases. Permission & Control Plane remains the sole mutation authorization choke point.

## Corrections
The initial Windows publication primitive was rejected after hosted Windows exposed an incompatible root-relative `SetFileInformationByHandle` path. The same WO moved to native NT handle-relative no-clobber rename without weakening the security contract. Real NTFS junction/reparse and publication-race tests were added. Independent audit then closed `.git` and approval-confusing Unicode/control path gaps.

## Evidence
Technical head `12d86579335c8f553bf77457739a6f2a7d287f10` passed Governance #278 with Ubuntu **317 PASS** and Windows HIGH_ASSURANCE **89 PASS**, plus Desktop Shell #114. HEDS technical `5217411336` approved promotion with unresolved HIGH/CRITICAL `0`.

Promotion head `9f82d7211aa7ae304d4045623ab1c27911c12a14` passed Governance #281 and Desktop Shell #117. HEDS promotion `5217449846` approved this final documentation/state mutation with unresolved HIGH/CRITICAL `0`.

## Final-candidate result
DEC-025 is **APPROVED / FINAL CANDIDATE — NOT CANONICAL**. This state mutation introduces no runtime/product/workflow/dependency/capability change. Canonicalization still requires exact-head final Governance + Desktop Shell, final HEDS with unresolved HIGH/CRITICAL 0, squash product merge, post-merge exact-SHA validation and documentation-only canonical closeout.