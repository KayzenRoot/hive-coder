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
16. `HCODER-WO-0016` Trusted Workspace & Git Read Surface — **DONE / CANONICAL `HCODER-CP-0016`**. Product PR #35 squash-merged as `6483ed36393b02f45e286590e75bc9fb36d48727`; post-merge Governance #215 and Desktop Shell #51 SUCCESS.
17. `HCODER-WO-0017` Runtime Observability Contract & Safe Status Export — **STAGED NEXT**. Historical stacked implementation/evidence exists but must be reconciled onto canonical CP-0016 and revalidated before promotion.
18. `HCODER-WO-0018` Cross-Runtime Status IPC Contract — **STACKED / BLOCKED BY CP-0017**.
19. `HCODER-WO-0019` Runtime Status Sidecar Helper — **STACKED / BLOCKED BY CP-0018**.
20. `HCODER-WO-0020` Desktop Runtime Status Supervisor & System Truth Surface — **STACKED / BLOCKED BY CP-0019**. Technical corrected head exists; no canonical promotion yet.

## Product capability roadmap
- **Desktop Shell/UI:** governed native substrate plus canonical explicit user-mediated workspace opening and truthful bounded workspace/Git/evidence reads.
- **Model Capability Negotiator:** normalize provider/model capabilities and expose only verified capability state.
- **Hive Skills Engine:** discover, verify, install, version, activate, compose and learn reusable skills under the permission boundary.
- **Agent Runtime:** long-running task UX over the approved resumable runtime, checkpoints, plans, subagents and evidence.
- **Provider/Model Router:** OpenCode Go first-class plus replaceable providers, quality/cost/latency policy and per-task selection.
- **Git / Workspace / Shell:** read-only workspace/Git/evidence foundation is canonical through CP-0016; file mutation, Git mutation and terminal execution require later governed permit-aware capability adapters.
- **Computer surface:** live view and privileged control remain separate; mutation stays behind permit-gated Cua executors.
- **Remote Hive Control:** future HIGH_ASSURANCE authenticated/encrypted subsystem with revocation, audit and emergency stop; never expose raw RDP/VNC/Cua publicly.
- **Integrated Build Loop:** code -> test -> launch -> observe -> computer-use validate -> repair -> evidence -> PR/review.
- **Packaging/Updates:** signed Windows packaging, controlled acquisition, update channels, rollback and health diagnostics.

## Next NECESSARY product increment after canonical CP-0016
Reconcile and promote `HCODER-WO-0017`, preserving truthful live **runtime/provider/task/permission presentation state** through existing Hive-owned engines without enabling their corresponding mutation surfaces. Existing staged implementation must be rebased/reconstructed on canonical CP-0016 rather than treating pre-squash ancestry as authoritative.

Any next increment must preserve:
- presentation state as non-authoritative;
- explicit provenance and UNKNOWN/DISCONNECTED/DEGRADED instead of fake readiness;
- `UI -> Application/Orchestrator -> Permission & Control Plane -> Capability Adapters`;
- no generic shell execution or arbitrary filesystem/desktop mutation;
- disabled mutation controls until a later governed permit-gated path exists.

## Open residual work
- Rust dependency refresh/target-chain analysis for the 7 RustSec warning-class advisories.
- Stricter desktop CSP than `style-src 'unsafe-inline'`.
- Native picker/full desktop interaction E2E, Windows reparse fixture, visual screenshot/pixel validation and accessibility automation.
- Stronger handle-relative/no-follow workspace capability I/O before privileged file/Git mutation.
- Installer/signing/updater/release packaging and rollback/roll-forward proof.
- Live runtime/provider/permission adapter integration through staged WO-0017..0020 sequence.
- Final project license and release attribution decision.

Only the next NECESSARY increment enters canonical promotion automatically; later stacked Work Orders remain blocked until their predecessor checkpoint is canonical.
