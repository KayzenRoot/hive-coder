# Test & Benchmark Plan — Hive Coder

Baseline by risk:
- LOW: targeted deterministic checks.
- STANDARD: unit + lint + typecheck/build + relevant integration.
- ELEVATED: STANDARD + broad regression, persistence/security/recovery where applicable.
- HIGH_ASSURANCE: ELEVATED + independent review, adversarial/permission tests, rollback proof and platform-specific validation.

Computer-use tests must cover permission denial, emergency stop, wrong-window protection where feasible, sensitive-data redaction and safe failure.

## Existing competence/evaluation policy
Agent competence is measured independently from model/provider reputation. A model name, benchmark marketing claim, system prompt or agent self-description cannot promote competence. Repository-aware evaluation, Provider Certification Lab, Semantic Repository Twin, Elite Specialist Forge and Autonomous Engineering Arena continue to use the approved CP-0011 through CP-0014 evidence, independence, freshness, anti-overfit and authority-separation rules. Hosted deterministic/mock provider evaluation remains contract evidence only and does not prove a real provider/model stack elite or `DISTINGUISHED`.

## Desktop shell validation policy — WO-0015 candidate
Desktop work is ELEVATED because UI/native bridging can become a privilege boundary even when the current slice is read-only.

Every WO-0015 promotion head must prove on the exact commit:
- committed npm and Cargo lockfiles;
- desktop static security gate PASS;
- exactly one approved frontend invoke command and one approved native Tauri command;
- capability scope restricted to the intended window with zero plugin permissions;
- no shell/filesystem/process plugins or direct process-command surface;
- no unsafe HTML sink admitted by the security gate;
- TypeScript typecheck PASS;
- deterministic frontend/contract/component tests PASS;
- production Vite build PASS;
- full npm dependency audit PASS;
- RustSec scan executed against the committed `Cargo.lock` with warnings recorded rather than hidden;
- Rust unit tests PASS with `--locked`;
- `cargo check --locked` PASS with warnings denied;
- Windows Tauri release build PASS;
- native launch smoke PASS;
- existing Governance regression PASS, including Linux source-pack and Windows HIGH_ASSURANCE suites;
- independent HEDS exact-head review with no unresolved HIGH/CRITICAL finding.

### Proven technical candidate receipts
Technical head `9e212c6f8c959f3d3cb19cc5146485f39bd6c8fd` established:
- Governance #187: **256/256 Ubuntu PASS** and **56/56 Windows HIGH_ASSURANCE PASS**.
- Desktop Shell #23: **8/8 Vitest PASS**, **3/3 Rust PASS**, TypeScript PASS, Vite build PASS, npm vulnerabilities `0`, RustSec command PASS, `cargo check --locked` PASS, Tauri release build PASS and `DESKTOP_LAUNCH_SMOKE=PASS`.
- HEDS technical review `5211566651`: APPROVED FOR PROMOTION CANDIDATE; HIGH/CRITICAL open findings `0`.

### Required adversarial/truthfulness coverage
- malformed/unsupported `DesktopSnapshot` schemas fail to disconnected/unknown presentation state;
- unbounded strings and invalid operational-state enums are rejected;
- no safety action may become available without an actionable trusted session;
- disconnected runtime/provider/Git/evidence/permission state must not render as READY;
- non-`main` window callers must be rejected by the native command;
- unavailable navigation/task execution remains disabled and must not be represented as ready;
- future privileged commands require a new Work Order and tests through the Permission & Control Plane, not extension of the WO-0015 read-only command.

## Explicit desktop evidence limits
- Launch smoke proves that the release executable remains alive for the bounded smoke window; it is not screenshot/pixel-fidelity validation or full interaction E2E.
- `bundle.active=false`; installer/signing/updater/package/release-channel and rollback/roll-forward evidence remain unproven.
- RustSec currently reports seven warning-class transitive advisories. Passing the audit command does not mean the graph is warning-free.
- Live provider/runtime/Git/evidence/permission adapters are not proven by WO-0015.
- Visual screenshot regression, accessibility automation and end-to-end task/computer-use flows require later increments.

Future benchmark or desktop-test upgrades must preserve exact-head evidence and must not report unmeasured quality/performance/security gains as facts.
