# HCODER-CP-0022 — Canonical Closeout

**Status:** CLOSEOUT CANDIDATE — EXACT-HEAD GATES / HEDS REQUIRED BEFORE MERGE  
**Work Order:** `HCODER-WO-0022`  
**Decision candidate:** `DEC-026`  
**Canonical predecessor:** `HCODER-CP-0021`  
**Product merge SHA:** `06c68611a42e07b85ae765145d94bb613110ac14`  
**Product PR:** `#62`  
**Correction PR:** `#64`  
**Issue:** `#61`

## Canonical candidate boundary
HCODER-CP-0022 closes the first Hive-owned governed capability for replacing the bytes of one already-existing regular file inside the trusted workspace.

The capability is `FILESYSTEM_WRITE` action `replace_file_v1`. Approval binds the canonical workspace, normalized target, parent identity, exact observed old target identity, old content SHA-256/length, new content SHA-256/length and contract version. Raw old/new content is not approval/audit metadata.

The implementation uses verified capability-owned staging, late live revalidation, request-bound short-lived single-use permit consumption at the mutation-ready boundary, and platform-proven atomic namespace replacement. It preserves the previously canonical `write_file_v1` create-only/no-clobber boundary.

## Security contract
This checkpoint explicitly canonicalizes **bounded-race atomic replacement**, not strict expected-target or expected-inode CAS.

An uncooperative external process may alter the destination pathname after Hive's final successful observable revalidation and before the native atomic publication call where the platform interface has no expected-target predicate. This residual interval is explicit and must not be renamed or represented as strict CAS.

All observable stale state before publication fails closed. Unsupported platform/filesystem combinations must expose capability unavailability and fail closed. `.git`, traversal, non-regular targets, symlink/reparse traversal, outside-workspace mutation, permit bypass and authority expansion remain forbidden.

## Objective promotion evidence
### Correction exact-head
- CR-001 final exact head: `12e38e98bb690e29494bab5e7a1c597a64b49765`.
- Governance #322: SUCCESS.
- Desktop Shell #158: SUCCESS.
- Governance jobs: source-pack SUCCESS; native Windows HIGH_ASSURANCE SUCCESS; native macOS replacement proof SUCCESS.
- HEDS CR-001 review: `5222036573`; unresolved HIGH/CRITICAL: `0/0`.
- Correction squash merge into product branch: `35745aa56e203fa819751aee4b70cce57a9600e7`.

### Product exact-head
- Product exact head: `35745aa56e203fa819751aee4b70cce57a9600e7`.
- Governance #323: SUCCESS.
- Desktop Shell #159: SUCCESS.
- HEDS final product review: `5222076357`; unresolved HIGH/CRITICAL: `0/0`.
- Product PR #62 squash merged to main as `06c68611a42e07b85ae765145d94bb613110ac14`.

### Post-merge main validation
- Main exact SHA: `06c68611a42e07b85ae765145d94bb613110ac14`.
- Push Governance #324: SUCCESS.
- Push Desktop Shell #160: SUCCESS.

## Platform evidence
- Linux/POSIX: governed contract/security tests and adversarial staging ownership/revalidation tests pass under the source-pack lane.
- Windows: native HIGH_ASSURANCE replacement contract and control-plane tests pass, including native `FileRenameInformationEx` publication through `NtSetInformationFile` class 65 and preservation of the sealed create-only receipt state.
- macOS/Darwin: dedicated native macOS replacement lane passes independently from Linux evidence.

Platform support remains evidence-based. HCODER-PLATFORM-001 / Issue #63 owns the broader first-class platform architecture matrix and future packaging/runtime validation.

## Preserved exclusions
This checkpoint does not authorize append, truncate-in-place, delete, arbitrary rename/move, recursive mutation, chmod/chown, Git mutation, generic shell/terminal execution, desktop/Tauri write authority, outside-workspace mutation, provider/model credential expansion, Cua/computer-use mutation expansion, remote control, billing/purchases or automatic skill activation.

## Closeout promotion gates
Before this closeout may merge:
1. exact-head Governance on the closeout branch must be SUCCESS;
2. exact-head Desktop Shell must be SUCCESS;
3. HEDS closeout review must report unresolved HIGH/CRITICAL `0/0`;
4. closeout changes must remain documentation/state promotion only and must not broaden runtime authority.

After closeout merge and post-merge validation, `HCODER-WO-0022` may be marked COMPLETE, Issue #61 may close, and DEC-026 may be promoted to CANONICAL with this checkpoint as its promotion evidence.

## STOP CONDITION
Do not mark HCODER-CP-0022 canonical before the closeout exact-head gates, HEDS closeout approval, closeout merge and post-merge validation succeed. Never rewrite the bounded-race contract as strict CAS.