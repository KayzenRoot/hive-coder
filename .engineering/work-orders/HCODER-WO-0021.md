# HCODER-WO-0021 — Trusted Workspace File Capability & Permit-Gated Mutation Boundary

**Status:** IN PROGRESS  
**Risk:** HIGH_ASSURANCE  
**Task class:** T3  
**Context radius:** C4  
**Canonical base:** `HCODER-CP-0020` / `c1f4166497d07eea6758e00f8a6d201e2b9acc02`  
**Issue:** `#57`  
**Branch:** `feat/HCODER-WO-0021-workspace-file-capability`

## OBJECTIVE
Establish the first Hive-owned privileged workspace file capability boundary. The first mutation slice must be root-bound, traversal-resistant, no-follow, live-identity revalidated and gated by the canonical Permission & Control Plane. Every `FILESYSTEM_WRITE` mutation consumes a short-lived request-bound single-use permit immediately before mutation.

## CONTEXT
CP-0016 deliberately accepted path-based TOCTOU only for non-authoritative read presentation and required a separately governed stronger handle-relative/no-follow design before privileged file/Git mutation. CP-0020 is fully sealed and introduces no mutation authority.

## SCOPE
- Hive runtime workspace-file capability contract.
- Trusted canonical workspace identity and bounded workspace-relative file targets.
- Traversal/absolute/drive/UNC escape rejection as platform applicable.
- No-follow directory/file identity and reparse/symlink/non-file rejection.
- Exact workspace/target/content metadata binding through `ActionRequest` fingerprinting.
- Existing `FILESYSTEM_WRITE` mandatory approval and permit flow, with permit consumption immediately before commit/mutation.
- Live session/workspace/parent/target revalidation before commit.
- Bounded payload and path component limits.
- Atomic or rollback-aware file commit only when the platform primitive can preserve the security contract; otherwise fail closed.
- Cancellation, emergency stop and takeover blocking before commit.
- Adversarial Ubuntu and Windows HIGH_ASSURANCE tests.

## OUT OF SCOPE
Generic shell/terminal execution; Git mutation; caller-selected outside-workspace paths; symlink/reparse traversal; permit bypass; Tauri/desktop write commands; provider/model execution or credentials; Cua/computer-use mutation; remote control; billing/purchases; automatic skill activation; recursive delete/rename/chmod/chown.

## FILES / SOURCES TO READ
`AGENTS.md`; canonical Checkpoint, Decisions Ledger, Scope, Definition of Done, Architecture, Requirements, Security; `hive_runtime/control_types.py`; `hive_runtime/control_policy.py`; `hive_runtime/control_plane.py`; control-plane tests and Governance workflow.

## REQUIREMENTS
1. Privileged writes use only `Capability.FILESYSTEM_WRITE` and a fixed Hive-owned action contract.
2. Workspace identity used by policy and executor must be canonical and must match the executor-owned workspace root.
3. Relative paths are normalized syntactically without resolving through links; empty, dot/dot-dot, absolute, drive-qualified, UNC/device and NUL-containing targets fail closed.
4. Every traversed existing path component is opened/validated no-follow and must be an ordinary directory where a directory is expected.
5. A write request fingerprints the exact workspace, normalized target and bounded content digest/length. Raw content is not stored in audit metadata.
6. `FILESYSTEM_WRITE` remains HIGH with mandatory trusted approval. Model/tool text cannot approve a challenge or mint a permit.
7. Executor revalidates live session and workspace/file identity, then consumes the matching permit immediately before the commit boundary.
8. Stale, consumed, wrong-session, wrong-workspace, wrong-target or wrong-content permits fail closed.
9. Failure before commit leaves the previous target unchanged; temporary artifacts are removed best-effort. Platform primitives that cannot uphold the boundary are not silently downgraded.
10. No shell, Git, desktop mutation or broader filesystem authority is introduced.

## ARCHITECTURE RULES
`Trusted host/orchestrator -> PermissionControlPlane -> WorkspaceFileCapability -> OS handle/no-follow primitives -> workspace file`.

The Permission & Control Plane remains the sole authorization choke point. The file adapter owns capability-I/O mechanics only and cannot mint approvals/permits or infer authority from task/model text.

## CONSTRAINTS
No shell strings; no external process; no PATH lookup; no ambient credential use; no following symlink/reparse components; no outside-root fallback; no caller-selected OS absolute destination; no hidden desktop/Tauri invoke; no generic filesystem API export.

## ACCEPTANCE CRITERIA
- exact request/workspace/target/content binding proven;
- traversal, absolute/drive/UNC/device, symlink/reparse, wrong workspace, stale/consumed/wrong permit and oversize payload fail closed;
- target/workspace swap adversarial tests fail closed or the OS primitive proves the swap cannot succeed while capability handles are held;
- cancellation/emergency/takeover before commit prevents mutation;
- rollback/failure-injection tests preserve prior target/no unexpected new target;
- Ubuntu complete suite green and Windows HIGH_ASSURANCE workspace-file suite green;
- no generic shell/Git/desktop mutation authority in diff;
- exact-head HEDS unresolved HIGH/CRITICAL = 0 before promotion.

## TESTS
`python -m compileall -q hive_runtime tools`; full `python -m unittest discover -s tests -p "test_*.py"`; focused workspace-file adversarial suite on Ubuntu and Windows; existing control-plane/executor/status suites; repository security/static gates; exact-head Governance and Desktop Shell where required by repository policy.

## DELIVERABLES
Work Order, Context Lock, implementation, adversarial tests, CI wiring if required, Evidence Bundle, proposed Decision/Checkpoint Delta, PR and exact-head HEDS receipts.

## REVIEW FORMAT
`HEDS_DELTA`, HIGH_ASSURANCE, exact-head. Any permit bypass, outside-root write, link/reparse follow, exploitable target-swap window, unbounded write, destructive failure behavior, or shell/Git authority expansion is HIGH/CRITICAL.

## STOP CONDITION
Do not weaken no-follow/TOCTOU guarantees to make a platform pass. Do not introduce generic shell/terminal execution, Git mutation, caller-selected outside-workspace paths, desktop write authority, provider credentials, computer-use mutation, remote control, billing/purchases or skill activation under WO-0021. Promotion requires exact-head required CI, HEDS and unresolved HIGH/CRITICAL 0.