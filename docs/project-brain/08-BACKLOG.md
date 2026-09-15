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
17. `HCODER-WO-0017` Runtime Observability Contract & Safe Status Export — **DONE / CANONICAL `HCODER-CP-0017`**. Product PR #42 squash-merged as `00bcb87251772cba0eb385d9628448374e9dd612`; canonical closeout `79e6eb60288c8e0adcb26bdcffdfe0ae21ef8db7`; final HEDS unresolved HIGH/CRITICAL 0.
18. `HCODER-WO-0018` Cross-Runtime Status IPC Contract — **DONE / CANONICAL `HCODER-CP-0018`**. Product PR #45 squash-merged as `9987b13f67f4c33b87acb2f03b87c6437e7a61ca`; post-merge Governance #244 and Desktop Shell #80 SUCCESS; final product HEDS `5215823771`, unresolved HIGH/CRITICAL 0.
19. `HCODER-WO-0019` Runtime Status Sidecar Helper — **STAGED NEXT / RECONSTRUCTION REQUIRED**. Historical PR #38 is supporting evidence only; rebuild on canonical CP-0018.
20. `HCODER-WO-0020` Desktop Runtime Status Supervisor & System Truth Surface — **HISTORICAL STACK EXISTS / BLOCKED BY CP-0019**. Corrected technical head exists; no canonical promotion yet.

## Product capability roadmap
- **Desktop Shell/UI:** governed native substrate plus canonical explicit user-mediated workspace opening and truthful bounded workspace/Git/evidence reads.
- **Runtime Observability:** strict bounded `RuntimeStatusSnapshot v1` is canonical through CP-0017 and the frozen one-shot `hive-runtime-status-ipc-v1` cross-runtime presentation protocol is canonical through CP-0018.
- **Model Capability Negotiator:** normalize provider/model capabilities and expose only verified capability state.
- **Hive Skills Engine:** discover, verify, install, version, activate, compose and learn reusable skills under the permission boundary.
- **Agent Runtime:** long-running task UX over the approved resumable runtime, checkpoints, plans, subagents and evidence.
- **Provider/Model Router:** OpenCode Go first-class plus replaceable providers, quality/cost/latency policy and per-task selection.
- **Git / Workspace / Shell:** read-only workspace/Git/evidence foundation is canonical through CP-0016; file mutation, Git mutation and terminal execution require later governed permit-aware capability adapters.
- **Computer surface:** live view and privileged control remain separate; mutation stays behind permit-gated Cua executors.
- **Remote Hive Control:** future HIGH_ASSURANCE authenticated/encrypted subsystem with revocation, audit and emergency stop; never expose raw RDP/VNC/Cua publicly.
- **Integrated Build Loop:** code -> test -> launch -> observe -> computer-use validate -> repair -> evidence -> PR/review.
- **Packaging/Updates:** signed Windows packaging, controlled acquisition, update channels, rollback and health diagnostics.

## Current NECESSARY product increment after canonical CP-0018
Reconstruct `HCODER-WO-0019 — Runtime Status Sidecar Helper` on canonical CP-0018. Historical PR #38 must not be merged directly.

The reconstruction must reconcile the historical helper against the canonical CP-0018 API:
- `serve_one()` consumes a **prebuilt `RuntimeStatusSnapshot`**, so the helper must construct `disconnected_snapshot()` before calling it rather than passing the function object;
- process tests must use the canonical `encode_request()` wire rather than ad hoc `json.dumps(...)` fixtures;
- the sidecar must accept exactly `--stdio-status-v1`, handle exactly one request, emit exactly one response, then exit;
- default status remains truthful DISCONNECTED;
- `ManagedStdioProcess` remains shell-free and its sanitized child environment must preserve secret non-observation;
- no desktop launcher, generic process dispatch, provider/model/network execution, credential lookup, task/permission mutation, filesystem/Git/terminal/computer-use mutation, remote control, billing/purchases or skill activation enters WO-0019.

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
- Rust dependency refresh/target-chain analysis for the 7 RustSec warning-class advisories.
- Stricter desktop CSP than `style-src 'unsafe-inline'`.
- Native picker/full desktop interaction E2E, Windows reparse fixture, visual screenshot/pixel validation and accessibility automation.
- Stronger handle-relative/no-follow workspace capability I/O before privileged file/Git mutation.
- Installer/signing/updater/release packaging and rollback/roll-forward proof.
- Runtime helper/process identity, containment and supervision through staged WO-0019..0020 sequence.
- Safe public permission/status observation only if later objectively needed; never serialize private authorization internals as a shortcut.
- Final project license and release attribution decision.

Only the next NECESSARY increment enters canonical promotion automatically; later historical stacked Work Orders remain blocked until their predecessor checkpoint is canonical.
