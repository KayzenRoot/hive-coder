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

## Desktop shell foundation — WO-0015
`apps/desktop/` is the first governed desktop substrate using Tauri 2 with React/TypeScript/Vite. The desktop framework does not own Hive authority.

`DesktopSnapshot v1` established a non-authoritative presentation bridge, a `main`-window-only Tauri capability with zero plugin permissions and no shell/filesystem/process plugin or generic dispatch. Future mutation remains subordinate to the canonical layering.

## Trusted workspace/Git read surface — WO-0016 promotion candidate
WO-0016 evolves the bridge without turning the UI into a filesystem authority:

`React UI -> desktopBridge.ts -> { choose_workspace | get_desktop_snapshot } -> trusted Rust application state -> DesktopSnapshot v2`

- `choose_workspace` accepts no frontend path argument. The operating-system/native picker is invoked only after explicit user interaction.
- The Rust application validates/canonicalizes the selected directory and retains it as session-owned `DesktopState`; the UI sees bounded identity/presentation fields only.
- Workspace observations are bounded, root-contained and read-only. Static symlink/reparse traversal fails closed.
- Git identity is observed from bounded `.git/HEAD`, loose ref or bounded packed-ref data, never by spawning `git`.
- Linked-worktree pointer files are intentionally reported DEGRADED rather than followed outside the selected root.
- Hive checkpoint/evidence discovery is bounded and no-follow; physical text reads enforce a byte ceiling before decoding.
- `DesktopSnapshot v2` remains presentation state, not an authorization token/capability grant.
- Tauri capability `desktop-read-only` still grants zero plugin permissions.
- Runtime/provider/permission may be shown only with explicit provenance and truthful UNKNOWN/DISCONNECTED/DEGRADED state until corresponding live adapters exist.

The remaining path-based read TOCTOU residual is acceptable only for this non-authoritative presentation slice. Before a future privileged file/Git mutation path exists, a separate governed design must establish stronger handle-relative/no-follow capability I/O and preserve the Permission & Control Plane choke point.