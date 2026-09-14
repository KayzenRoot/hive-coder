from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LOCK = ROOT / "foundations" / "foundations.lock.json"
_ALLOWED_LICENSES = {"Apache-2.0", "MIT"}
_REQUIRED = {"openInterpreter", "cuaDriver"}


def load_lock(path: Path = DEFAULT_LOCK) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_lock(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("schemaVersion") != "hive-foundations-lock-v1":
        errors.append("unsupported schemaVersion")
    foundations = data.get("foundations")
    if not isinstance(foundations, dict):
        return errors + ["foundations must be an object"]
    missing = _REQUIRED - foundations.keys()
    if missing:
        errors.append(f"missing foundations: {sorted(missing)}")
    for key in _REQUIRED & foundations.keys():
        item = foundations[key]
        if item.get("license") not in _ALLOWED_LICENSES:
            errors.append(f"{key}: unapproved license {item.get('license')!r}")
        commit = item.get("commit", "")
        if len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
            errors.append(f"{key}: commit must be a lowercase 40-char git SHA")
        discovery = item.get("discovery", {})
        if not discovery.get("expectedVersion") or not discovery.get("executables"):
            errors.append(f"{key}: incomplete discovery contract")
        for platform, artifact in item.get("artifacts", {}).items():
            digest = artifact.get("sha256", "")
            if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
                errors.append(f"{key}/{platform}: invalid sha256")
            if not str(artifact.get("url", "")).startswith("https://github.com/"):
                errors.append(f"{key}/{platform}: artifact URL must be GitHub HTTPS")
    policy = data.get("policy", {})
    if policy.get("autoInstall") is not False:
        errors.append("autoInstall must remain false")
    if policy.get("vendorBinaries") is not False:
        errors.append("vendorBinaries must remain false")
    if policy.get("failOnUnknownVersion") is not True:
        errors.append("failOnUnknownVersion must remain true")
    return errors


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    errors = validate_lock(load_lock())
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("FOUNDATIONS_LOCK_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
