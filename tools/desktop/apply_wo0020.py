from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "apps" / "desktop" / "src-tauri" / "src" / "lib.rs"
GATE = ROOT / "tools" / "desktop" / "security_gate.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, found {count}")
    return text.replace(old, new, 1)


def patch_lib() -> None:
    text = LIB.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "use rfd::FileDialog;\n",
        "mod runtime_status_supervisor;\n\nuse rfd::FileDialog;\n",
        "lib module",
    )
    command = '''#[tauri::command]\nfn get_runtime_status_envelope(webview_window: tauri::WebviewWindow) -> Result<String, String> {\n    if !desktop_window_is_authorized(webview_window.label()) {\n        return Err("runtime status is unavailable for this window".to_owned());\n    }\n    runtime_status_supervisor::query_runtime_status_envelope()\n}\n\n'''
    text = replace_once(
        text,
        "#[cfg_attr(mobile, tauri::mobile_entry_point)]\npub fn run() {\n",
        command + "#[cfg_attr(mobile, tauri::mobile_entry_point)]\npub fn run() {\n",
        "lib command insertion",
    )
    text = replace_once(
        text,
        ".invoke_handler(tauri::generate_handler![get_desktop_snapshot, choose_workspace])",
        ".invoke_handler(tauri::generate_handler![get_desktop_snapshot, choose_workspace, get_runtime_status_envelope])",
        "lib invoke handler",
    )
    LIB.write_text(text, encoding="utf-8")


def patch_gate() -> None:
    text = GATE.read_text(encoding="utf-8")
    text = replace_once(
        text,
        'ALLOWED_INVOKE_FILE = (DESKTOP / "src" / "lib" / "desktopBridge.ts").resolve()\nALLOWED_COMMANDS = {"get_desktop_snapshot", "choose_workspace"}\nEXPECTED_INVOKES = 2\n',
        'ALLOWED_INVOKE_FILE = (DESKTOP / "src" / "lib" / "desktopBridge.ts").resolve()\nALLOWED_PROCESS_FILE = (TAURI / "src" / "runtime_status_supervisor.rs").resolve()\nALLOWED_COMMANDS = {"get_desktop_snapshot", "choose_workspace", "get_runtime_status_envelope"}\nEXPECTED_INVOKES = 3\n',
        "gate constants",
    )
    text = replace_once(
        text,
        '        for needle, reason in FORBIDDEN_TEXT.items():\n            if needle in text:\n                failures.append(f"{rel}: forbidden {reason}: {needle}")\n',
        '        for needle, reason in FORBIDDEN_TEXT.items():\n            if needle in text:\n                if reason == "direct Rust process execution" and path.resolve() == ALLOWED_PROCESS_FILE:\n                    continue\n                failures.append(f"{rel}: forbidden {reason}: {needle}")\n',
        "gate process exception",
    )
    text = replace_once(
        text,
        '    if re.search(r"invoke\\(CHOOSE_WORKSPACE_COMMAND\\s*,", bridge_text):\n        failures.append("choose_workspace must not receive frontend arguments")\n',
        '    if re.search(r"invoke\\(CHOOSE_WORKSPACE_COMMAND\\s*,", bridge_text):\n        failures.append("choose_workspace must not receive frontend arguments")\n    if "invoke(RUNTIME_STATUS_COMMAND);" not in bridge_text:\n        failures.append("runtime status invocation must use the named argument-free command")\n    if re.search(r"invoke\\(RUNTIME_STATUS_COMMAND\\s*,", bridge_text):\n        failures.append("runtime status command must not receive frontend arguments")\n    if "decodeRuntimeStatusEnvelope(raw)" not in bridge_text:\n        failures.append("runtime status bridge must admit raw wire only through decodeRuntimeStatusEnvelope(raw)")\n    if "JSON.parse(raw)" in bridge_text:\n        failures.append("runtime status bridge must not bypass raw-wire canonical validation with JSON.parse(raw)")\n',
        "gate bridge guards",
    )
    supervisor_block = '''    supervisor_text = ALLOWED_PROCESS_FILE.read_text(encoding="utf-8") if ALLOWED_PROCESS_FILE.is_file() else ""\n    required_supervisor_guards = [\n        'const SIDECAR_MODE: &str = "--stdio-status-v1";',\n        'const MAX_STATUS_RESPONSE_BYTES: u64 = 33_024;',\n        "std::env::current_exe()",\n        "fs::symlink_metadata",\n        "is_link_or_reparse",\n        "Command::new(&sidecar)",\n        ".arg(SIDECAR_MODE)",\n        ".env_clear()",\n        "MAX_STATUS_WIRE_BYTES",\n        "SIDECAR_TIMEOUT",\n        "terminate_child",\n    ]\n    for guard in required_supervisor_guards:\n        if guard not in supervisor_text:\n            failures.append(f"fixed runtime supervisor guard missing: {guard}")\n    for forbidden in (".args(", ".env(", "powershell", "cmd.exe", "sh -c", "bash -c", "std::env::var("):\n        if forbidden in supervisor_text:\n            failures.append(f"fixed runtime supervisor contains forbidden dynamic execution surface: {forbidden}")\n    if supervisor_text.count("Command::new(") != 1:\n        failures.append("fixed runtime supervisor must contain exactly one process spawn site")\n    process_sites = {\n        path.resolve()\n        for path in files\n        if path.suffix == ".rs" and "Command::new" in production_rust(path.read_text(encoding="utf-8"))\n    }\n    if process_sites != {ALLOWED_PROCESS_FILE}:\n        failures.append(\n            f"process execution must exist only in fixed runtime supervisor, got "\n            f"{[str(path.relative_to(ROOT)) for path in sorted(process_sites)]}"\n        )\n\n'''
    text = replace_once(
        text,
        '    if "std::process" in prod_rust:\n        failures.append("workspace/Git read path must not invoke an external process command")\n\n',
        '    if "std::process" in prod_rust:\n        failures.append("workspace/Git read path must not invoke an external process command")\n\n' + supervisor_block,
        "gate supervisor guards",
    )
    text = replace_once(
        text,
        '    print("GENERIC_PROCESS_EXECUTION=0")\n    print("APPLE_SPECIFIC_FONT_REFERENCES=0")\n',
        '    print("GENERIC_PROCESS_EXECUTION=0")\n    print("FIXED_RUNTIME_SIDECAR_PROCESS=1")\n    print("RUNTIME_STATUS_FRONTEND_ARGS=0")\n    print("RUNTIME_STATUS_RAW_WIRE_DECODER=ENFORCED")\n    print("APPLE_SPECIFIC_FONT_REFERENCES=0")\n',
        "gate output",
    )
    GATE.write_text(text, encoding="utf-8")


def main() -> None:
    patch_lib()
    patch_gate()
    print("WO0020_APPLIER=PASS")


if __name__ == "__main__":
    main()
