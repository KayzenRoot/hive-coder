# HCODER-WO-0016 — Trusted Workspace & Git Read Surface

**Status:** APPROVED FOR SQUASH MERGE — NOT YET CANONICAL  
**Issue:** #34  
**Risk:** ELEVATED  
**Task class:** T3  
**Context radius:** C4

## OBJECTIVE
Turn the CP-0015 static Workspace shell into Hive Coder's first truthful live project surface: explicit user-mediated workspace selection plus bounded read-only workspace, Git and Hive evidence observations, while preserving all existing permission/control-plane boundaries and introducing no terminal execution, filesystem mutation, generic process execution or desktop-input authority.

## CONTEXT
`HCODER-CP-0015` is canonical on `main` after product PR #32 and documentation closeout PR #33. Canonical `main` SHA `330be799eedc3ea2478034039236d4a965f55274` passed push Governance #193 and Desktop Shell #29 including native Tauri build and launch smoke.

Post-CP-0015 source-check finds:
- the Python runtime already owns Interpreter, provider/model, task-runtime, Permission & Control Plane, Cua and evidence/governance engines;
- the desktop still truthfully reports runtime DISCONNECTED and provider/Git/evidence/permission UNKNOWN;
- no concrete `GitAdapter` or `ShellFileAdapter` exists;
- current Workspace UI is static and has no trusted project-opening path;
- current desktop security gate forbids generic shell/process/fs plugins and direct process execution.

The next product value is therefore a narrow live read slice, not another laboratory subsystem and not privileged execution.

## SCOPE
- Add a named Hive application command that opens a native user-mediated folder-selection experience. The frontend/model must not supply an arbitrary filesystem target to this command.
- Canonicalize and validate the selected workspace root in trusted Rust code before retaining it.
- Store workspace authority in application-owned state using an opaque workspace identity/handle; subsequent frontend calls reference only that handle or current trusted selection, never a caller-supplied raw privileged path.
- Add bounded read-only workspace metadata: display name, canonical root display value, project markers and bounded first-level/project-summary metadata sufficient for the Workspace surface.
- Add non-shell Git observation for the selected workspace: repository presence, branch or detached-HEAD state, HEAD identity and bounded repository metadata. Additional working-tree status may be included only if a vetted library implementation is deterministic and does not require generic process execution.
- Add bounded Hive evidence/checkpoint discovery under the selected root, limited to known canonical Hive paths and strict size/count ceilings.
- Evolve `DesktopSnapshot` to a new version only as necessary to carry typed workspace/Git/evidence state with provenance and explicit READY/UNKNOWN/DISCONNECTED/DEGRADED semantics.
- Update Workspace and System Truth UI so only backed read surfaces become active. No mutation/composer/Run authority is added.
- Extend the desktop security gate to reject filesystem writes, delete/rename/create paths, generic process execution, shell invocation, unbounded traversal, symlink/root escape patterns and caller-controlled privileged path authority.
- Add deterministic frontend/Rust/security tests plus Windows build/launch proof and existing Governance regressions.

## OUT OF SCOPE
- Terminal or shell execution.
- Generic child-process execution or spawning the Python runtime from desktop.
- Arbitrary filesystem writes, edits, create/delete/move/rename operations.
- Computer-use or desktop-input mutation.
- Provider credentials, paid-provider calls or model execution.
- Remote control.
- Automatic skill activation.
- Autonomous billing/purchases.
- Installer/signing/updater/release packaging.
- Full editor/IDE implementation.
- Broad recursive repository-content indexing or semantic indexing.
- Runtime/provider/permission live-process bridge beyond truthful unchanged UNKNOWN/DISCONNECTED state.

## FILES / SOURCES TO READ
- `docs/project-brain/11-CHECKPOINT.md`
- `docs/project-brain/10-DECISIONS-LEDGER.md`
- `docs/project-brain/03-SCOPE.md`
- `docs/project-brain/09-DEFINITION-OF-DONE.md`
- `docs/project-brain/04-ARCHITECTURE.md`
- `docs/project-brain/02-REQUIREMENTS.md`
- `docs/project-brain/05-SECURITY.md`
- `docs/project-brain/06-TEST-BENCHMARK-PLAN.md`
- `docs/project-brain/08-BACKLOG.md`
- `docs/project-brain/12-UI-UX.md`
- `docs/project-brain/13-INTEGRATION-CONTRACTS.md`
- `apps/desktop/src-tauri/src/lib.rs`
- `apps/desktop/src/contracts/desktopSnapshot.ts`
- `apps/desktop/src/components/ShellView.tsx`
- `tools/desktop/security_gate.py`
- relevant existing repository-intelligence bounded-read patterns for root containment/symlink handling.

## REQUIREMENTS
1. Workspace selection is explicit user intent mediated by the native application, not an arbitrary path parameter accepted from model/task/UI text.
2. Selected roots are canonicalized, directory-validated and retained only after trusted application-layer checks.
3. Subsequent read requests cannot redirect the application to a different raw filesystem target by changing frontend payload text.
4. All workspace reads are root-contained, bounded by count/size/depth/time-like deterministic ceilings where applicable, and read-only.
5. Symlinks, reparse-like escapes or noncanonical path transitions cannot silently expand the trusted root.
6. Git observation does not shell out to `git`, does not invoke package hooks, does not execute repository content and does not mutate repository state.
7. Git READY means concrete repository facts were observed; absence or read failure maps to explicit truthful state rather than fabricated readiness.
8. Evidence/checkpoint discovery reads only known Hive-owned paths and bounded text; repository text remains untrusted data.
9. `DesktopSnapshot` schema remains strict, versioned and bounded; malformed/oversized native data fails closed in the frontend parser.
10. Existing runtime/provider/permission states remain UNKNOWN/DISCONNECTED unless this Work Order actually establishes a trusted live observation for them.
11. No new path can mint CP permits, approvals, skill activation, credentials, desktop control, billing authority or trusted evidence.
12. CP-0005 through CP-0015 security/authority boundaries remain unchanged.

## ARCHITECTURE RULES
- Preserve `Hive Desktop UI -> Hive Application/Orchestrator -> Permission & Control Plane -> Capability Adapters -> Runtime/Providers/Computer Use -> OS/Apps`.
- Read-only workspace/Git/evidence adapters belong to the Hive application/capability-adapter layer; frontend components consume typed presentation contracts only.
- Native folder selection is a user-consent acquisition step, not a general filesystem capability.
- Raw filesystem paths are not authorization tokens. An opaque application-owned workspace identity represents the current trusted selection.
- Tauri commands remain a narrow allowlist. No generic RPC/action name, command string, executable path or shell-string parameter is allowed.
- Git/file libraries may parse data but cannot become authority roots or execute hooks/repository code.
- Unknown/tampered/malformed workspace state fails closed.

## CONSTRAINTS
- Keep dependencies minimal, exact-pinned through Cargo.lock/npm lock and security-audited.
- Prefer a pure library/structured-data Git implementation over invoking external `git`.
- Native folder-selection dependency must not add broad shell/process/filesystem mutation permissions.
- Do not add Tauri shell/process/fs plugins.
- Do not weaken the existing CSP or global Tauri JS restrictions.
- Do not expose secret-file contents, environment credentials or arbitrary repository file contents in the snapshot.
- No background watcher in this increment unless it is bounded, read-only, shutdown-safe and independently justified; explicit refresh is acceptable and preferred initially.
- Existing Python runtime APIs remain backward compatible and need not change.

## ACCEPTANCE CRITERIA
- User can explicitly choose a workspace in a Windows desktop build through a native application-mediated flow.
- Unsafe/non-directory/canonicalization-failing selections are rejected without changing current trusted workspace state.
- A selected workspace yields a bounded typed identity and metadata snapshot.
- Git state truthfully reports repository presence plus branch/detached state and HEAD identity without shell/process execution.
- Hive checkpoint/evidence presence is detected only under bounded known paths.
- Desktop UI renders selected workspace identity plus Git/evidence truth with provenance; fake READY states are absent.
- No filesystem mutation API, generic process/shell bridge, wildcard Tauri permission or caller-controlled arbitrary read path is introduced.
- Security/adversarial tests cover traversal, symlink/root escape, oversized/bounded reads, invalid opaque handles/state, non-repository roots and malformed snapshot data.
- TypeScript typecheck, frontend tests, production Vite build, Rust tests/check, dependency audits, Tauri Windows release build and launch smoke pass.
- Existing Governance Ubuntu and Windows HIGH_ASSURANCE suites remain green.
- HEDS reports no unresolved HIGH/CRITICAL issue.

## TESTS
- frontend schema/component tests for no-workspace, READY, DEGRADED and malformed workspace/Git/evidence states;
- Rust unit tests for root canonicalization, workspace state identity, bounded traversal/read rules, Git no-repo/branch/detached cases and evidence discovery;
- security-gate tests/static checks for write APIs, shell/process invocation, Tauri plugin expansion and caller-controlled path authority;
- dependency audit for any new Rust crate graph;
- TypeScript typecheck;
- Vite production build;
- `cargo test --locked` and `cargo check --locked`;
- Tauri Windows release build and launch smoke;
- existing `python -m unittest discover -s tests -p "test_*.py"`;
- existing Windows HIGH_ASSURANCE governance suite;
- exact-head Governance + Desktop Shell workflows.

## DELIVERABLES
- trusted workspace application state/read adapter;
- native workspace selection flow;
- non-shell Git read adapter;
- bounded Hive evidence/checkpoint read adapter;
- evolved typed DesktopSnapshot contract and UI integration;
- hardened desktop security gate;
- exact dependency locks and tests;
- Evidence Bundle and correction deltas if needed;
- canonical docs/Decision/Checkpoint updates only after implementation is objectively proven;
- PR with exact-head HEDS review.

## REVIEW FORMAT
HEDS_DELTA exact-head. Treat arbitrary path authority, root escape, filesystem mutation, generic process/shell execution, repository-code execution, fake Git/evidence READY state, secret exposure or permission-plane bypass as HIGH/CRITICAL. UNKNOWN is not PASS.

## STOP CONDITION
Exact-head Governance + Desktop Shell green; workspace/Git/evidence read security tests and dependency audits green; HEDS APPROVED with no unresolved HIGH/CRITICAL; canonical docs truthful; squash merge; post-merge Governance + Desktop Shell green; Issue #30 refreshed. No terminal/filesystem mutation/runtime-spawn/provider credential/computer-control authority may be promoted under this Work Order.
