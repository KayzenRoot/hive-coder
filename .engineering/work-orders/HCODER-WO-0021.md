# HCODER-WO-0021 — Trusted Workspace File Capability & Permit-Gated Mutation Boundary

**Status:** IN PROGRESS  
**Risk:** HIGH_ASSURANCE  
**Task class:** T3  
**Context radius:** C4  
**Canonical base:** `HCODER-CP-0020` / `c1f4166497d07eea6758e00f8a6d201e2b9acc02`  
**Issue:** `#57`  
**Branch:** `feat/HCODER-WO-0021-workspace-file-capability`

## OBJECTIVE
Establish the first Hive-owned privileged workspace file capability boundary. The first mutation slice is deliberately **atomic create-only / no-clobber**: root-bound, traversal-resistant, no-follow, live-identity revalidated and gated by the canonical Permission & Control Plane. Every `FILESYSTEM_WRITE` mutation consumes a short-lived request-bound single-use permit immediately before mutation.

## CONTEXT
CP-0016 deliberately accepted path-based TOCTOU only for non-authoritative read presentation and required a separately governed stronger handle-relative/no-follow design before privileged file/Git mutation. CP-0020 is fully sealed and introduces no mutation authority.

Preflight rejected a generic overwrite primitive: neither portable POSIX rename nor ordinary Windows replace provides a cross-platform inode/file-ID compare-and-swap guarantee for an existing target. Rather than weaken the target-swap proof obligation, WO-0021 admits only creation of a previously absent file. Existing-file replacement/edit remains a later separately governed capability.

## SCOPE
- Hive runtime workspace-file capability contract.
- Trusted canonical workspace identity and bounded workspace-relative file targets.
- Traversal/absolute/drive/UNC escape rejection as platform applicable.
- No-follow directory/file identity and reparse/symlink/non-file rejection.
- Exact workspace/target/content metadata binding through `ActionRequest` fingerprinting.
- Existing `FILESYSTEM_WRITE` mandatory approval and permit flow, with permit consumption immediately before commit/mutation.
- Live session/workspace/parent/target revalidation before commit.
- Bounded payload and path component limits.
- Atomic create-only/no-clobber commit: target must be absent when requested and must still be absent at commit; a concurrently appearing target makes the operation fail closed.
- Cancellation, emergency stop and takeover blocking before commit.
- Adversarial Ubuntu and Windows HIGH_ASSURANCE tests.

## OUT OF SCOPE
Existing-file overwrite/edit/append/truncate; generic shell/terminal execution; Git mutation; caller-selected outside-workspace paths; symlink/reparse traversal; permit bypass; Tauri/desktop write commands; provider/model execution or credentials; Cua/computer-use mutation; remote control; billing/purchases; automatic skill activation; recursive delete/rename/chmod/chown.

## FILES / SOURCES TO READ
`AGENTS.md`; canonical Checkpoint, Decisions Ledger, Scope, Definition of Done, Architecture, Requirements, Security; `hive_runtime/control_types.py`; `hive_runtime/control_policy.py`; `hive_runtime/control_plane.py`; control-plane tests and Governance workflow.

## REQUIREMENTS
1. Privileged writes use only `Capability.FILESYSTEM_WRITE` and fixed Hive-owned action `write_file_v1`, whose WO-0021 semantics are create-only/no-clobber.
2. Workspace identity used by policy and executor must be canonical and must match the executor-owned workspace root.
3. Relative paths are normalized syntactically without resolving through links; empty, dot/dot-dot, absolute, drive-qualified, UNC/device and NUL-containing targets fail closed.
4. Every traversed existing path component is opened/validated no-follow and must be an ordinary directory where a directory is expected.
5. A write request fingerprints the exact workspace, normalized target, parent identity, target-absent state and bounded content digest/length. Raw content is not stored in audit metadata.
6. `FILESYSTEM_WRITE` remains HIGH with mandatory trusted approval. Model/tool text cannot approve a challenge or mint a permit.
7. Executor revalidates live session, workspace, parent identity and target absence, then consumes the matching permit immediately before the first mutation.
8. Stale, consumed, wrong-session, wrong-workspace, wrong-parent, wrong-target or wrong-content permits/requests fail closed.
9. The final publication step must be atomic and no-clobber. If another actor creates the target before publication, the operation fails and preserves that target. Temporary artifacts are removed best-effort without deleting an unverified object.
10. No shell, Git, desktop mutation, existing-file replacement or broader filesystem authority is introduced.

## ARCHITECTURE RULES
`Trusted host/orchestrator -> PermissionControlPlane -> WorkspaceFileCapability(create-only) -> OS handle/no-follow/no-clobber primitives -> new workspace file`.

The Permission & Control Plane remains the sole authorization choke point. The file adapter owns capability-I/O mechanics only and cannot mint approvals/permits or infer authority from task/model text.

## CONSTRAINTS
No shell strings; no external process; no PATH lookup; no ambient credential use; no following symlink/reparse components; no outside-root fallback; no caller-selected OS absolute destination; no hidden desktop/Tauri invoke; no generic filesystem API export; no overwrite fallback when atomic no-clobber is unavailable.

## ACCEPTANCE CRITERIA
- exact request/workspace/parent/target/content binding proven;
- traversal, absolute/drive/UNC/device, symlink/reparse, existing target, wrong workspace, wrong parent, stale/consumed/wrong permit and oversize payload fail closed;
- target-appears-after-approval adversarial test preserves the concurrently created target and fails closed;
- cancellation/emergency/takeover before commit prevents mutation;
- publication failure leaves no final target and best-effort cleans only the capability-created verified temporary object;
- Ubuntu complete suite green and Windows HIGH_ASSURANCE workspace-file suite green;
- no generic shell/Git/desktop mutation authority or existing-file overwrite path in diff;
- exact-head HEDS unresolved HIGH/CRITICAL = 0 before promotion.

## TESTS
`python -m compileall -q hive_runtime tools`; full `python -m unittest discover -s tests -p "test_*.py"`; focused workspace-file adversarial suite on Ubuntu and Windows; existing control-plane/executor/status suites; repository security/static gates; exact-head Governance and Desktop Shell where required by repository policy.

## DELIVERABLES
Work Order, Context Lock, implementation, adversarial tests, CI wiring if required, Evidence Bundle, proposed Decision/Checkpoint Delta, PR and exact-head HEDS receipts.

## REVIEW FORMAT
`HEDS_DELTA`, HIGH_ASSURANCE, exact-head. Any permit bypass, outside-root write, link/reparse follow, existing-file clobber, exploitable target-swap window, unbounded write, unsafe temporary cleanup, or shell/Git authority expansion is HIGH/CRITICAL.

## STOP CONDITION
Do not weaken no-follow/TOCTOU/no-clobber guarantees to make a platform pass. Do not introduce existing-file overwrite/edit, generic shell/terminal execution, Git mutation, caller-selected outside-workspace paths, desktop write authority, provider credentials, computer-use mutation, remote control, billing/purchases or skill activation under WO-0021. Promotion requires exact-head required CI, HEDS and unresolved HIGH/CRITICAL 0.