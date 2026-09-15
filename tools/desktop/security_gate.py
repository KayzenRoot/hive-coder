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
}

ALLOWED_INVOKE_FILE = (DESKTOP / "src" / "lib" / "desktopBridge.ts").resolve()
ALLOWED_COMMANDS = {"get_desktop_snapshot"}
EXPECTED_CAPABILITY = "desktop-read-only"
EXPECTED_WINDOW = "main"


def text_files() -> list[Path]:
    suffixes = {".rs", ".ts", ".tsx", ".json", ".toml"}
    return [p for p in DESKTOP.rglob("*") if p.is_file() and p.suffix in suffixes]


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

        if "invoke(" in text:
            invoke_count += text.count("invoke(")
            if path.resolve() != ALLOWED_INVOKE_FILE:
                failures.append(f"{rel}: invoke() outside the single desktop bridge")

        if path.suffix == ".rs":
            lines = text.splitlines()
            for index, line in enumerate(lines):
                if "#[tauri::command]" in line:
                    following = "\n".join(lines[index + 1:index + 5])
                    match = re.search(r"fn\s+([A-Za-z0-9_]+)\s*\(", following)
                    if not match:
                        failures.append(f"{rel}: unable to resolve tauri command after annotation")
                    else:
                        command_names.add(match.group(1))

    if invoke_count != 1:
        failures.append(f"expected exactly one frontend invoke(), found {invoke_count}")
    if command_names != ALLOWED_COMMANDS:
        failures.append(f"Tauri command allowlist mismatch: {sorted(command_names)}")

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
        failures.append("WO-0015 must keep installer/bundle generation disabled")

    rust_lib = (TAURI / "src" / "lib.rs").read_text(encoding="utf-8")
    if 'const DESKTOP_WINDOW_LABEL: &str = "main";' not in rust_lib:
        failures.append("read-model command must bind its trusted window label explicitly")
    if "webview_window.label()" not in rust_lib:
        failures.append("read-model command must revalidate the invoking window label")

    package = json.loads((DESKTOP / "package.json").read_text(encoding="utf-8"))
    all_deps = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
    for dep in all_deps:
        if dep.startswith("@tauri-apps/plugin-"):
            failures.append(f"Tauri plugin not approved in WO-0015: {dep}")

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

    if failures:
        print("DESKTOP_SECURITY_GATE=FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("DESKTOP_SECURITY_GATE=PASS")
    print(f"TAURI_COMMANDS={','.join(sorted(command_names))}")
    print(f"CAPABILITY={EXPECTED_CAPABILITY}")
    print(f"WINDOW_SCOPE={EXPECTED_WINDOW}")
    print("CAPABILITY_PERMISSIONS=0")
    print("LOCKFILES=COMMITTED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
