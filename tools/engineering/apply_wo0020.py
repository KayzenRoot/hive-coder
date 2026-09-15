from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit(f"expected exactly one patch anchor in {path}: {old[:80]!r}")
    path.write_text(text.replace(old, new), encoding="utf-8", newline="\n")


lib = ROOT / "apps/desktop/src-tauri/src/lib.rs"
replace_once(lib, "use rfd::FileDialog;\n", "mod runtime_status_supervisor;\n\nuse rfd::FileDialog;\n")
replace_once(
    lib,
    "#[cfg_attr(mobile, tauri::mobile_entry_point)]\npub fn run() {",
    "#[tauri::command]\nfn get_runtime_status_envelope(webview_window: tauri::WebviewWindow) -> Result<String, String> {\n    if !desktop_window_is_authorized(webview_window.label()) {\n        return Err(\"runtime status is unavailable for this window\".to_owned());\n    }\n    runtime_status_supervisor::query_runtime_status_envelope()\n}\n\n#[cfg_attr(mobile, tauri::mobile_entry_point)]\npub fn run() {",
)
replace_once(
    lib,
    ".invoke_handler(tauri::generate_handler![get_desktop_snapshot, choose_workspace])",
    ".invoke_handler(tauri::generate_handler![get_desktop_snapshot, choose_workspace, get_runtime_status_envelope])",
)

bridge = ROOT / "apps/desktop/src/lib/desktopBridge.ts"
replace_once(
    bridge,
    '} from "../contracts/desktopSnapshot";\n\nconst SNAPSHOT_COMMAND',
    '} from "../contracts/desktopSnapshot";\nimport { parseRuntimeStatusEnvelope, type RuntimeStatusEnvelope } from "../contracts/runtimeStatus";\n\nconst SNAPSHOT_COMMAND',
)
replace_once(
    bridge,
    'const CHOOSE_WORKSPACE_COMMAND = "choose_workspace" as const;\n',
    'const CHOOSE_WORKSPACE_COMMAND = "choose_workspace" as const;\nconst RUNTIME_STATUS_COMMAND = "get_runtime_status_envelope" as const;\n',
)
bridge_text = bridge.read_text(encoding="utf-8")
if "export async function loadRuntimeStatusEnvelope" in bridge_text:
    raise SystemExit("runtime status bridge already applied")
bridge.write_text(
    bridge_text.rstrip() + '\n\nexport async function loadRuntimeStatusEnvelope(): Promise<RuntimeStatusEnvelope | null> {\n  try {\n    const raw: unknown = await invoke(RUNTIME_STATUS_COMMAND);\n    if (typeof raw !== "string") return null;\n    return parseRuntimeStatusEnvelope(JSON.parse(raw));\n  } catch {\n    return null;\n  }\n}\n',
    encoding="utf-8",
    newline="\n",
)

app = ROOT / "apps/desktop/src/App.tsx"
replace_once(
    app,
    'import { type DesktopSnapshot, disconnectedSnapshot } from "./contracts/desktopSnapshot";\nimport { chooseWorkspace, loadDesktopSnapshot } from "./lib/desktopBridge";',
    'import { type DesktopSnapshot, disconnectedSnapshot } from "./contracts/desktopSnapshot";\nimport type { RuntimeStatusEnvelope } from "./contracts/runtimeStatus";\nimport { chooseWorkspace, loadDesktopSnapshot, loadRuntimeStatusEnvelope } from "./lib/desktopBridge";',
)
replace_once(
    app,
    '  const [snapshot, setSnapshot] = useState<DesktopSnapshot>(() => disconnectedSnapshot());\n',
    '  const [snapshot, setSnapshot] = useState<DesktopSnapshot>(() => disconnectedSnapshot());\n  const [runtimeStatus, setRuntimeStatus] = useState<RuntimeStatusEnvelope | null>(null);\n',
)
replace_once(
    app,
    '    void loadDesktopSnapshot().then((next) => {\n      if (active) setSnapshot(next);\n    });\n',
    '    void loadDesktopSnapshot().then((next) => {\n      if (active) setSnapshot(next);\n    });\n    void loadRuntimeStatusEnvelope().then((next) => {\n      if (active) setRuntimeStatus(next);\n    });\n',
)
replace_once(
    app,
    '      snapshot={snapshot}\n      choosingWorkspace={choosingWorkspace}',
    '      snapshot={snapshot}\n      runtimeStatus={runtimeStatus}\n      choosingWorkspace={choosingWorkspace}',
)

shell = ROOT / "apps/desktop/src/components/ShellView.tsx"
replace_once(
    shell,
    'import type { DesktopSnapshot, OperationalState, StatusSignal } from "../contracts/desktopSnapshot";\n',
    'import type { DesktopSnapshot, OperationalState, StatusSignal } from "../contracts/desktopSnapshot";\nimport type { RuntimeStatusEnvelope } from "../contracts/runtimeStatus";\n',
)
replace_once(
    shell,
    '  snapshot: DesktopSnapshot;\n  choosingWorkspace?: boolean;',
    '  snapshot: DesktopSnapshot;\n  runtimeStatus?: RuntimeStatusEnvelope | null;\n  choosingWorkspace?: boolean;',
)
replace_once(
    shell,
    '  snapshot,\n  choosingWorkspace = false,',
    '  snapshot,\n  runtimeStatus = null,\n  choosingWorkspace = false,',
)
replace_once(
    shell,
    '  const statusSignals = [snapshot.runtime, snapshot.provider, snapshot.git.signal, snapshot.evidence.signal, snapshot.permission];\n',
    '''  const live = runtimeStatus?.snapshot ?? null;\n  const runtimeSignal: StatusSignal = live\n    ? { state: live.runtime.state, label: "Runtime", detail: live.runtime.detail, provenance: live.runtime.provenance }\n    : snapshot.runtime;\n  const providerState: OperationalState = !live\n    ? snapshot.provider.state\n    : live.runtime.state === "DISCONNECTED"\n      ? "DISCONNECTED"\n      : live.providers.some((provider) => provider.state === "DEGRADED")\n        ? "DEGRADED"\n        : live.providers.some((provider) => provider.state === "READY")\n          ? "READY"\n          : "UNKNOWN";\n  const providerModels = live?.providers.reduce((total, provider) => total + provider.modelIds.length, 0) ?? 0;\n  const providerSignal: StatusSignal = live\n    ? {\n        state: providerState,\n        label: "Provider",\n        detail: live.providers.length > 0\n          ? `${live.providers.length} provider${live.providers.length === 1 ? "" : "s"} / ${providerModels} observed model${providerModels === 1 ? "" : "s"}. Capability authority remains evidence-driven.`\n          : "No provider catalog is connected through the runtime status channel.",\n        provenance: "runtime-status-ipc-v1",\n      }\n    : snapshot.provider;\n  const permissionSignal: StatusSignal = live\n    ? {\n        state: live.permission.state,\n        label: "Permission plane",\n        detail: live.permission.state === "READY"\n          ? `Read-only status: ${live.permission.activeSessions ?? 0} active session(s), ${live.permission.pendingApprovals ?? 0} pending approval(s).`\n          : "No actionable permission authority is exposed through the runtime status channel.",\n        provenance: "runtime-status-ipc-v1",\n      }\n    : snapshot.permission;\n  const statusSignals = [runtimeSignal, providerSignal, snapshot.git.signal, snapshot.evidence.signal, permissionSignal];\n''',
)
replace_once(
    shell,
    '              <h3>No execution session attached</h3>\n              <p>\n                Workspace and Git observations are read-only. Task execution, shell commands, file mutation and\n                computer input remain unavailable until later governed application boundaries are promoted.\n              </p>',
    '''              <h3>{live?.task ? `${live.task.taskId} · ${live.task.state}` : "No execution session attached"}</h3>\n              <p>\n                {live?.task\n                  ? `Read-only task progress: ${live.task.nodeSucceeded}/${live.task.nodeTotal} nodes succeeded, ${live.task.executions} execution(s), ${live.task.failures} failure(s). Mutation remains unavailable.`\n                  : "Workspace, Git and runtime status observations are read-only. Task execution, shell commands, file mutation and computer input remain unavailable."}\n              </p>''',
)

security = ROOT / "tools/desktop/security_gate.py"
replace_once(
    security,
    'ALLOWED_INVOKE_FILE = (DESKTOP / "src" / "lib" / "desktopBridge.ts").resolve()\nALLOWED_COMMANDS = {"get_desktop_snapshot", "choose_workspace"}\nEXPECTED_INVOKES = 2\n',
    'ALLOWED_INVOKE_FILE = (DESKTOP / "src" / "lib" / "desktopBridge.ts").resolve()\nALLOWED_PROCESS_FILE = (TAURI / "src" / "runtime_status_supervisor.rs").resolve()\nALLOWED_COMMANDS = {"get_desktop_snapshot", "choose_workspace", "get_runtime_status_envelope"}\nEXPECTED_INVOKES = 3\n',
)
replace_once(
    security,
    '        for needle, reason in FORBIDDEN_TEXT.items():\n            if needle in text:\n                failures.append(f"{rel}: forbidden {reason}: {needle}")\n',
    '        for needle, reason in FORBIDDEN_TEXT.items():\n            if needle in text:\n                if reason == "direct Rust process execution" and path.resolve() == ALLOWED_PROCESS_FILE:\n                    continue\n                failures.append(f"{rel}: forbidden {reason}: {needle}")\n',
)
replace_once(
    security,
    '    if re.search(r"invoke\\(CHOOSE_WORKSPACE_COMMAND\\s*,", bridge_text):\n        failures.append("choose_workspace must not receive frontend arguments")\n',
    '    if re.search(r"invoke\\(CHOOSE_WORKSPACE_COMMAND\\s*,", bridge_text):\n        failures.append("choose_workspace must not receive frontend arguments")\n    if "invoke(RUNTIME_STATUS_COMMAND);" not in bridge_text:\n        failures.append("runtime status invocation must use the named argument-free command")\n    if re.search(r"invoke\\(RUNTIME_STATUS_COMMAND\\s*,", bridge_text):\n        failures.append("runtime status command must not receive frontend arguments")\n',
)
insert_anchor = '    package = json.loads((DESKTOP / "package.json").read_text(encoding="utf-8"))\n'
supervisor_gate = '''    supervisor_text = ALLOWED_PROCESS_FILE.read_text(encoding="utf-8") if ALLOWED_PROCESS_FILE.is_file() else ""\n    required_supervisor_guards = [\n        'const SIDECAR_MODE: &str = "--stdio-status-v1";',\n        "std::env::current_exe()",\n        "Command::new(&sidecar)",\n        ".arg(SIDECAR_MODE)",\n        ".env_clear()",\n        "MAX_STATUS_RESPONSE_BYTES",\n        "SIDECAR_TIMEOUT",\n    ]\n    for guard in required_supervisor_guards:\n        if guard not in supervisor_text:\n            failures.append(f"fixed runtime supervisor guard missing: {guard}")\n    for forbidden in (".args(", "powershell", "cmd.exe", "sh -c", "bash -c", "std::env::var("):\n        if forbidden in supervisor_text:\n            failures.append(f"fixed runtime supervisor contains forbidden dynamic execution surface: {forbidden}")\n    process_sites = [path for path in files if path.suffix == ".rs" and "Command::new" in production_rust(path.read_text(encoding="utf-8"))]\n    if process_sites != [ALLOWED_PROCESS_FILE]:\n        failures.append(f"process execution must exist only in fixed runtime supervisor, got {[str(path.relative_to(ROOT)) for path in process_sites]}")\n\n'''
replace_once(security, insert_anchor, supervisor_gate + insert_anchor)
replace_once(
    security,
    '    print("GENERIC_PROCESS_EXECUTION=0")\n',
    '    print("GENERIC_PROCESS_EXECUTION=0")\n    print("FIXED_RUNTIME_SIDECAR_PROCESS=1")\n',
)

test = ROOT / "apps/desktop/src/components/RuntimeStatusSurface.test.tsx"
test.write_text('''import { renderToStaticMarkup } from "react-dom/server";\nimport { describe, expect, it } from "vitest";\nimport { disconnectedSnapshot } from "../contracts/desktopSnapshot";\nimport type { RuntimeStatusEnvelope } from "../contracts/runtimeStatus";\nimport { ShellView } from "./ShellView";\n\nconst liveStatus: RuntimeStatusEnvelope = {\n  protocol: "hive-runtime-status-ipc-v1",\n  requestId: "desktop-runtime",\n  ok: true,\n  snapshot: {\n    schema: "hive-runtime-status-v1",\n    runtime: { state: "READY", provenance: "fixture-runtime", detail: "Runtime observer connected." },\n    providers: [{ providerId: "opencode-go", modelIds: ["fixture-model"], state: "READY" }],\n    task: { taskId: "task-20", state: "running", nodeTotal: 3, nodeSucceeded: 1, executions: 1, failures: 0 },\n    permission: { state: "UNKNOWN", policyEpoch: null, activeSessions: null, pendingApprovals: null },\n  },\n};\n\ndescribe("Runtime System Truth surface", () => {\n  it("renders live read-only runtime/provider/task truth without enabling mutation", () => {\n    const html = renderToStaticMarkup(<ShellView snapshot={disconnectedSnapshot()} runtimeStatus={liveStatus} />);\n    expect(html).toContain("Runtime observer connected.");\n    expect(html).toContain("1 provider / 1 observed model");\n    expect(html).toContain("task-20 · running");\n    expect(html).toContain("1/3 nodes succeeded");\n    expect(html).toContain("Mutation remains unavailable");\n    expect(html).toContain("Emergency stop");\n    expect(html.match(/disabled=\"\"/g)?.length ?? 0).toBeGreaterThanOrEqual(8);\n  });\n});\n''', encoding="utf-8", newline="\n")

print("WO0020_PATCH=APPLIED")
