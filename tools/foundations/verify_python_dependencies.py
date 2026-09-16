from __future__ import annotations

"""Verify the governed Python runtime dependency lock for Hive Coder.

This is a non-mutating, deterministic check. It never installs anything. It
fails closed when a locked dependency is absent, at the wrong version, or
installed from a platform (native-extension) artifact, or when the CI-consumed
requirements file does not match the admitted artifacts exactly.

Runtime import isolation (no network/credential/client module reachable from the
admitted codec surface) is proven by the focused WO-0023 tests rather than here,
because an unrelated interpreter may legitimately already have those modules
installed for other reasons. This verifier records that fact without gating on it.
"""

import argparse
import importlib.util
import json
import re
import sys
from importlib.metadata import PackageNotFoundError, distribution
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DEFAULT_LOCK = ROOT / "foundations" / "python-dependencies.lock.json"
SCHEMA = "hive-python-dependencies-lock-v1"
VERIFIER_SCHEMA = "hive-python-dependency-doctor-v1"
PURE_WHEEL_TAG = "py3-none-any"
_REQUIREMENT = re.compile(r"^(?P<name>[A-Za-z0-9._-]+)\s*@\s*(?P<url>\S+)\s+--hash=sha256:(?P<sha256>[0-9a-f]{64})$")


def load_lock(path: Path = DEFAULT_LOCK) -> dict[str, Any]:
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    if document.get("schemaVersion") != SCHEMA:
        raise ValueError("unsupported python dependency lock schema")
    dependencies = document.get("dependencies")
    if not isinstance(dependencies, dict):
        raise ValueError("python dependency lock missing dependencies object")
    return document


def _installed_wheel_tag(name: str) -> str | None:
    """Return the wheel Tag of the installed distribution, or None if unprovable."""
    try:
        dist = distribution(name)
    except PackageNotFoundError:
        return None
    wheel = dist._path / "WHEEL"  # type: ignore[attr-defined]
    try:
        text = wheel.read_text(encoding="utf-8")
    except OSError:
        return None
    for line in text.splitlines():
        if line.lower().startswith("tag:"):
            return line.split(":", 1)[1].strip()
    return None


def admitted_artifacts(lock: dict[str, Any]) -> dict[str, dict[str, str]]:
    admitted: dict[str, dict[str, str]] = {}
    for name, spec in lock["dependencies"].items():
        for key, artifact in (spec.get("artifacts") or {}).items():
            if isinstance(artifact, dict) and artifact.get("admitted") is True:
                admitted[f"{name}:{key}"] = {
                    "name": name,
                    "url": artifact["url"],
                    "sha256": artifact["sha256"],
                    "filename": artifact["filename"],
                }
    return admitted


def check_requirements_file(lock: dict[str, Any]) -> dict[str, Any]:
    """The CI-consumed pin file must name exactly the admitted artifacts."""
    relative = lock.get("policy", {}).get("requirementsFile")
    if not relative:
        return {"status": "UNDECLARED"}
    path = ROOT / relative
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return {"status": "MISSING", "path": relative, "error": type(exc).__name__}

    admitted = admitted_artifacts(lock)
    pinned: list[dict[str, str]] = []
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = _REQUIREMENT.match(line)
        if match is None:
            return {"status": "UNPARSEABLE_PIN", "path": relative, "line": line}
        pinned.append({"name": match["name"], "url": match["url"], "sha256": match["sha256"]})

    matches = {key for key, art in admitted.items() if any(p["url"] == art["url"] and p["sha256"] == art["sha256"] for p in pinned)}
    if len(pinned) != len(admitted) or len(matches) != len(admitted):
        return {
            "status": "ADMITTED_SET_MISMATCH",
            "path": relative,
            "admitted": sorted(admitted),
            "pinned": sorted(p["name"] for p in pinned),
        }
    return {"status": "MATCHES_ADMITTED", "path": relative, "pinnedCount": len(pinned)}


def _check_dependency(name: str, spec: dict[str, Any]) -> dict[str, Any]:
    record: dict[str, Any] = {"expectedVersion": spec["version"]}
    try:
        dist = distribution(name)
    except PackageNotFoundError:
        record["status"] = "MISSING"
        record["reason"] = (
            "governed dependency is not materialized; install with "
            "`python -m pip install --no-deps --require-hashes -r "
            "foundations/python-dependencies.requirements.txt`"
        )
        return record

    record["installedVersion"] = dist.version
    if dist.version != spec["version"]:
        record["status"] = "VERSION_MISMATCH"
        return record

    if not spec.get("nativeExtensionRequiredForCorrectness", True):
        tag = _installed_wheel_tag(name)
        record["installedWheelTag"] = tag
        if tag is None:
            record["status"] = "ARTIFACT_UNPROVEN"
            record["reason"] = "cannot prove the installed artifact is the admitted pure-Python wheel"
            return record
        if tag != PURE_WHEEL_TAG:
            record["status"] = "NATIVE_ARTIFACT_NOT_ADMITTED"
            record["reason"] = (
                f"installed artifact tag {tag!r} is not {PURE_WHEEL_TAG!r}; a platform wheel would make "
                "correctness depend on the optional compiled extension"
            )
            return record

    record["status"] = "READY"
    return record


def inspect(lock: dict[str, Any]) -> dict[str, Any]:
    results = {name: _check_dependency(name, spec) for name, spec in lock["dependencies"].items()}
    requirements = check_requirements_file(lock)

    environment_note: dict[str, Any] = {}
    for name, spec in lock["dependencies"].items():
        for item in spec.get("unmaterializedDeclaredRequires", []) or []:
            module = item["name"].replace("-", "_")
            present = importlib.util.find_spec(module) is not None
            environment_note[item["name"]] = {
                "declared": item["declared"],
                "installedInThisInterpreter": present,
                "gated": False,
                "note": (
                    "Recorded only. Import isolation of the admitted codec surface is proven by the "
                    "focused WO-0023 tests, not by global interpreter state."
                ),
            }

    statuses = {record["status"] for record in results.values()}
    if "MISSING" in statuses:
        overall = "NOT_MATERIALIZED"
    elif statuses != {"READY"} or requirements.get("status") != "MATCHES_ADMITTED":
        overall = "MISMATCH"
    else:
        overall = "LOCKED"

    return {
        "schemaVersion": VERIFIER_SCHEMA,
        "status": overall,
        "pythonRequires": lock.get("python", {}).get("requires"),
        "dependencies": results,
        "requirementsFile": requirements,
        "environmentNote": environment_note,
        "sideEffects": "NONE",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Hive Coder governed Python dependency verifier (non-installing)")
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    parser.add_argument("--inventory-only", action="store_true", help="Validate the lock document only, without checking the interpreter")
    args = parser.parse_args(argv)

    try:
        lock = load_lock(args.lock)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"schemaVersion": VERIFIER_SCHEMA, "status": "INVALID_LOCK", "error": type(exc).__name__, "sideEffects": "NONE"}, indent=2, sort_keys=True))
        return 1

    if args.inventory_only:
        print(json.dumps({
            "schemaVersion": VERIFIER_SCHEMA,
            "status": "LOCKED",
            "dependencies": {name: {"status": "LOCKED", "version": spec["version"]} for name, spec in lock["dependencies"].items()},
            "requirementsFile": check_requirements_file(lock),
            "sideEffects": "NONE",
        }, indent=2, sort_keys=True))
        return 0

    report = inspect(lock)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "LOCKED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
