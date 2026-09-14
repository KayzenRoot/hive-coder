from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.foundations.verify_lock import DEFAULT_LOCK, load_lock, validate_lock


def _locate(discovery: dict[str, Any]) -> str | None:
    override = os.environ.get(discovery["env"])
    if override:
        candidate = Path(override).expanduser()
        return str(candidate) if candidate.is_file() else None
    for name in discovery["executables"]:
        found = shutil.which(name)
        if found:
            return found
    return None


def _reports_exact_version(output: str, expected: str) -> bool:
    pattern = rf"(?<![0-9A-Za-z.+-]){re.escape(expected)}(?![0-9A-Za-z.+-])"
    return re.search(pattern, output) is not None


def _probe(path: str, discovery: dict[str, Any]) -> dict[str, Any]:
    expected = str(discovery["expectedVersion"])
    try:
        result = subprocess.run(
            [path, *discovery.get("versionArgs", ["--version"])],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status": "PROBE_FAILED", "error": type(exc).__name__}
    output = (result.stdout + "\n" + result.stderr).strip()
    if result.returncode != 0:
        return {"status": "PROBE_FAILED", "exitCode": result.returncode, "output": output[:500]}
    return {
        "status": "READY" if _reports_exact_version(output, expected) else "VERSION_MISMATCH",
        "expectedVersion": expected,
        "reported": output[:500],
    }


def inspect(lock: dict[str, Any], inventory_only: bool = False) -> dict[str, Any]:
    errors = validate_lock(lock)
    if errors:
        return {"schemaVersion": "hive-foundation-doctor-v1", "status": "INVALID_LOCK", "errors": errors, "sideEffects": "NONE"}
    results: dict[str, Any] = {}
    for name, item in lock["foundations"].items():
        if inventory_only:
            results[name] = {"status": "LOCKED", "release": item["release"], "commit": item["commit"], "license": item["license"]}
            continue
        path = _locate(item["discovery"])
        results[name] = {"status": "MISSING"} if path is None else _probe(path, item["discovery"])
    statuses = {item["status"] for item in results.values()}
    overall = "LOCKED" if inventory_only else ("READY" if statuses == {"READY"} else "NOT_READY")
    return {"schemaVersion": "hive-foundation-doctor-v1", "status": overall, "foundations": results, "sideEffects": "NONE"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Hive Coder non-invasive foundation doctor")
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    parser.add_argument("--inventory-only", action="store_true")
    args = parser.parse_args()
    report = inspect(load_lock(args.lock), inventory_only=args.inventory_only)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] in {"READY", "LOCKED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
