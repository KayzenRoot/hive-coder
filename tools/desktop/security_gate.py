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

# Install/restart authority is HCODER-DIST-001E. Production Rust in this slice may
# verify and hold a candidate, but may never mutate the running product.
PRODUCTION_RUST_INSTALL_PRIMITIVES = {
    ".install(": "updater install call",
    "restart_app": "restart command",
    "install_update": "install command",
    "relaunch": "relaunch authority",
}

# The updater trust root is Rust-side configuration only. A frontend that names
# any of these keys is describing trust it does not own, which is the exact
# caller-selected-trust surface HCODER-WO-0027 forbids.
FRONTEND_FORBIDDEN_UPDATE_TEXT = {
    "@tauri-apps/plugin-updater": "guest updater plugin dependency",
    "plugin:updater": "guest updater plugin permission",
    "updater:default": "guest updater plugin permission",
    "pubkey": "updater trust root in frontend source",
    "endpoints": "updater endpoint list in frontend source",
    "requireSignedVersion": "updater trust config in frontend source",
    "allowDowngrades": "updater downgrade config in frontend source",
    "dangerousInsecureTransportProtocol": "updater transport config in frontend source",
    "dangerousAcceptInvalidCerts": "updater TLS-weakening config in frontend source",
    "dangerousAcceptInvalidHostnames": "updater host-weakening config in frontend source",
    "install_update": "install command surface",
    "restart_app": "restart command surface",
}

# Delta-001 admits exactly this node, and nothing else, under plugins.updater.
EXPECTED_UPDATER_CONFIG = {
    "pubkey": "",
    "endpoints": [],
    "requireSignedVersion": True,
    "allowDowngrades": False,
    "dangerousInsecureTransportProtocol": False,
    "dangerousAcceptInvalidCerts": False,
    "dangerousAcceptInvalidHostnames": False,
}

# 2.11.x deserializes the updater config with unknown keys ignored, so a pin below
# 2.12.0 would silently drop requireSignedVersion/allowDowngrades and keep running.
MIN_UPDATER_PLUGIN_VERSION = (2, 12, 0)

# A signed-version requirement is only honourable if the tool that signs the
# artifact writes the version into the minisign trusted comment. Upstream added
# that in `@tauri-apps/cli-v2.11.5` (`updater_signature.rs` appends
# "\tversion:{version}" and refuses a version carrying a tab or newline); at
# v2.11.4 the same file builds `format!("timestamp:{}\tfile:{}", ..)` and records
# no version at all. Below this floor the admitted trust posture is
# unsatisfiable by anything this repository can build, so it fails the gate
# rather than being left as a comment in an evidence file.
MIN_TAURI_CLI_VERSION = (2, 11, 5)

ALLOWED_INVOKE_FILE = (DESKTOP / "src" / "lib" / "desktopBridge.ts").resolve()
ALLOWED_PROCESS_FILE = (TAURI / "src" / "runtime_status_supervisor.rs").resolve()
ALLOWED_UPDATER_ADMISSION_FILE = (TAURI / "src" / "update_admission.rs").resolve()
FRONTEND_SOURCE = (DESKTOP / "src").resolve()
ALLOWED_COMMANDS = {
    "get_desktop_snapshot",
    "choose_workspace",
    "get_runtime_status_envelope",
    "get_update_status",
    "check_for_update",
    "download_update_candidate",
}
# Every command reachable from the guest must take no caller-supplied data. The
# three update commands additionally receive only Tauri-injected handles, which
# carry no path, version, URL or payload.
ARGUMENT_FREE_COMMANDS = (
    "choose_workspace",
    "get_runtime_status_envelope",
    "get_update_status",
    "check_for_update",
    "download_update_candidate",
)
CALLER_CONTROLLED_SIGNATURE_TOKENS = ("String", "Path", "PathBuf", "Vec<", "serde_json", "Value")
EXPECTED_COMMAND_CONSTANTS = {
    "SNAPSHOT_COMMAND": "get_desktop_snapshot",
    "CHOOSE_WORKSPACE_COMMAND": "choose_workspace",
    "RUNTIME_STATUS_COMMAND": "get_runtime_status_envelope",
    "UPDATE_STATUS_COMMAND": "get_update_status",
    "UPDATE_CHECK_COMMAND": "check_for_update",
    "UPDATE_DOWNLOAD_COMMAND": "download_update_candidate",
}
EXPECTED_INVOKES = 6
EXPECTED_CAPABILITY = "desktop-read-only"
EXPECTED_WINDOW = "main"

# Dependency and build output trees are gitignored and never part of a candidate
# head. Scanning them would make the verdict depend on whether a developer had
# installed the graph locally rather than on what the head actually authorises.
UNTRACKED_ARTIFACT_DIRS = {"node_modules", "target", "dist", "build", "__pycache__", ".venv"}


def text_files() -> list[Path]:
    suffixes = {".rs", ".ts", ".tsx", ".json", ".toml", ".css"}
    found = []
    for path in DESKTOP.rglob("*"):
        if not path.is_file() or path.suffix not in suffixes:
            continue
        if UNTRACKED_ARTIFACT_DIRS.intersection(path.relative_to(DESKTOP).parts):
            continue
        found.append(path)
    return found


def production_rust(text: str) -> str:
    return text.split("#[cfg(test)]", 1)[0]


def locked_version(lock_text: str, package: str) -> str | None:
    match = re.search(
        rf'\[\[package\]\]\nname = "{re.escape(package)}"\nversion = "([^"]+)"',
        lock_text,
    )
    return match.group(1) if match else None


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
                if reason == "direct Rust process execution" and path.resolve() == ALLOWED_PROCESS_FILE:
                    continue
                failures.append(f"{rel}: forbidden {reason}: {needle}")

        if path.suffix == ".rs":
            prod = production_rust(text)
            for needle, reason in PRODUCTION_RUST_WRITE_PRIMITIVES.items():
                if needle in prod:
                    failures.append(f"{rel}: forbidden production {reason}: {needle}")
            for needle, reason in PRODUCTION_RUST_INSTALL_PRIMITIVES.items():
                if needle in prod:
                    failures.append(f"{rel}: forbidden production {reason}: {needle}")

        if path.suffix in {".ts", ".tsx"} and FRONTEND_SOURCE in path.resolve().parents:
            for needle, reason in FRONTEND_FORBIDDEN_UPDATE_TEXT.items():
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
    # Each command is reached through its own module-level `as const` literal. An
    # invoke site that names anything else, or that passes an argument, would turn
    # these bindings back into a generic invoke surface the caller controls.
    for constant, command in EXPECTED_COMMAND_CONSTANTS.items():
        if f'const {constant} = "{command}" as const;' not in bridge_text:
            failures.append(f"{constant} must bind literal command {command!r} as an as-const value")
    invoke_sites = re.findall(r"invoke\(([^)]*)\)", bridge_text)
    if len(invoke_sites) != EXPECTED_INVOKES:
        failures.append(f"desktop bridge must declare exactly {EXPECTED_INVOKES} invoke sites, found {len(invoke_sites)}")
    for argument in invoke_sites:
        if argument not in EXPECTED_COMMAND_CONSTANTS:
            failures.append(f"invoke site must name a declared constant and carry no arguments, got invoke({argument})")
    if "decodeRuntimeStatusEnvelope(raw)" not in bridge_text:
        failures.append("runtime status bridge must admit raw wire only through decodeRuntimeStatusEnvelope(raw)")
    if "evaluateStatus(raw)" not in bridge_text:
        failures.append("update bridge must admit raw wire only through evaluateStatus(raw)")
    if "JSON.parse(raw)" in bridge_text:
        failures.append("runtime status bridge must not bypass canonical raw-wire validation with JSON.parse(raw)")

    capability_path = TAURI / "capabilities" / "desktop-read-only.json"
    capability = json.loads(capability_path.read_text(encoding="utf-8"))
    if capability.get("identifier") != EXPECTED_CAPABILITY:
        failures.append("desktop capability identifier mismatch")
    if capability.get("windows") != [EXPECTED_WINDOW]:
        failures.append(f"desktop capability must target only [{EXPECTED_WINDOW!r}]")
    if capability.get("permissions") != []:
        failures.append(f"desktop capability permissions must be empty, got {capability.get('permissions')!r}")

    # Zero-Guest: no capability in the tree may name the updater plugin, so the
    # plugin's own guest commands stay unreachable from the webview.
    for capability_file in sorted((TAURI / "capabilities").rglob("*.json")):
        if "updater" in capability_file.read_text(encoding="utf-8"):
            failures.append(f"{capability_file.relative_to(ROOT)}: guest updater permission must not be referenced")

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
    if bundle.get("createUpdaterArtifacts") is True:
        failures.append("updater artifact generation must not be enabled by this slice")

    # Context Lock Delta-001 unfroze exactly one config node, and only in its
    # fail-closed posture: empty pubkey and empty endpoints are the explicit
    # "no trust root" state, never a usable configuration.
    plugins = tauri_config.get("plugins")
    if not isinstance(plugins, dict) or list(plugins) != ["updater"]:
        failures.append(f"only the updater plugin node may be configured, got {sorted(plugins or {})!r}")
    updater_node = plugins.get("updater") if isinstance(plugins, dict) else None
    if not isinstance(updater_node, dict):
        failures.append("tauri.conf must carry an explicit updater plugin object")
    elif updater_node != EXPECTED_UPDATER_CONFIG:
        drifted = [
            key
            for key in EXPECTED_UPDATER_CONFIG
            if key not in updater_node or updater_node[key] != EXPECTED_UPDATER_CONFIG[key]
        ]
        drifted += [key for key in updater_node if key not in EXPECTED_UPDATER_CONFIG]
        failures.append(f"updater plugin node must equal the Delta-001 fail-closed posture, drifted: {sorted(set(drifted))}")

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

    # Only the six governed commands may be reachable, and each must be declared
    # exactly once in the handler; a seventh registration would be an unlisted
    # authority surface even if its Rust function exists.
    handler = re.search(r"generate_handler!\[(.*?)\]", prod_rust, re.DOTALL)
    if handler is None:
        failures.append("tauri command handler list not found")
    else:
        registered = {name.strip() for name in handler.group(1).replace("\n", " ").split(",") if name.strip()}
        if registered != ALLOWED_COMMANDS:
            failures.append(f"registered command set mismatch: {sorted(registered)}")

    # The update commands are the third argument-free family: they carry no
    # version, URL, target, key, payload or install choice from the guest.
    for command in ARGUMENT_FREE_COMMANDS:
        match = re.search(rf"fn\s+{command}\s*\((.*?)\)\s*->", prod_rust, re.DOTALL)
        if match is None:
            failures.append(f"{command} command signature not found")
            continue
        signature = match.group(1)
        offenders = [token for token in CALLER_CONTROLLED_SIGNATURE_TOKENS if token in signature]
        if offenders:
            failures.append(f"{command} command accepts caller-controlled data: {offenders}")

    if "std::process" in prod_rust:
        failures.append("workspace/Git read path must not invoke an external process command")

    supervisor_text = ALLOWED_PROCESS_FILE.read_text(encoding="utf-8") if ALLOWED_PROCESS_FILE.is_file() else ""
    supervisor_prod = production_rust(supervisor_text)
    required_supervisor_guards = [
        'const SIDECAR_MODE: &str = "--stdio-status-v1";',
        'const STATUS_REQUEST: &str = "{\\\"op\\\":\\\"status.snapshot\\\",\\\"protocol\\\":\\\"hive-runtime-status-ipc-v1\\\",\\\"requestId\\\":\\\"desktop-runtime\\\"}";',
        "const MAX_STATUS_RESPONSE_BYTES: u64 = 33_024;",
        "std::env::current_exe()",
        "Command::new(&sidecar)",
        ".arg(SIDECAR_MODE)",
        ".env_clear()",
        "SIDECAR_TIMEOUT",
        "terminate_child",
        "fs::symlink_metadata",
    ]
    for guard in required_supervisor_guards:
        if guard not in supervisor_prod:
            failures.append(f"fixed runtime supervisor guard missing: {guard}")
    if supervisor_prod.count("Command::new") != 1:
        failures.append(f"fixed runtime supervisor must contain exactly one Command::new site, found {supervisor_prod.count('Command::new')}")
    for forbidden in (".args(", ".env(", "powershell", "cmd.exe", "sh -c", "bash -c", "std::env::var(", "std::env::vars("):
        if forbidden in supervisor_prod:
            failures.append(f"fixed runtime supervisor contains forbidden dynamic execution surface: {forbidden}")
    process_sites = [path for path in files if path.suffix == ".rs" and "Command::new" in production_rust(path.read_text(encoding="utf-8"))]
    if process_sites != [ALLOWED_PROCESS_FILE]:
        failures.append(f"process execution must exist only in fixed runtime supervisor, got {[str(path.relative_to(ROOT)) for path in process_sites]}")

    # The updater plugin may be touched by exactly two Rust files: the command
    # wiring in lib.rs and the admission law in update_admission.rs. Any third
    # file that names the plugin is a second, unreviewed trust surface.
    plugin_sites = [
        path
        for path in files
        if path.suffix == ".rs" and "tauri_plugin_updater" in production_rust(path.read_text(encoding="utf-8"))
    ]
    if {path.resolve() for path in plugin_sites} != {
        (TAURI / "src" / "lib.rs").resolve(),
        ALLOWED_UPDATER_ADMISSION_FILE,
    }:
        failures.append(f"updater plugin must be referenced only by lib.rs and update_admission.rs, got {[str(p.relative_to(ROOT)) for p in plugin_sites]}")

    admission_text = (
        ALLOWED_UPDATER_ADMISSION_FILE.read_text(encoding="utf-8")
        if ALLOWED_UPDATER_ADMISSION_FILE.is_file()
        else ""
    )
    if not admission_text:
        failures.append("update_admission.rs is missing, so the updater has no Hive trust surface")
    admission_prod = production_rust(admission_text)
    required_admission_guards = [
        # Compile-time proof that the pinned plugin really exposes both trust keys;
        # a pin that drops either field must stop compiling, not degrade silently.
        "config.require_signed_version",
        "config.allow_downgrades",
        # Upstream ignores unknown config keys, so the Hive probe must not.
        '#[serde(deny_unknown_fields, rename_all = "camelCase")]',
        "fn resolve_trust",
        "fn expected_platform",
        "fn evaluate_admission",
    ]
    for guard in required_admission_guards:
        if guard not in admission_prod:
            failures.append(f"updater admission guard missing: {guard}")

    required_command_guards = [
        ".manage(UpdateAdmissionBridge::default())",
        ".plugin(tauri_plugin_updater::Builder::new().build())",
        "updater_builder()",
        ".download(",
        "resolve_trust",
    ]
    for guard in required_command_guards:
        if guard not in prod_rust:
            failures.append(f"update command guard missing: {guard}")

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
    # A pin below 2.12.0 keeps building and keeps *passing* Hive-side policy checks
    # while silently discarding requireSignedVersion/allowDowngrades upstream, so
    # the floor is law here rather than a comment.
    pin = re.search(r'tauri-plugin-updater\s*=\s*"=(\d+)\.(\d+)\.(\d+)"', cargo_toml)
    resolved_plugin_pin = ".".join(pin.groups()) if pin else "ABSENT"
    if pin is None:
        failures.append('tauri-plugin-updater must be exact-pinned as "=x.y.z"')
    elif tuple(int(part) for part in pin.groups()) < MIN_UPDATER_PLUGIN_VERSION:
        failures.append(
            "tauri-plugin-updater must be at least "
            + ".".join(str(part) for part in MIN_UPDATER_PLUGIN_VERSION)
            + ": older pins ignore the signed-version and downgrade keys"
        )

    # The counterpart of the plugin floor: `requireSignedVersion` is admitted in
    # `tauri.conf.json`, but a CLI that signs without a version field makes every
    # produced artifact end `MissingSignedVersion`. The pin is therefore load-bearing
    # trust, not build convenience, and a downgrade must fail here.
    cli_pin = package.get("devDependencies", {}).get("@tauri-apps/cli")
    resolved_cli_pin = cli_pin or "ABSENT"
    cli_parts = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", cli_pin or "")
    if cli_parts is None:
        failures.append(
            f"@tauri-apps/cli must be an exact x.y.z pin, got {cli_pin!r}"
        )
    elif tuple(int(part) for part in cli_parts.groups()) < MIN_TAURI_CLI_VERSION:
        failures.append(
            "@tauri-apps/cli must be at least "
            + ".".join(str(part) for part in MIN_TAURI_CLI_VERSION)
            + ": older CLIs sign updater artifacts without a version field,"
            " which makes the admitted requireSignedVersion posture unsatisfiable"
        )

    if package_lock.is_file():
        lock = json.loads(package_lock.read_text(encoding="utf-8"))
        root_package = lock.get("packages", {}).get("", {})
        if root_package.get("dependencies") != package.get("dependencies"):
            failures.append("package-lock runtime dependencies differ from package.json")
        if root_package.get("devDependencies") != package.get("devDependencies"):
            failures.append("package-lock dev dependencies differ from package.json")
        locked_cli = (
            lock.get("packages", {}).get("node_modules/@tauri-apps/cli", {}).get("version")
        )
        if locked_cli != cli_pin:
            failures.append(
                "package-lock must resolve @tauri-apps/cli to the manifest pin"
                f" {cli_pin!r}, got {locked_cli!r}"
            )

    if cargo_lock.is_file():
        cargo_text = cargo_lock.read_text(encoding="utf-8")
        if not cargo_text.startswith("# This file is automatically @generated by Cargo.\n"):
            failures.append("Cargo.lock missing generated-file header")
        if "\nversion = 4\n" not in cargo_text[:200]:
            failures.append("Cargo.lock must use lockfile version 4")
        if 'name = "rfd"' not in cargo_text or 'version = "0.17.2"' not in cargo_text:
            failures.append("Cargo.lock must contain exact rfd 0.17.2 resolution")
        resolved_updater = locked_version(cargo_text, "tauri-plugin-updater")
        if pin is not None and resolved_updater != resolved_plugin_pin:
            failures.append(
                f"Cargo.lock must resolve tauri-plugin-updater to the manifest pin {resolved_plugin_pin}, got {resolved_updater!r}"
            )

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
    print("RUNTIME_STATUS_ARGS=0")
    print("RUNTIME_STATUS_RAW_DECODER=STRICT")
    print("UPDATE_COMMAND_ARGS=0")
    print("UPDATE_RAW_DECODER=STRICT")
    print("GUEST_UPDATER_PERMISSIONS=0")
    print("UPDATER_TRUST_CONFIG=DELTA_001_FAIL_CLOSED")
    print(f"UPDATER_PLUGIN_PIN={resolved_plugin_pin}")
    print(f"TAURI_CLI_PIN={resolved_cli_pin}")
    print("INSTALL_RESTART_AUTHORITY=0")
    print("FILESYSTEM_MUTATION_PRIMITIVES=0")
    print("GENERIC_PROCESS_EXECUTION=0")
    print("FIXED_RUNTIME_SIDECAR_PROCESS=1")
    print("APPLE_SPECIFIC_FONT_REFERENCES=0")
    print("LOCKFILES=COMMITTED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
