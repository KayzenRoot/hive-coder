# Backlog — Hive Coder

## Foundation sequence
1. `HCODER-WO-0001` governance/source-pack bootstrap — DONE.
2. `HCODER-WO-0002` Open Interpreter + Cua provenance/foundation lock — DONE.
3. `HCODER-WO-0003` Hive runtime bridge — DONE.
4. `HCODER-WO-0004` Permission & Control Plane — DONE.
5. `HCODER-WO-0005` permit-gated Cua mutation boundary — DONE.
6. `HCODER-WO-0006` opt-in real Cua Windows integration harness — IN PROGRESS.

## Product capability roadmap
- **Model Capability Negotiator:** every LLM/provider exposes a normalized capability manifest (reasoning, vision, tool calling, structured output, context, coding, computer use, streaming, multimodal input/output). Hive routes tasks and enables UI/runtime features from proven capabilities rather than assuming all models are equal.
- **Hive Skills Engine:** discover, verify, install, version, activate, compose and learn reusable skills. Support project/user/global scopes, manifests, dependencies, provenance, signatures/digests, sandboxing, evaluation, rollback and explicit permission requirements. Cua MCP skills/resources are one source, not the owner of Hive skills.
- **Skill Learning Loop:** successful workflows can become candidate skills only after sanitization, deterministic replay/evaluation and user/governance promotion. Models cannot silently self-grant permissions through learned content.
- **Agent Runtime:** long-running tasks, checkpoints, resumability, subagents, task graphs, memory/context retrieval, schedules and autonomous repair loops.
- **Provider/Model Router:** OpenCode Go first-class plus replaceable providers, cost/latency/quality policies, fallback and per-task model selection.
- **Remote Hive Control:** secure control of the home Hive Coder from another authorized computer. Use an outbound-established, mutually authenticated encrypted session, device enrollment, short-lived credentials, least privilege, approval relay, audit trail, revocation, emergency stop and optional view-only mode. Never expose a raw RDP/VNC/Cua port directly to the internet.
- **Remote Workspace Streaming:** task/chat/status/evidence first; desktop pixels/control only as a separately permissioned capability.
- **Desktop Shell/UI:** premium Hive workspace with agent/chat, computer pane, tasks, Git, model status, approvals, skills, remote sessions and audit timeline.
- **Integrated Build Loop:** code -> test -> launch -> observe -> computer-use validate -> repair -> evidence -> PR/review.
- **Packaging/Updates:** signed Windows packaging, controlled foundation acquisition, update channels, rollback and health diagnostics.

Only the next NECESSARY increment enters automatically after current approval/checkpoint promotion. HIGH_ASSURANCE capabilities retain their dedicated safety gates.