# Evidence Bundle — HCODER-WO-0021

**Work Order:** `HCODER-WO-0021 — Trusted Workspace File Capability & Permit-Gated Mutation Boundary`  
**Issue:** `#57`  
**PR:** `#58`  
**Canonical base:** `HCODER-CP-0020` / `c1f4166497d07eea6758e00f8a6d201e2b9acc02`  
**Technical exact head:** `12d86579335c8f553bf77457739a6f2a7d287f10`  
**Technical HEDS:** `5217411336` — APPROVED FOR PROMOTION CANDIDATE, H/C `0`

## Scope receipt
WO-0021 establishes the first Hive-owned privileged workspace file mutation boundary. The admitted authority is intentionally narrow: **atomic create-only / no-clobber** for a previously absent regular file inside the trusted workspace.

The technical implementation provides:
- `WorkspaceFileCapability` with fixed `FILESYSTEM_WRITE` / `write_file_v1` authority;
- portable strict workspace-relative path contract;
- workspace/root and parent live identity validation;
- target-absence and content SHA-256/length binding in the approved request;
- short-lived request-bound single-use permit consumption immediately before first OS mutation;
- bounded payload ceiling of 1 MiB;
- POSIX no-follow traversal and same-parent atomic hard-link publication;
- Windows handle-relative no-follow/reparse-resistant traversal and native `NtSetInformationFile(FileRenameInformation=10)` no-clobber publication;
- adversarial Ubuntu/Windows race, link/reparse, identity, permit and path-security tests.

No existing-file overwrite/edit/append/truncate, delete, rename-existing, generic shell/terminal, Git mutation, Tauri/desktop write, provider/model execution, Cua/computer-use mutation, remote control, skill activation or billing/purchase authority is introduced.

## Correction history
- Initial Windows publication using `SetFileInformationByHandle(FileRenameInfo)` with a non-null root handle failed on hosted Windows with WinError 87. The same WO was corrected to native NT handle-relative rename semantics. No weaker fallback was admitted.
- Real NTFS junction/reparse adversarial tests were added, including parent and target cases.
- Late publication race tests prove a concurrently created target is preserved and the Hive operation fails closed.
- Independent diff audit identified VCS-internal and approval-confusion path gaps. `.git` components are now rejected case-insensitively, together with control/display-format/bidi characters and non-portable Windows-forbidden forms.

## Technical exact-head receipt
Governance #278 (`35040798107`) on exact `12d86579335c8f553bf77457739a6f2a7d287f10`: **SUCCESS**.
- Ubuntu full suite: **317 PASS**, 3 skips.
- Windows Server 2025 HIGH_ASSURANCE: **89 PASS**, 2 skips.
- The new Windows junction/reparse and publication-race cases execute and pass; the skips are pre-existing platform/symlink fixture exclusions.

Desktop Shell #114 (`35040798164`) on the same exact head: **SUCCESS**.
- `desktop-web`: exact-head checkout, desktop security gate, npm graph, typecheck, component/contract tests, production web build and full npm audit all PASS.
- `desktop-windows`: exact-head checkout, locked RustSec audit, exact npm graph, Rust unit tests, locked Rust check, Tauri Windows build and desktop launch smoke all PASS.

HEDS technical `5217411336`: **APPROVED FOR PROMOTION CANDIDATE**, unresolved HIGH/CRITICAL `0`.

## HIGH_ASSURANCE authority proof
- `FILESYSTEM_WRITE` remains HIGH with mandatory trusted approval.
- Model/tool/task text cannot approve a challenge or mint a permit.
- Approval fingerprint binds exact workspace, normalized target, parent identity, target-absent state, content digest and content byte length. Raw content is absent from approval/audit metadata.
- Executor revalidates live session/workspace/parent/target state and consumes the matching permit immediately before mutation.
- Stale, consumed, wrong-session, wrong-workspace, wrong-parent, wrong-target and wrong-content requests/permits fail closed.
- Existing targets are rejected. A target appearing after approval or immediately before publication is preserved and causes failure.
- Traversed parent components are no-follow/reparse-resistant and identity checked.
- `.git` internals are outside this filesystem-write authority.
- Absolute, traversal, backslash, drive/UNC/device-like, NUL/control/format/bidi, Windows forbidden/reserved and other non-portable path forms fail closed.
- Temporary cleanup is best-effort and constrained to the capability-created temporary object; it does not delete an unverified final target.

## Explicit residuals
- Existing-file replacement/edit/append/truncate remains unimplemented and requires a separately governed compare-and-swap design.
- Git mutation remains unavailable.
- Desktop/Tauri does not expose this write capability.
- This WO does not add generic filesystem APIs, shell/process authority, provider/model credentials/execution, Cua mutation, remote control, billing/purchase or automatic skill activation.
- Existing desktop release-hardening and dependency warning-class residuals remain unchanged.

## Promotion state
Technical implementation is approved for a **documentation/evidence/state-only promotion candidate**. Any product/runtime/workflow/dependency/capability change after technical head `12d86579335c8f553bf77457739a6f2a7d287f10` requires returning to technical HEDS.

Canonical status still requires candidate Decision/Checkpoint Delta, exact-head Governance + Desktop Shell, promotion HEDS, final approval state mutation, final exact-head gates/HEDS, squash product merge, post-merge validation and documentation-only canonical closeout.