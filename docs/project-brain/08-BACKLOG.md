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
15. `HCODER-WO-0015` Desktop Shell Foundation & Safe Workspace Read Model — DONE. Canonical checkpoint `HCODER-CP-0015`; PR `#32` squash-merged; post-merge Governance #191 and Desktop Shell #27 green on canonical `main`.

## Product capability roadmap
- **Desktop Shell/UI:** first governed read-only substrate completed in WO-0015. Next layers must connect live runtime/provider/Git/evidence/permission state through typed Hive-owned adapters before enabling corresponding mutation surfaces.
- **Model Capability Negotiator:** normalize provider/model capabilities and expose only verified capability state.
- **Hive Skills Engine:** discover, verify, install, version, activate, compose and learn reusable skills under the existing permission boundary.
- **Skill Learning Loop:** candidate skill creation only after sanitization, deterministic replay/evaluation and governed promotion.
- **Agent Runtime:** long-running task UX over the already-approved resumable runtime, including checkpoints, plans, subagents and evidence surfaces.
- **Provider/Model Router:** OpenCode Go first-class plus replaceable providers, quality/cost/latency policy and per-task model selection.
- **Git / Workspace / Shell surfaces:** integrate read models first; any mutation or command execution requires a later governed bridge through the Permission & Control Plane.
- **Computer surface:** live view and privileged control remain separate capabilities; mutation must stay behind permit-gated Cua executors.
- **Remote Hive Control:** future HIGH_ASSURANCE subsystem using authenticated encrypted device/session semantics, revocation, audit and emergency stop. Never expose raw RDP/VNC/Cua directly.
- **Integrated Build Loop:** code -> test -> launch -> observe -> computer-use validate -> repair -> evidence -> PR/review.
- **Packaging/Updates:** signed Windows packaging, controlled acquisition, update channels, rollback and health diagnostics.

## Next NECESSARY product increment after CP-0015
Connect truthful live **read-only** desktop state to existing Hive-owned runtime/provider/task engines and introduce bounded workspace/Git/evidence/permission read adapters where concrete implementations are still absent.

The next increment must:
- keep desktop presentation state non-authoritative;
- expose explicit provenance and UNKNOWN/DISCONNECTED/DEGRADED rather than fake readiness;
- preserve `UI -> Application/Orchestrator -> Permission & Control Plane -> Capability Adapters`;
- avoid generic shell execution, arbitrary filesystem mutation or desktop-input mutation;
- keep all unavailable mutation controls disabled until a later governed permit-gated path exists.

## Open residual work after CP-0015
- Rust dependency refresh/target-chain analysis for the 7 RustSec warning-class advisories.
- Stricter desktop CSP than `style-src 'unsafe-inline'`.
- Native visual screenshot/pixel validation and full desktop interaction E2E.
- Installer/signing/updater/release packaging and rollback/roll-forward proof.
- Live runtime/provider/Git/evidence/permission adapter integration.
- Final project license and release attribution decision.

Only the next NECESSARY increment enters automatically after source-check and a new governed Work Order/Context Lock are created. HIGH_ASSURANCE capabilities retain their dedicated safety gates.
