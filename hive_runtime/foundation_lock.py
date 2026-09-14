from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .errors import RuntimePreflightError

DEFAULT_FOUNDATION_LOCK = Path(__file__).resolve().parents[1] / "foundations" / "foundations.lock.json"


def load_foundation_record(name: str, lock_path: Path = DEFAULT_FOUNDATION_LOCK) -> dict[str, Any]:
    try:
        document = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimePreflightError(f"cannot read foundation lock: {type(exc).__name__}") from exc
    if document.get("schemaVersion") != "hive-foundations-lock-v1":
        raise RuntimePreflightError("unsupported foundation lock schema")
    foundations = document.get("foundations")
    if not isinstance(foundations, dict):
        raise RuntimePreflightError("foundation lock missing foundations object")
    record = foundations.get(name)
    if not isinstance(record, dict):
        raise RuntimePreflightError(f"foundation lock missing record: {name}")
    discovery = record.get("discovery")
    if not isinstance(discovery, dict) or not isinstance(discovery.get("expectedVersion"), str):
        raise RuntimePreflightError(f"foundation record missing expectedVersion: {name}")
    return record


def expected_foundation_version(name: str, lock_path: Path = DEFAULT_FOUNDATION_LOCK) -> str:
    return load_foundation_record(name, lock_path)["discovery"]["expectedVersion"]
