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
16. `HCODER-WO-0016` Trusted Workspace & Git Read Surface — **DONE / CANONICAL `HCODER-CP-0016`**. Canonical closeout SHA `442733aeae6bd2f615dc0bc4c76dda024455c212`; push Governance #218 and Desktop Shell #54 SUCCESS.
17. `HCODER-WO-0017` Runtime Observability Contract & Safe Status Export — **PROMOTION CANDIDATE / CP-0017 NOT YET CANONICAL**. Technical head `63abc6349421ed4c83c52c5f03d305cbb0f1f3ef` passed Governance #225, Desktop Shell #61 and HEDS technical review `5215028501`; CR-001 MEDIUM resolved.
18. `HCODER-WO-0018` Cross-Runtime Status IPC Contract — **HISTORICAL STACK EXISTS / BLOCKED UNTIL CP-0017 CANONICAL**. Must be reconstructed against the strict canonical RuntimeStatusSnapshot v1 contract rather than merging the old divergent branch.
19. `HCODER-WO-0019` Runtime Status Sidecar Helper — **HISTORICAL STACK EXISTS / BLOCKED BY CP-0018**.
20. `HCODER-WO-0020` Desktop Runtime Status Supervisor & System Truth Surface — **HISTORICAL STACK EXISTS / BLOCKED BY CP-0019**. Corrected technical head exists; no canonical promotion yet.

## Product capability roadmap
- **Desktop Shell/UI:** governed native substrate plus canonical explicit user-mediated workspace opening and truthful bounded workspace/Git/evidence reads.
- **Runtime Observability:** strict bounded `RuntimeStatusSnapshot v1` is a CP-0017 promotion candidate. Presentation state is non-authoritative and uses canonical provenance plus fail-closed UNKNOWN/DISCONNECTED/DEGRADED semantics.
- **Model Capability Negotiator:** normalize provider/model capabilities and expose only verified capability state.
- **Hive Skills Engine:** discover, verify, install, version, activate, compose and learn reusable skills under the permission boundary.
- **Agent Runtime:** long-running task UX over the approved resumable runtime, checkpoints, plans, subagents and evidence.
- **Provider/Model Router:** OpenCode Go first-class plus replaceable providers, quality/cost/latency policy and per-task selection.
- **Git / Workspace / Shell:** read-only workspace/Git/evidence foundation is canonical through CP-0016; file mutation, Git mutation and terminal execution require later governed permit-aware capability adapters.
- **Computer surface:** live view and privileged control remain separate; mutation stays behind permit-gated Cua executors.
- **Remote Hive Control:** future HIGH_ASSURANCE authenticated/encrypted subsystem with revocation, audit and emergency stop; never expose raw RDP/VNC/Cua publicly.
- **Integrated Build Loop:** code -> test -> launch -> observe -> computer-use validate -> repair -> evidence -> PR/review.
- **Packaging/Updates:** signed Windows packaging, controlled acquisition, update channels, rollback and health diagnostics.

## Next NECESSARY product increment
First finish canonical promotion of `HCODER-WO-0017`. After CP-0017 is canonical, reconstruct `HCODER-WO-0018 — Cross-Runtime Status IPC Contract` on the new canonical main. The IPC layer must consume the corrected strict schema/provenance rules and must not treat status as authorization.

Any next increment must preserve:
- presentation state as non-authoritative;
- canonical provenance and UNKNOWN/DISCONNECTED/DEGRADED instead of fake readiness;
- provider catalog observation distinct from VERIFIED capability evidence;
- no private Permission & Control Plane state serialization when no safe public observer exists;
- `UI -> Application/Orchestrator -> Permission & Control Plane -> Capability Adapters`;
- no generic shell execution or arbitrary filesystem/desktop mutation;
- disabled mutation controls until a later governed permit-gated path exists.

## Open residual work
- Rust dependency refresh/target-chain analysis for the 7 RustSec warning-class advisories.
- Stricter desktop CSP than `style-src 'unsafe-inline'`.
- Native picker/full desktop interaction E2E, Windows reparse fixture, visual screenshot/pixel validation and accessibility automation.
- Stronger handle-relative/no-follow workspace capability I/O before privileged file/Git mutation.
- Installer/signing/updater/release packaging and rollback/roll-forward proof.
- Live runtime transport/supervision integration through staged WO-0018..0020 sequence.
- Safe public permission/status observation only if later objectively needed; never serialize private authorization internals as a shortcut.
- Final project license and release attribution decision.

Only the next NECESSARY increment enters canonical promotion automatically; later historical stacked Work Orders remain blocked until their predecessor checkpoint is canonical.