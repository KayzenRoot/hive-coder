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

## Desktop shell foundation — WO-0015 candidate
`apps/desktop/` is the first governed desktop substrate. It uses Tauri 2 with React/TypeScript/Vite, but the desktop framework does not own Hive authority.

The WO-0015 application bridge is deliberately read-only:

`React UI -> desktopBridge.ts -> get_desktop_snapshot -> DesktopSnapshot v1`

- `get_desktop_snapshot` is the only Tauri command in the increment.
- The command accepts no user-controlled execution payload and fails closed unless invoked from the WebView window labelled `main`.
- `DesktopSnapshot v1` is presentation state, not an authorization token or capability grant.
- Tauri capability `desktop-read-only` grants zero plugin permissions.
- Shell/filesystem/process plugins and generic command dispatch are absent.
- Runtime/provider/Git/evidence/permission signals may be shown only with explicit provenance and truthful UNKNOWN/DISCONNECTED/DEGRADED state when the corresponding live adapter is absent.
- Safety controls may be visible before they are actionable, but they must remain disabled until a later governed session exposes a trusted action path.

Any future desktop mutation path must preserve the canonical layering: UI -> application/orchestrator -> Permission & Control Plane -> capability adapter/executor. A Tauri command must never become a bypass around the existing permit model.
