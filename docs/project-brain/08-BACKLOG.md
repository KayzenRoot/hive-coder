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
18. `HCODER-WO-0018` Cross-Runtime Status IPC Contract — **DONE / CANONICAL `HCODER-CP-0018`**. Product PR #45 and canonical closeout PR #46 are squash-merged; canonical closeout SHA `c0a44d43546b9f176125b9e7099b8422d6b62ba3`; push Governance #246 and Desktop Shell #82 SUCCESS.
19. `HCODER-WO-0019` Runtime Status Sidecar Helper — **TECHNICALLY APPROVED / PROMOTION CANDIDATE, NOT CANONICAL**. PR #48; technical head `ba10ba72f76316806cd820dc0d205e68105f61bb`; Governance #250 **288/288 Ubuntu + 61/61 Windows HIGH_ASSURANCE PASS**; Desktop Shell #86 SUCCESS; HEDS `5216093993`, H/C 0. Historical PR #38 remains non-authoritative evidence only.
20. `HCODER-WO-0020` Desktop Runtime Status Supervisor & System Truth Surface — **HISTORICAL STACK EXISTS / BLOCKED BY CANONICAL CP-0019**. No direct promotion/merge until WO-0019 is canonical and WO-0020 is freshly reconstructed against it.

## Product capability roadmap
- **Desktop Shell/UI:** governed native substrate plus canonical explicit user-mediated workspace opening and truthful bounded workspace/Git/evidence reads.
- **Runtime Observability:** strict bounded `RuntimeStatusSnapshot v1` is canonical through CP-0017; frozen one-shot `hive-runtime-status-ipc-v1` is canonical through CP-0018; the fixed one-shot sidecar helper is technically approved as the CP-0019 promotion candidate.
- **Model Capability Negotiator:** normalize provider/model capabilities and expose only verified capability state.
- **Hive Skills Engine:** discover, verify, install, version, activate, compose and learn reusable skills under the permission boundary.
- **Agent Runtime:** long-running task UX over the approved resumable runtime, checkpoints, plans, subagents and evidence.
- **Provider/Model Router:** OpenCode Go first-class plus replaceable providers, quality/cost/latency policy and per-task selection.
- **Git / Workspace / Shell:** read-only workspace/Git/evidence foundation is canonical through CP-0016; file mutation, Git mutation and terminal execution require later governed permit-aware capability adapters.
- **Computer surface:** live view and privileged control remain separate; mutation stays behind permit-gated Cua executors.
- **Remote Hive Control:** future HIGH_ASSURANCE authenticated/encrypted subsystem with revocation, audit and emergency stop; never expose raw RDP/VNC/Cua publicly.
- **Integrated Build Loop:** code -> test -> launch -> observe -> computer-use validate -> repair -> evidence -> PR/review.
- **Packaging/Updates:** signed Windows packaging, controlled acquisition, update channels, rollback and health diagnostics.

## Current NECESSARY product increment
Finish governed promotion/canonicalization of `HCODER-WO-0019 — Runtime Status Sidecar Helper` in PR #48. The technical slice is approved; CP-0019 is not canonical until promotion/final exact-head gates, HEDS, squash merge and post-merge validation pass.

The candidate preserves these fixed laws:
- exact mode `--stdio-status-v1` only;
- prebuilt truthful `disconnected_snapshot()` passed to canonical CP-0018 `serve_one()`;
- one canonical request -> one canonical response -> exit;
- usage/protocol failures use stable exit `64` / `65` without fake snapshots or payload-derived stderr;
- canonical `encode_request()` / `parse_response()` wire in acceptance tests;
- duplicate/noncanonical/future/unsupported/oversized/missing-newline process input fails closed;
- `ManagedStdioProcess` remains `shell=False` with least-privilege allowlisted child environment;
- ambient provider credential material is neither inherited nor emitted;
- Ubuntu source-pack and Windows HIGH_ASSURANCE both exercise the sidecar process boundary;
- no desktop launcher, generic process dispatch, provider/model/network execution, credential authority, task/permission mutation, filesystem/Git/terminal/computer-use mutation, remote control, billing/purchases or automatic skill activation enters WO-0019.

Any next increment must preserve:
- presentation state as non-authoritative;
- canonical provenance and UNKNOWN/DISCONNECTED/DEGRADED instead of fake readiness;
- provider catalog observation distinct from VERIFIED capability evidence;
- no private Permission & Control Plane state serialization when no safe public observer exists;
- `UI -> Application/Orchestrator -> Permission & Control Plane -> Capability Adapters`;
- no generic shell execution or arbitrary filesystem/desktop mutation;
- no silent expansion of `hive-runtime-status-ipc-v1` beyond `status.snapshot`;
- disabled mutation controls until a later governed permit-gated path exists.

## Open residual work
- Desktop/Tauri runtime status supervisor/launcher, helper identity/authenticity, containment and lifecycle policy after canonical CP-0019.
- Rust dependency refresh/target-chain analysis for the 7 RustSec warning-class advisories.
- Stricter desktop CSP than `style-src 'unsafe-inline'`.
- Native picker/full desktop interaction E2E, Windows reparse fixture, visual screenshot/pixel validation and accessibility automation.
- Stronger handle-relative/no-follow workspace capability I/O before privileged file/Git mutation.
- Installer/signing/updater/release packaging and rollback/roll-forward proof.
- Safe public permission/status observation only if later objectively needed; never serialize private authorization internals as a shortcut.
- Final project license and release attribution decision.

Only the next NECESSARY increment enters canonical promotion automatically; later historical stacked Work Orders remain blocked until their predecessor checkpoint is canonical.
