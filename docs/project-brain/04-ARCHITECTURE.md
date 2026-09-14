# Architecture — Hive Coder

Target layered architecture:

`Hive Desktop UI -> Hive Application/Orchestrator -> Capability Adapters -> Runtime/Providers/Computer Use -> OS/Apps`.

Initial capability adapters: `InterpreterAdapter`, `ComputerUseAdapter(Cua)`, `ProviderAdapter(OpenCode Go + others)`, `GitAdapter`, `Shell/FileAdapter`, `BrowserAdapter`, and governance/evidence integration.

Rules:
- Hive-facing contracts own subsystem boundaries.
- External foundations stay behind adapters to permit replacement/upgrades.
- UI must not invoke privileged OS actions directly.
- Permission engine gates computer-use and sensitive operations.
- Durable logs/evidence must redact secrets and minimize user desktop data.
- Architecture changes require T3 Work Order + ADR/Decisions Ledger update.
