# HCODER-WO-0021 — Trusted Workspace File Capability & Permit-Gated Mutation Boundary

**Status:** APPROVED FOR EXECUTION  
**Risk:** HIGH_ASSURANCE  
**Task class:** T3  
**Context radius:** C4  
**Issue:** `#56`  
**Canonical base:** `HCODER-CP-0020` / `main c1f4166497d07eea6758e00f8a6d201e2b9acc02`

## OBJECTIVE
Create Hive Coder's first permit-gated filesystem mutation executor contract for an existing trusted workspace file, while refusing to claim an OS backend until root-bound/no-follow/TOCTOU-safe semantics are independently proven.

## CONTEXT
CP-0016 canonicalized bounded read-only workspace/Git/evidence observation and explicitly deferred privileged file/Git mutation until a stronger handle-relative/no-follow capability-I/O design exists. CP-0020 is fully sealed. The Permission & Control Plane already defines `FILESYSTEM_WRITE` as HIGH risk with mandatory approval. No governed filesystem mutation executor exists today.

## SCOPE
- Add a Hive-owned `GatedFileActionExecutor` in the Python runtime.
- First allowlisted action only: `file.replace_text` for an existing regular file.
- Define a strict `FileMutationPort` trusted-host protocol and immutable `FileObservation`/`FileMutationReceipt` records.
- Require backend guarantees: root-bound identity, no-follow identity proof, atomic replace, precondition enforcement and bounded evidence.
- Keep file content outside `ActionRequest`/ApprovalChallenge. Bind only canonical relative path, byte length, content SHA-256 and observed precondition identity/hash into the permit fingerprint.
- Consume the existing single-use execution permit immediately before live revalidation/mutation.
- Revalidate workspace identity, parent identity, target identity, target content SHA-256 and no-follow/root-bound guarantees after permit consumption.
- Support cancellation/emergency/takeover callback semantics and prohibit parallel mutation per control session.
- Add deterministic adversarial tests with a trusted in-memory test port.
- Add the file-executor suite to Windows HIGH_ASSURANCE governance.

## OUT OF SCOPE
Production filesystem backend; arbitrary absolute/outside-workspace path; file create/delete/rename; binary file writes; shell/terminal execution; Git mutation; desktop/Tauri write command; provider/model execution; credentials; computer-use mutation; remote control; automatic skill activation; billing/purchases.

## FILES / SOURCES TO READ
- `docs/project-brain/11-CHECKPOINT.md`
- `docs/project-brain/03-SCOPE.md`
- `docs/project-brain/04-ARCHITECTURE.md`
- `docs/project-brain/05-SECURITY.md`
- `docs/project-brain/09-DEFINITION-OF-DONE.md`
- `docs/project-brain/13-INTEGRATION-CONTRACTS.md`
- `docs/security/PERMISSION-CONTROL-PLANE.md`
- `hive_runtime/control_types.py`
- `hive_runtime/control_plane.py`
- `hive_runtime/cua_executor.py`
- `.github/workflows/governance.yml`

## REQUIREMENTS
1. Only `Capability.FILESYSTEM_WRITE` + action `file.replace_text` is admitted.
2. Relative path is canonical POSIX-style workspace-relative text: no absolute path, drive prefix, backslash, empty/dot/dot-dot component, NUL, colon, Windows reserved basename, trailing dot/space, or component over 120 chars; total <= 512 chars.
3. Replacement content is UTF-8 text, non-empty, NUL-free and <= 262,144 bytes.
4. Raw content never enters `ActionRequest.arguments`, ApprovalChallenge display arguments, audit payload or mutation receipt. Request binds only content SHA-256 + byte count.
5. Request also binds trusted preflight `workspace_identity`, `parent_identity`, `target_identity`, existing target SHA-256 and target byte count.
6. Executor validates request/contents before permit consumption, then consumes permit once, then performs live observation and exact precondition comparison immediately before backend mutation.
7. Live observation must prove `root_bound`, `no_follow`, `regular_file`, existing target and non-empty trusted identities.
8. Backend must declare `root_bound`, `no_follow` and `atomic_replace` guarantees. A backend lacking any guarantee is rejected before permit consumption.
9. Mutation receipt must contain no source/replacement content, must bind before/after SHA-256, bytes written, path and resulting target identity, and must prove atomic/root-bound/no-follow execution.
10. Cancellation, emergency stop or takeover blocks dispatch. Parallel mutation in one control session is denied.
11. Stale/wrong/replayed permit, wrong workspace, changed parent/target identity, changed content hash/size, path traversal, unsafe platform aliases or oversized content fail closed.
12. No production filesystem writes occur in this WO. Production OS backend selection requires a later HIGH_ASSURANCE increment with platform-specific no-follow/handle-relative proof.

## ARCHITECTURE RULES
`Trusted host preflight -> ActionRequest(FILESYSTEM_WRITE, metadata/digests only) -> PermissionControlPlane approval/permit -> GatedFileActionExecutor -> live FileObservation -> trusted FileMutationPort`.

The `FileMutationPort` is an explicit trusted-host capability boundary, not a generic Python filesystem adapter. It may not be supplied by model/tool text. The executor cannot approve requests or create permits.

## CONSTRAINTS
No `open()`, `Path.write_*`, `os.replace`, `shutil`, subprocess or direct production filesystem mutation inside the executor module. The deterministic test port may mutate only in-memory state.

## ACCEPTANCE CRITERIA
- full existing regression remains green;
- new executor tests cover success, content-digest binding, no content in request/receipt, path canonicalization, traversal/platform alias rejection, backend guarantee rejection, wrong capability/action, stale/replayed permit, workspace/parent/target swap, hash/size drift, cancellation/takeover/emergency stop, parallel mutation and malformed receipt;
- Windows HIGH_ASSURANCE executes the file-executor suite;
- no new desktop/Tauri capability or generic process surface;
- exact-head Governance + Desktop Shell green;
- HEDS unresolved HIGH/CRITICAL = 0.

## TESTS
Python unittest source-pack; Windows HIGH_ASSURANCE fixed suite; existing Desktop Shell regression; adversarial HEDS.

## DELIVERABLES
`hive_runtime/file_executor.py`, deterministic test suite, Windows HIGH_ASSURANCE inclusion, Evidence Bundle and governed checkpoint/decision only after technical proof.

## REVIEW FORMAT
HEDS_DELTA HIGH_ASSURANCE. Permit bypass, mutation before permit/live revalidation, content leakage, path escape, weak backend guarantee, unbound target/content or mutation after cancellation is HIGH/CRITICAL.

## STOP CONDITION
Technical exact-head Governance + Desktop Shell green and HEDS approved. Promotion must explicitly state that CP-0021 does not provide a production OS filesystem backend or desktop write surface. No shell/Git/computer-use mutation may enter this Work Order.