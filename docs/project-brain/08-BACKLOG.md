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
16. `HCODER-WO-0016` Trusted Workspace & Git Read Surface — **DONE / CANONICAL `HCODER-CP-0016`**.
17. `HCODER-WO-0017` Runtime Observability Contract & Safe Status Export — **DONE / CANONICAL `HCODER-CP-0017`**.
18. `HCODER-WO-0018` Cross-Runtime Status IPC Contract — **DONE / CANONICAL `HCODER-CP-0018`**. Canonical closeout SHA `c0a44d43546b9f176125b9e7099b8422d6b62ba3`; push Governance #246 and Desktop Shell #82 SUCCESS.
19. `HCODER-WO-0019` Runtime Status Sidecar Helper — **DONE / CANONICAL `HCODER-CP-0019` SUBJECT TO CLOSEOUT SEAL**. Product PR #48 squash-merged as GitHub-signed `2ed4222556916cf524e31f65c4c417d27b7e6fd9`; final HEDS `5216313496`, H/C 0; post-merge Governance #253 and Desktop Shell #89 SUCCESS. Historical PR #38 remains non-authoritative evidence only.
20. `HCODER-WO-0020` Desktop Runtime Status Supervisor & System Truth Surface — **STAGED NEXT / RECONSTRUCTION REQUIRED AFTER CP-0019 CLOSEOUT SEAL**. Historical stacked work is supporting evidence only and must not be merged directly.

## Product capability roadmap
- **Desktop Shell/UI:** governed native substrate plus canonical explicit user-mediated workspace opening and truthful bounded workspace/Git/evidence reads.
- **Runtime Observability:** `RuntimeStatusSnapshot v1` is canonical through CP-0017; frozen `hive-runtime-status-ipc-v1` through CP-0018; fixed one-shot sidecar helper through CP-0019 once this closeout seal completes.
- **Model Capability Negotiator:** normalize provider/model capabilities and expose only verified capability state.
- **Hive Skills Engine:** discover, verify, install, version, activate, compose and learn reusable skills under the permission boundary.
- **Agent Runtime:** long-running task UX over the approved resumable runtime, checkpoints, plans, subagents and evidence.
- **Provider/Model Router:** OpenCode Go first-class plus replaceable providers, quality/cost/latency policy and per-task selection.
- **Git / Workspace / Shell:** read-only workspace/Git/evidence foundation is canonical through CP-0016; file mutation, Git mutation and terminal execution require later governed permit-aware capability adapters.
- **Computer surface:** live view and privileged control remain separate; mutation stays behind permit-gated Cua executors.
- **Remote Hive Control:** future HIGH_ASSURANCE authenticated/encrypted subsystem with revocation, audit and emergency stop; never expose raw RDP/VNC/Cua publicly.
- **Integrated Build Loop:** code -> test -> launch -> observe -> computer-use validate -> repair -> evidence -> PR/review.
- **Packaging/Updates:** signed Windows packaging, controlled acquisition, update channels, rollback and health diagnostics.

## Current NECESSARY product increment after the CP-0019 closeout seal
Freshly reconstruct `HCODER-WO-0020 — Desktop Runtime Status Supervisor & System Truth Surface` from canonical CP-0019. Historical stacked WO-0020 artifacts are evidence only and may be mined for intent/tests, never merged or cherry-picked as canonical ancestry.

WO-0020 must preserve these laws from CP-0017..0019:
- runtime status is presentation state, never authorization;
- wire remains `hive-runtime-status-ipc-v1` with sole `status.snapshot` operation unless a separately governed protocol change explicitly proves otherwise;
- sidecar launch target is fixed Hive-owned identity, not caller/model-selected process input;
- no generic process/shell capability is introduced as a shortcut;
- helper/supervisor lifecycle must fail closed on identity, startup, malformed status, timeout, crash, shutdown and stale-process ambiguity;
- provider catalog observation remains distinct from VERIFIED capability evidence;
- private Permission & Control Plane state is not serialized as presentation telemetry;
- `UI -> Application/Orchestrator -> Permission & Control Plane -> Capability Adapters` remains the mutation authority path;
- mutation controls remain disabled until a later permit-gated path exists.

## Open residual work
- Desktop/Tauri runtime status supervisor/launcher, fixed helper identity/authenticity, containment and lifecycle policy through WO-0020.
- Rust dependency refresh/target-chain analysis for the 7 RustSec warning-class advisories.
- Stricter desktop CSP than `style-src 'unsafe-inline'`.
- Native picker/full desktop interaction E2E, Windows reparse fixture, visual screenshot/pixel validation and accessibility automation.
- Stronger handle-relative/no-follow workspace capability I/O before privileged file/Git mutation.
- Installer/signing/updater/release packaging and rollback/roll-forward proof.
- Safe public permission/status observation only if later objectively needed; never serialize private authorization internals as a shortcut.
- Final project license and release attribution decision.

Only the next NECESSARY increment enters canonical promotion automatically; later historical stacked Work Orders remain blocked until their predecessor checkpoint is canonical.
