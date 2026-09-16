# HCODER-WO-0021 — Trusted Workspace File Capability & Permit-Gated Mutation Boundary

**Status:** COMPLETE / CANONICAL  
**Risk:** HIGH_ASSURANCE  
**Task class:** T3  
**Context radius:** C4  
**Canonical base:** `HCODER-CP-0020` / `c1f4166497d07eea6758e00f8a6d201e2b9acc02`  
**Canonical result:** `HCODER-CP-0021` / `200540c2605ff4e5c32f54cd1c3be40dbd167520`  
**Issue:** `#57` — CLOSED / COMPLETED  
**Product PR:** `#58` — SQUASH MERGED as `ee2e01e99aaea89deb2754ba8295fe34d7744541`  
**Closeout PR:** `#59` — SQUASH MERGED as `200540c2605ff4e5c32f54cd1c3be40dbd167520`  
**Decision:** `DEC-025` — APPROVED / CANONICAL

## OBJECTIVE
Establish the first Hive-owned privileged workspace file capability boundary. The admitted mutation slice is deliberately **atomic create-only / no-clobber**: root-bound, traversal-resistant, no-follow, live-identity revalidated and gated by the canonical Permission & Control Plane. Every `FILESYSTEM_WRITE` mutation consumes a short-lived request-bound single-use permit immediately before mutation.

## CANONICAL RESULT
The objective and acceptance criteria were proven and promoted without weakening the security contract. Hive Coder can create a previously absent regular file inside the trusted workspace through fixed action `write_file_v1`. Existing-file replacement/edit remains unapproved.

Canonical authority chain:
`Trusted host/orchestrator -> PermissionControlPlane -> request-bound single-use FILESYSTEM_WRITE permit -> WorkspaceFileCapability(create-only/no-clobber) -> OS handle/no-follow/no-clobber primitive -> new workspace file`.

## SEALED INVARIANTS
1. Capability is exactly `FILESYSTEM_WRITE`; action is fixed `write_file_v1`.
2. Workspace identity is canonical and executor-owned.
3. Target is a strictly normalized workspace-relative path; traversal, absolute/drive/UNC/device, `.git`, control/display-format and non-portable ambiguous forms fail closed.
4. Existing parent traversal is no-follow/reparse-resistant and identity-bound.
5. Approval fingerprints workspace, target, parent identity, target absence, content digest and byte length; raw content is excluded from approval/audit metadata.
6. Mandatory trusted approval remains required; model/tool/task/file content cannot mint permits.
7. Live session/workspace/parent/target state is revalidated immediately before permit consumption and mutation.
8. Stale/replayed/wrong-session/workspace/parent/target/content requests fail closed.
9. Publication is atomic no-clobber and preserves a concurrently appearing target.
10. Payload is bounded to 1 MiB.

## OUTSIDE CANONICAL AUTHORITY
Existing-file overwrite/edit/append/truncate, delete/rename-existing, generic shell/terminal execution, Git mutation, caller-selected outside-workspace paths, Tauri/desktop write commands, provider/model execution or credentials, additional Cua/computer-use mutation, remote control, billing/purchases, automatic skill activation and recursive destructive filesystem operations remain outside WO-0021/CP-0021.

## CORRECTION HISTORY
- Initial Windows root-relative publication primitive failed on hosted Windows and was replaced in the same WO by native NT handle-relative no-clobber rename semantics.
- Real NTFS junction/reparse and publication-race tests were added.
- Independent audit closed `.git` mutation and Unicode/control path-confusion gaps.
- No no-follow/TOCTOU/no-clobber guarantee was weakened.

## EVIDENCE
- Technical head `12d86579335c8f553bf77457739a6f2a7d287f10`: Governance #278 + Desktop Shell #114 SUCCESS; HEDS `5217411336`.
- Promotion head `9f82d7211aa7ae304d4045623ab1c27911c12a14`: Governance #281 + Desktop Shell #117 SUCCESS; HEDS `5217449846`.
- Final product head `347dc69ab97e48d75f72d16df3bb34347da09c69`: Governance #282 + Desktop Shell #118 SUCCESS; HEDS `5217471428`, APPROVED FOR SQUASH MERGE, HIGH/CRITICAL 0.
- Product merge `ee2e01e99aaea89deb2754ba8295fe34d7744541`: post-merge Governance #283 + Desktop Shell #119 SUCCESS.
- Closeout head `eec525cbf48439c5722cef624b25e8ff9203d9e0`: Governance #284 + Desktop Shell #120 SUCCESS; HEDS `5217531877`.
- Canonical closeout main `200540c2605ff4e5c32f54cd1c3be40dbd167520`: Governance #285 + Desktop Shell #121 SUCCESS.

## STOP CONDITION — SATISFIED
Exact-head required CI passed, HEDS unresolved HIGH/CRITICAL is 0, product and closeout merges were push-validated, and Issue #57 is closed. WO-0021 is COMPLETE / CANONICAL.