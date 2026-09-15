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

## Trusted workspace/Git read surface — WO-0016
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

## Runtime observability presentation boundary — WO-0017
WO-0017 adds a Python-side presentation contract without connecting it to desktop process lifecycle or granting execution authority:

`Existing Python engines -> bounded public observation/reduction -> RuntimeStatusSnapshot v1 -> future trusted IPC -> desktop presentation`

Architectural rules for this contract:
- `RuntimeStatusSnapshot v1` is presentation data only and can never substitute for Permission & Control Plane authorization, CP permits, trusted capability evidence or task-control authority.
- The JSON boundary is versioned, byte-bounded and strict. Unknown fields, duplicate keys, invalid states, invalid counters and unbounded collections fail closed.
- Runtime/provider/task/permission records use canonical Hive-owned provenance identities. Caller-defined labels do not become provenance.
- Provider `READY` means a concrete bounded local catalog observation exists. It does not assert provider reachability/authentication and does not promote model capability to VERIFIED.
- The task reducer consumes bounded public `TaskSnapshot` state and excludes plan fingerprints, attempts, event payloads, prompts and outputs.
- The Permission & Control Plane has no approved public live counter observer in WO-0017. The architecture therefore reports UNKNOWN/DISCONNECTED rather than reaching into private session/challenge/permit state.
- Invalid observation/transport data may reduce only to a fixed generic `DEGRADED` snapshot. Error details and rejected values are not echoed into presentation state.
- `tools/runtime/status_snapshot.py` is a disconnected diagnostic exporter, not a host process, provider runner or authority service.

WO-0017 intentionally stops before process identity, sidecar launch, wire framing/lifecycle and desktop transport. CP-0017 is canonical and the next layer must preserve these authority limits.

## Cross-runtime runtime-status IPC boundary — WO-0018
WO-0018 freezes the cross-language presentation wire before any desktop process lifecycle is admitted:

`RuntimeStatusSnapshot v1 -> hive-runtime-status-ipc-v1/status.snapshot -> strict raw TypeScript decoder -> presentation only`

Architecture rules:
- `hive-runtime-status-ipc-v1` contains exactly one operation: `status.snapshot`.
- Request and response use deterministic canonical JSON with bounded UTF-8 size. Snapshot semantics remain owned by CP-0017 rather than redefined by transport.
- Desktop response admission must traverse `decodeRuntimeStatusEnvelope(raw)`; the lower-level semantic parser is private so callers cannot bypass raw-wire canonicality.
- Request ceiling is 512 bytes, snapshot ceiling remains 32,768 bytes, and total response ceiling is 33,024 bytes.
- The Python `serve_one()` primitive receives a prebuilt validated snapshot and owns no callback/provider/model/process/task/permission lifecycle.
- The protocol introduces no generic RPC namespace, socket listener, WebSocket, HTTP service or Tauri command.
- Status transport remains non-authoritative and cannot become a permit, capability verifier, task command or permission decision.

CP-0018 canonicalizes this frozen IPC boundary only. The separately governed runtime sidecar/supervisor layer may later consume this protocol, but it may not expand it silently. Process launch, identity/authenticity, restart/shutdown and containment remain outside WO-0018.

## Fixed runtime-status sidecar boundary — WO-0019
WO-0019 canonicalizes the first process-level consumer of the frozen CP-0018 wire without connecting that process to the desktop:

`future trusted supervisor -> fixed status_sidecar.py --stdio-status-v1 -> CP-0018 serve_one -> prebuilt CP-0017 disconnected snapshot`

Architecture rules:
- the helper has one fixed mode and no caller-selectable executable/command dispatch;
- it constructs `disconnected_snapshot()` before entering the protocol primitive, so `serve_one()` still owns no observation callback or runtime lifecycle;
- one process invocation serves one request and exits; there is no loop, daemon, socket, listener, HTTP/WebSocket surface or generic RPC namespace;
- expected invalid mode/protocol input fails closed with stable process exit codes and no fake snapshot;
- process-level validation uses canonical `ManagedStdioProcess`, preserving `shell=False` and its least-privilege child environment;
- the sidecar itself gains no provider/model, credential, task, permission or mutation adapter;
- presentation truth remains non-authoritative and intentionally DISCONNECTED until a later separately governed trusted observer/supervisor exists.

CP-0019 adds no Tauri command, process plugin or desktop launcher. The next governed layer, WO-0020, must be freshly reconstructed on canonical CP-0019 and separately prove helper identity, fixed launch target, lifecycle/containment and read-only system-truth integration before any desktop process capability can be promoted.
