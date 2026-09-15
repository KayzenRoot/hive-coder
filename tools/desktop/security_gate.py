from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DESKTOP = ROOT / "apps" / "desktop"
TAURI = DESKTOP / "src-tauri"

FORBIDDEN_TEXT = {
    "tauri_plugin_shell": "Rust shell plugin",
    "@tauri-apps/plugin-shell": "frontend shell plugin",
    "std::process::Command": "direct Rust process execution",
    "Command::new": "direct Rust process execution",
    "@tauri-apps/plugin-fs": "filesystem plugin",
    "tauri_plugin_fs": "Rust filesystem plugin",
    "@tauri-apps/plugin-process": "process plugin",
    "tauri_plugin_process": "Rust process plugin",
    "dangerouslySetInnerHTML": "untrusted HTML sink",
    "OPENAI_API_KEY": "provider credential reference",
    "ANTHROPIC_API_KEY": "provider credential reference",
    "GEMINI_API_KEY": "provider credential reference",
    "-apple-system": "Apple-specific UI font reference",
    "BlinkMacSystemFont": "Apple-specific UI font reference",
    "SFMono-Regular": "Apple-specific UI font reference",
}

PRODUCTION_RUST_WRITE_PRIMITIVES = {
    "fs::write(": "filesystem write",
    "File::create(": "filesystem create",
    "OpenOptions": "filesystem open-for-mutation",
    "remove_file(": "filesystem delete",
    "remove_dir(": "filesystem directory delete",
    "remove_dir_all(": "recursive filesystem delete",
    "create_dir(": "filesystem directory create",
    "create_dir_all(": "recursive filesystem directory create",
    "fs::rename(": "filesystem rename",
    ".write_all(": "filesystem write",
    ".set_len(": "filesystem truncate",
}

ALLOWED_INVOKE_FILE = (DESKTOP / "src" / "lib" / "desktopBridge.ts").resolve()
ALLOWED_COMMANDS = {"get_desktop_snapshot", "choose_workspace"}
EXPECTED_INVOKES = 2
EXPECTED_CAPABILITY = "desktop-read-only"
EXPECTED_WINDOW = "main"


def text_files() -> list[Path]:
    suffixes = {".rs", ".ts", ".tsx", ".json", ".toml", ".css"}
    return [p for p in DESKTOP.rglob("*") if p.is_file() and p.suffix in suffixes]


def production_rust(text: str) -> str:
    return text.split("#[cfg(test)]", 1)[0]


def main() -> int:
    failures: list[str] = []
    files = text_files()
    if not files:
        failures.append("desktop source tree is empty")

    package_lock = DESKTOP / "package-lock.json"
    cargo_lock = TAURI / "Cargo.lock"
    if not package_lock.is_file():
        failures.append("package-lock.json must be committed")
    if not cargo_lock.is_file():
        failures.append("Cargo.lock must be committed")

    command_names: set[str] = set()
    invoke_count = 0

    for path in files:
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(ROOT)
        for needle, reason in FORBIDDEN_TEXT.items():
            if needle in text:
                failures.append(f"{rel}: forbidden {reason}: {needle}")

        if path.suffix == ".rs":
            prod = production_rust(text)
            for needle, reason in PRODUCTION_RUST_WRITE_PRIMITIVES.items():
                if needle in prod:
                    failures.append(f"{rel}: forbidden production {reason}: {needle}")

        if "invoke(" in text:
            invoke_count += text.count("invoke(")
            if path.resolve() != ALLOWED_INVOKE_FILE:
                failures.append(f"{rel}: invoke() outside the single desktop bridge")

        if path.suffix == ".rs":
            lines = text.splitlines()
            for index, line in enumerate(lines):
                if "#[tauri::command]" in line:
                    following = "\n".join(lines[index + 1:index + 10])
                    match = re.search(r"fn\s+([A-Za-z0-9_]+)\s*\(", following)
                    if not match:
                        failures.append(f"{rel}: unable to resolve tauri command after annotation")
                    else:
                        command_names.add(match.group(1))

    if invoke_count != EXPECTED_INVOKES:
        failures.append(f"expected exactly {EXPECTED_INVOKES} frontend invoke() calls, found {invoke_count}")
    if command_names != ALLOWED_COMMANDS:
        failures.append(f"Tauri command allowlist mismatch: {sorted(command_names)}")

    bridge_text = ALLOWED_INVOKE_FILE.read_text(encoding="utf-8")
    if "invoke(CHOOSE_WORKSPACE_COMMAND);" not in bridge_text:
        failures.append("choose_workspace frontend invocation must carry no caller-controlled path/payload")
    if re.search(r"invoke\(CHOOSE_WORKSPACE_COMMAND\s*,", bridge_text):
        failures.append("choose_workspace must not receive frontend arguments")

    capability_path = TAURI / "capabilities" / "desktop-read-only.json"
    capability = json.loads(capability_path.read_text(encoding="utf-8"))
    if capability.get("identifier") != EXPECTED_CAPABILITY:
        failures.append("desktop capability identifier mismatch")
    if capability.get("windows") != [EXPECTED_WINDOW]:
        failures.append(f"desktop capability must target only [{EXPECTED_WINDOW!r}]")
    if capability.get("permissions") != []:
        failures.append(f"desktop capability permissions must be empty, got {capability.get('permissions')!r}")

    tauri_config = json.loads((TAURI / "tauri.conf.json").read_text(encoding="utf-8"))
    app_config = tauri_config.get("app", {})
    security = app_config.get("security", {})
    if security.get("capabilities") != [EXPECTED_CAPABILITY]:
        failures.append("tauri.conf must enable only the desktop-read-only capability")
    if tauri_config.get("app", {}).get("withGlobalTauri") not in (None, False):
        failures.append("global Tauri JavaScript API must remain disabled")

    windows = app_config.get("windows")
    if not isinstance(windows, list) or len(windows) != 1 or windows[0].get("label") != EXPECTED_WINDOW:
        failures.append("tauri.conf must declare exactly one window labeled main")
    elif "url" in windows[0]:
        failures.append("main production window must not declare a remote URL")

    csp = security.get("csp")
    if not isinstance(csp, str) or "default-src 'self'" not in csp:
        failures.append("desktop CSP must be explicit and default to self")
    if security.get("dangerousDisableAssetCspModification") not in (None, False):
        failures.append("Tauri asset CSP modification must not be disabled")

    bundle = tauri_config.get("bundle", {})
    if bundle.get("active") is not False:
        failures.append("installer/bundle generation must remain disabled in current governed desktop scope")

    rust_lib = (TAURI / "src" / "lib.rs").read_text(encoding="utf-8")
    prod_rust = production_rust(rust_lib)
    required_workspace_guards = [
        'const DESKTOP_WINDOW_LABEL: &str = "main";',
        "webview_window.label()",
        "validate_workspace_root",
        "safe_existing_path",
        "fs::canonicalize",
        "is_link_or_reparse",
        "MAX_TOP_LEVEL_ENTRIES",
        "MAX_EVIDENCE_BUNDLES",
    ]
    for guard in required_workspace_guards:
        if guard not in prod_rust:
            failures.append(f"trusted workspace guard missing: {guard}")

    choose_match = re.search(r"fn\s+choose_workspace\s*\((.*?)\)\s*->", prod_rust, re.DOTALL)
    if not choose_match:
        failures.append("choose_workspace command signature not found")
    else:
        signature = choose_match.group(1)
        if any(token in signature for token in ("String", "Path", "PathBuf", "Vec<", "serde_json", "Value")):
            failures.append("choose_workspace command accepts caller-controlled target/payload")

    if "std::process" in prod_rust or "git " in prod_rust.lower():
        failures.append("workspace/Git read path must not invoke an external git/process command")

    package = json.loads((DESKTOP / "package.json").read_text(encoding="utf-8"))
    all_deps = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
    for dep in all_deps:
        if dep.startswith("@tauri-apps/plugin-"):
            failures.append(f"Tauri plugin not approved in current desktop scope: {dep}")

    cargo_toml = (TAURI / "Cargo.toml").read_text(encoding="utf-8")
    if 'rfd = { version = "=0.17.2", default-features = false }' not in cargo_toml:
        failures.append("native picker dependency must remain exact-pinned and minimal")
    if "gix" in cargo_toml:
        failures.append("WO-0016 Git HEAD observation must not add the broad gix dependency graph")

    if package_lock.is_file():
        lock = json.loads(package_lock.read_text(encoding="utf-8"))
        root_package = lock.get("packages", {}).get("", {})
        if root_package.get("dependencies") != package.get("dependencies"):
            failures.append("package-lock runtime dependencies differ from package.json")
        if root_package.get("devDependencies") != package.get("devDependencies"):
            failures.append("package-lock dev dependencies differ from package.json")

    if cargo_lock.is_file():
        cargo_text = cargo_lock.read_text(encoding="utf-8")
        if not cargo_text.startswith("# This file is automatically @generated by Cargo.\n"):
            failures.append("Cargo.lock missing generated-file header")
        if "\nversion = 4\n" not in cargo_text[:200]:
            failures.append("Cargo.lock must use lockfile version 4")
        if 'name = "rfd"' not in cargo_text or 'version = "0.17.2"' not in cargo_text:
            failures.append("Cargo.lock must contain exact rfd 0.17.2 resolution")

    if failures:
        print("DESKTOP_SECURITY_GATE=FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("DESKTOP_SECURITY_GATE=PASS")
    print(f"TAURI_COMMANDS={','.join(sorted(command_names))}")
    print(f"FRONTEND_INVOKES={invoke_count}")
    print(f"CAPABILITY={EXPECTED_CAPABILITY}")
    print(f"WINDOW_SCOPE={EXPECTED_WINDOW}")
    print("CAPABILITY_PERMISSIONS=0")
    print("WORKSPACE_SELECTION_ARGS=0")
    print("FILESYSTEM_MUTATION_PRIMITIVES=0")
    print("GENERIC_PROCESS_EXECUTION=0")
    print("APPLE_SPECIFIC_FONT_REFERENCES=0")
    print("LOCKFILES=COMMITTED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
