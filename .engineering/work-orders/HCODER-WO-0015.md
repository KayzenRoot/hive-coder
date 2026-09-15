# HCODER-WO-0015 — Desktop Shell Foundation & Safe Workspace Read Model

**Status:** APPROVED FOR EXECUTION  
**Issue:** #31  
**Risk:** ELEVATED  
**Task class:** T3  
**Context radius:** C4

## OBJECTIVE
Deliver Hive Coder's first real desktop product vertical slice: a Windows-buildable premium desktop shell with an original Hive visual system and a bounded read-only application bridge that presents truthful project/runtime/provider/Git/evidence/permission state without creating any new privileged execution path.

## CONTEXT
HCODER-CP-0014 proves substantial governed runtime, planning, certification and specialist-selection foundations, but canonical Scope/Requirements/Architecture/UI-UX still require a native desktop experience. Post-CP-0014 source-check found no existing frontend/desktop toolchain or Desktop UI layer. Initial product progress now requires a thin end-to-end shell before additional lab-only expansion.

Current ecosystem preflight direction, to be exact-pinned in lockfiles after compatibility validation: Node 24 LTS, Tauri 2, React 19.3, TypeScript, Vite 8 supported line. Upstream/version names grant no Hive authority.

## SCOPE
- Add a version-locked frontend/desktop toolchain under a dedicated Hive desktop app boundary.
- Establish Tauri 2 + React + TypeScript + Vite project structure after preflight compatibility checks.
- Create original Hive design tokens and reusable shell primitives; no Apple proprietary assets, trademarks, SF Symbols or copied application chrome.
- Implement first canonical surfaces: workspace/project rail, task/conversation center, system/status inspector, Git/evidence summary, provider/runtime state and a permanently visible safety control region.
- Add a typed, allowlisted, read-only Tauri command boundary for `DesktopSnapshot`/health information. No generic command execution and no arbitrary path/command parameters.
- Model UNKNOWN, DISCONNECTED, DEGRADED and READY states explicitly. The UI must never fabricate runtime/provider/Git readiness.
- Safety controls (Pause, Emergency Stop, Take Control) render current capability/session truth and remain disabled when no authorized actionable session exists. No mutation wiring in this increment.
- Add deterministic frontend tests, schema/contract tests, typecheck, production frontend build and Windows desktop build/smoke proof where hosted CI supports it.
- Update only canonical documentation actually affected by the proven implementation, including stale Backlog status reconciliation during promotion.

## OUT OF SCOPE
- Privileged computer-use mutation from UI.
- Terminal/shell execution, arbitrary filesystem writes or browser automation.
- Provider credentials or paid-provider execution.
- Live desktop/screen streaming.
- Remote control.
- Automatic skill activation.
- Autonomous billing/purchases.
- Installer/signing/release packaging.
- Full IDE/editor implementation.
- Final visual-polish pass or complete product navigation.
- TelemetrySeal/MasteryVault implementation.

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
- existing `hive_runtime/` public/runtime status surfaces and tests.

## REQUIREMENTS
1. A reproducible Windows-buildable desktop shell exists under an explicit Hive-owned desktop boundary.
2. UI invokes only named typed commands. No generic shell/command bridge exists.
3. Initial application bridge is read-only and cannot create CP-0005 permits, activate skills, execute arbitrary commands, mutate files, control desktop input or obtain provider credentials.
4. `DesktopSnapshot` has a versioned schema with bounded strings/collections and explicit state enums.
5. Every displayed operational status has provenance and explicit UNKNOWN/DISCONNECTED behavior.
6. Safety controls are visible but capability/session-aware; unavailable mutation actions are disabled rather than simulated.
7. Original Hive design tokens/components satisfy the canonical premium desktop direction without copying Apple proprietary assets.
8. Frontend does not treat repository/provider/tool text as executable instruction authority.
9. Desktop dependency capabilities remain replaceable behind Hive-facing contracts.
10. No regression or weakening of CP-0005 through CP-0014 authority/security boundaries.

## ARCHITECTURE RULES
- Preserve target layering: `Hive Desktop UI -> Hive Application/Orchestrator -> Permission & Control Plane -> Capability Adapters -> Runtime/Providers/Computer Use -> OS/Apps`.
- This increment may implement only the UI and a read-only application boundary. It must not skip directly from React/Tauri UI to privileged OS/runtime mutation.
- Tauri commands are an allowlist, not an RPC escape hatch.
- Read-model objects are presentation state and cannot grant authority.
- Unknown/tampered/malformed desktop snapshots fail closed to an error/disconnected presentation.
- New framework choice is replaceable and documented as an adapter/shell decision, not a new authority root.

## CONSTRAINTS
- Prefer current stable/LTS toolchain. Resolve exact versions into lockfiles; do not use floating `latest` in committed reproducibility-critical metadata.
- Keep dependencies minimal and auditable.
- No secrets or provider keys in frontend, Tauri config, tests, screenshots or CI.
- No arbitrary child-process invocation from desktop code in this increment.
- Keep first UI vertical slice intentionally narrow; no silent expansion into full IDE functionality.
- Existing Python runtime APIs remain backward compatible.

## ACCEPTANCE CRITERIA
- Desktop source tree, exact dependency lock and Tauri configuration exist and pass dependency/preflight validation.
- Windows desktop app builds successfully in CI or an equivalent exact-head Windows build gate.
- Production frontend build and TypeScript typecheck pass.
- Deterministic component/contract tests cover READY/UNKNOWN/DISCONNECTED/DEGRADED states, malformed snapshot rejection and disabled unavailable safety actions.
- Static/security checks prove no generic shell invoke, unrestricted filesystem bridge, wildcard Tauri capability or provider secret is introduced.
- The shell renders workspace navigation, task center, status inspector, Git/evidence summary and safety controls using original Hive tokens/components.
- The read-only bridge returns a bounded versioned `DesktopSnapshot` and exposes no mutation command.
- Existing Python/Linux and Windows HIGH_ASSURANCE governance regressions remain green.
- HEDS finds no unresolved HIGH/CRITICAL issue.

## TESTS
- frontend unit/component tests;
- TypeScript typecheck;
- production Vite build;
- Tauri/Rust compile/check;
- Windows Tauri build or explicit deterministic smoke/build gate;
- static grep/contract tests against generic shell invocation, wildcard capabilities and secrets;
- existing `python -m unittest discover -s tests -p "test_*.py"`;
- existing Windows HIGH_ASSURANCE governance suite;
- exact-head Governance;
- visual evidence/snapshot checks only when deterministic and non-secret.

## DELIVERABLES
- desktop/frontend project and lockfiles;
- original Hive design-token/component foundation;
- first desktop shell surfaces;
- versioned read-only desktop application contract;
- targeted CI/build checks;
- tests and Evidence Bundle;
- canonical Architecture/Security/Test/UI-UX/Integration/Backlog updates only where proven;
- DEC-019 if architecture/toolchain is approved;
- proposed HCODER-CP-0015 and Checkpoint Delta;
- PR with HEDS review.

## REVIEW FORMAT
HEDS_DELTA exact-head. Treat architecture-boundary bypass, generic command execution, wildcard privileges, secret exposure or fake-ready operational state as HIGH/CRITICAL. UNKNOWN is not PASS.

## STOP CONDITION
Exact-head Governance plus desktop/frontend CI green; HEDS APPROVED; no unresolved HIGH/CRITICAL; DEC-019/HCODER-CP-0015 approved if warranted; squash merge; post-merge Governance green; continuation handoff updated.