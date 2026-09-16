# HCODER-WO-0021 — Technical Evidence Bundle

**Risk:** `HIGH_ASSURANCE`  
**Canonical base:** `HCODER-CP-0020` / `c1f4166497d07eea6758e00f8a6d201e2b9acc02`  
**Product PR:** `#58`  
**Reviewed technical head:** `12d86579335c8f553bf77457739a6f2a7d287f10`  
**HEDS technical review:** `5217396566` — **APPROVED FOR PROMOTION DELTA**  
**Unresolved HIGH:** `0`  
**Unresolved CRITICAL:** `0`

## Authority proven
WO-0021 introduces only the first Hive-owned privileged workspace-file mutation slice: atomic create-only/no-clobber through canonical `Capability.FILESYSTEM_WRITE` and fixed action `write_file_v1`. It does not introduce existing-file overwrite/edit/append/truncate, Git mutation, shell/terminal authority, desktop/Tauri write authority, provider/model execution, computer-use mutation, remote control, purchases/billing or automatic skill activation.

## Request and permit binding
The approved request binds the canonical workspace, normalized relative target, live parent identity, target state `absent`, content SHA-256 and bounded content length. Raw file content is not approval/audit metadata. The capability revalidates live state and consumes the matching short-lived single-use permit immediately before first OS mutation.

## Filesystem safety
- Portable path policy rejects absolute/drive/UNC/device/traversal/backslash forms, empty components, NUL/control/display-format/bidi characters, Windows-forbidden characters, trailing dot/space, reserved Windows device names and `.git` components.
- Existing directory traversal is no-follow/reparse-resistant and identity checked.
- Workspace and parent identity are revalidated before publication.
- POSIX publication uses same-parent hard-link atomic no-clobber publication.
- Windows publication uses native `NtSetInformationFile(FileRenameInformation=10)` with a pinned parent handle and replace disabled.
- A concurrently appearing target causes fail-closed behavior and is preserved.
- Capability-created temporary artifacts are cleaned best-effort without deleting an unverified target.

## Exact-head CI evidence
On exact technical head `12d86579335c8f553bf77457739a6f2a7d287f10`:
- Governance #278 / run `35040798107`: **SUCCESS**.
- Ubuntu complete suite: **317 tests**, `OK (skipped=3)`.
- Windows HIGH_ASSURANCE suite: **89 tests**, `OK (skipped=2)` on Windows Server 2025.
- Windows coverage includes real NTFS junction/reparse rejection and real late native-publication race preservation.
- Desktop Shell #114 / run `35040798164`: **SUCCESS**.

## Correction history
The same Work Order remained open through corrections. An earlier Windows publication implementation failed Governance with WinError 87 and was replaced rather than weakening the security contract. Subsequent adversarial audit added native Windows junction/reparse coverage, late publication race coverage, `.git` exclusion and portable Unicode/control/path hardening. All corrections passed the exact-head gates above.

## HEDS result
Technical HEDS review `5217396566` found unresolved HIGH/CRITICAL = `0` and approved only the next promotion-delta step. This evidence does not itself make CP-0021 canonical. Promotion documentation must produce a new exact head, pass the required exact-head gates again and receive final HEDS approval before squash merge.