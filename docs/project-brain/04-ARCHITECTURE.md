# Architecture — Hive Coder

Target layered architecture:

`Hive Desktop UI -> Hive Application/Orchestrator -> Permission & Control Plane -> Capability Adapters -> Runtime/Providers/Computer Use -> OS/Apps`.

Initial capability adapters: `InterpreterAdapter`, `ComputerUseAdapter(Cua)`, `ProviderAdapter(OpenCode Go + others)`, `GitAdapter`, `Shell/FileAdapter`, `BrowserAdapter`, and governance/evidence integration.

Rules:
- Hive-facing contracts own subsystem boundaries.
- External foundations stay behind adapters to permit replacement/upgrades.
- UI must not invoke privileged OS actions directly.
- The Permission & Control Plane is the mandatory authorization choke point for computer-use and sensitive operations; untrusted model/tool text cannot mint approvals or execution permits.
- Privileged executors must consume a short-lived request-bound execution permit immediately before mutation and must revalidate live target identity to control TOCTOU/window-switch risk.
- Permission/control-plane state must fail closed on unknown capability, target, session, approval, permit or policy epoch.
- Durable logs/evidence must redact secrets and minimize user desktop data.
- Architecture changes require T3 Work Order + ADR/Decisions Ledger update.
