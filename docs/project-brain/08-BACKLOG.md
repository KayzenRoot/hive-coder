# Backlog — Hive Coder

## Foundation sequence
1. `HCODER-WO-0001` governance/source-pack bootstrap — DONE.
2. `HCODER-WO-0002` Open Interpreter + Cua provenance/foundation lock — DONE.
3. `HCODER-WO-0003` Hive runtime bridge — DONE.
4. `HCODER-WO-0004` Permission & Control Plane — DONE.
5. `HCODER-WO-0005` permit-gated Cua mutation boundary — DONE.
6. `HCODER-WO-0006` opt-in real Cua Windows integration harness — DONE.
7. `HCODER-WO-0007` evidence-driven model capabilities + governed skills — DONE.
8. `HCODER-WO-0008` provider/model runtime + ACP prompt boundary — DONE.
9. `HCODER-WO-0009` resumable agent task runtime — DONE.
10. `HCODER-WO-0010` Master Planner + evidence-gated orchestration — DONE.
11. `HCODER-WO-0011` measured expert-agent mesh + context intelligence — DONE.
12. `HCODER-WO-0012` repository intelligence + continuous recertification — DONE.
13. `HCODER-WO-0013` Provider Certification Lab + Semantic Repository Twin — DONE.
14. `HCODER-WO-0014` Elite Specialist Forge + Autonomous Engineering Arena — DONE.
15. `HCODER-WO-0015` Desktop Shell Foundation & Safe Workspace Read Model — DONE. Canonical `HCODER-CP-0015`.
16. `HCODER-WO-0016` Trusted Workspace & Git Read Surface — DONE / CANONICAL `HCODER-CP-0016`.
17. `HCODER-WO-0017` Runtime Observability Contract & Safe Status Export — DONE / CANONICAL `HCODER-CP-0017`.
18. `HCODER-WO-0018` Cross-Runtime Status IPC Contract — DONE / CANONICAL `HCODER-CP-0018`.
19. `HCODER-WO-0019` Runtime Status Sidecar Helper — DONE / CANONICAL `HCODER-CP-0019`. Canonical closeout `main` SHA `e4bc74d1ae6c4054cd98cd34b16e6357f911224c`; push Governance #255 and Desktop Shell #91 SUCCESS.
20. `HCODER-WO-0020` Desktop Runtime Status Supervisor & System Truth Surface — **PROMOTION CANDIDATE / CP-0020 NOT CANONICAL**. Technical head `86c6e956985e0b51e0f56b3568a3fe9db61fef90` passed Governance #263, Desktop #99 and HEDS `5216871217`; CR-001/CR-002 resolved. Product merge is not yet authorized by this backlog entry.

## Product capability roadmap
- **Desktop Shell/UI:** governed native substrate, explicit trusted workspace opening, truthful bounded workspace/Git/evidence reads, and candidate read-only runtime System Truth through the fixed supervisor boundary.
- **Runtime Observability:** canonical `RuntimeStatusSnapshot v1` through CP-0017, canonical `hive-runtime-status-ipc-v1` through CP-0018, canonical fixed one-shot sidecar through CP-0019, and CP-0020 candidate fixed desktop supervisor + System Truth consumption.
- **Model Capability Negotiator:** normalize provider/model capabilities and expose only verified capability state.
- **Hive Skills Engine:** discover, verify, install, version, activate, compose and learn reusable skills under the permission boundary.
- **Agent Runtime:** long-running task UX over the approved resumable runtime, checkpoints, plans, subagents and evidence.
- **Provider/Model Router:** OpenCode Go first-class plus replaceable providers, quality/cost/latency policy and per-task selection.
- **Git / Workspace / Shell:** read-only workspace/Git/evidence foundation is canonical through CP-0016; file mutation, Git mutation and terminal execution require later governed permit-aware capability adapters.
- **Computer surface:** live view and privileged control remain separate; mutation stays behind permit-gated Cua executors.
- **Remote Hive Control:** future HIGH_ASSURANCE authenticated/encrypted subsystem with revocation, audit and emergency stop; never expose raw RDP/VNC/Cua publicly.
- **Integrated Build Loop:** code -> test -> launch -> observe -> computer-use validate -> repair -> evidence -> PR/review.
- **Packaging/Updates:** signed Windows packaging, controlled acquisition, update channels, rollback and health diagnostics.

## Current governed product increment
Finish `HCODER-WO-0020 — Desktop Runtime Status Supervisor & System Truth Surface` through promotion/final gates, squash product merge, exact-SHA post-merge validation and documentation-only canonical closeout. Do not select a new product Work Order before CP-0020 is fully canonical and a fresh source-check is performed.

WO-0020 laws:
- runtime status is presentation state, never authorization;
- wire remains canonical `hive-runtime-status-ipc-v1` with sole `status.snapshot` operation;
- exactly one fixed Hive-owned supervisor process site is admitted; generic process/shell remains forbidden;
- executable identity is fixed sibling-of-current-executable and rejects link/reparse identity;
- no frontend/model/task process path/args/env authority;
- child environment is cleared and output is byte-bounded with hard timeout;
- raw response admission is only through `decodeRuntimeStatusEnvelope(raw)`;
- no fake readiness or fabricated null counters;
- mutation controls remain disabled and the Permission & Control Plane remains the authority choke point.

## Open residual work
- Package/sign/attest the runtime-status sidecar and prove packaged live sidecar E2E; WO-0020 does not claim this.
- Define future restart/health/process-containment policy only if objectively needed; no generic daemon supervisor is approved.
- Rust dependency refresh/target-chain analysis for the 7 RustSec warning-class advisories.
- Stricter desktop CSP than `style-src 'unsafe-inline'`.
- Native picker/full desktop interaction E2E, Windows reparse fixture, visual screenshot/pixel validation and accessibility automation.
- Stronger handle-relative/no-follow workspace capability I/O before privileged file/Git mutation.
- Installer/signing/updater/release packaging and rollback/roll-forward proof.
- Safe public permission/status observation only if later objectively needed; never serialize private authorization internals as a shortcut.
- Final project license and release attribution decision.

Only the next NECESSARY increment enters canonical promotion automatically. Historical stacked branches remain evidence only unless freshly reconstructed from the current canonical checkpoint.