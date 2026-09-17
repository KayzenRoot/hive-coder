"""Deterministic product-version drift verifier for Hive Coder (HCODER-WO-0024).

Canonical source-of-truth law
-----------------------------
Exactly one canonical version source exists:
``apps/desktop/src-tauri/tauri.conf.json`` -> ``version``.
The Tauri application version identifies the shipped product artifact and is the
version a future updater compares against. The Rust package version and the npm
package version are *mirrors* and must equal it exactly.

This tool is deterministic, offline and non-mutating: it reads manifests, applies
strict SemVer parsing and reports drift. It never writes, downloads, installs,
signs or publishes anything.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
TAURI_CONFIG = ROOT / "apps" / "desktop" / "src-tauri" / "tauri.conf.json"
CARGO_MANIFEST = ROOT / "apps" / "desktop" / "src-tauri" / "Cargo.toml"
PACKAGE_MANIFEST = ROOT / "apps" / "desktop" / "package.json"

CANONICAL_SOURCE = "apps/desktop/src-tauri/tauri.conf.json"
VERSION_CONTRACT = "hive-version-v1"
VERIFIER_SCHEMA = "hive-version-drift-doctor-v1"
MAX_VERSION_CHARS = 128

# Official SemVer 2.0.0 pattern under the declared bounded profile: the SemVer
# grammar restricted to version strings of at most MAX_VERSION_CHARS characters.
# The bound is part of the shared law and is asserted identically by the product
# TypeScript parser, by this gate and by the shared vector file
# `apps/desktop/src/contracts/semverParityVectors.json`.
#
# Two properties are deliberate and load-bearing for cross-language parity:
#   * No anchors, and matching via `fullmatch`. `re.match` with a trailing `$`
#     accepts a final newline, so this gate would report LOCKED for a version the
#     product parser rejects.
#   * Explicit `[0-9]` digit classes instead of `\d`. Python's `\d` also matches
#     Unicode decimal digits, whereas JavaScript's `\d` (used by the product
#     parser) is ASCII-only, so `1.0.0-1٠` would be accepted here and rejected
#     there.
SEMVER_PATTERN = re.compile(
    r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-((?:0|[1-9][0-9]*|[0-9]*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9][0-9]*|[0-9]*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?"
)


def is_valid_version(value: object) -> bool:
    """Strict SemVer 2.0.0 acceptance under the bounded profile.

    A full-string match is required, so nothing — including a trailing newline,
    carriage return or Unicode line separator — may ride along. Malformed input
    fails closed. Acceptance must agree exactly with the product TypeScript
    parser; the shared vector file is the executable statement of that agreement.
    """
    if not isinstance(value, str) or not value or len(value) > MAX_VERSION_CHARS:
        return False
    return SEMVER_PATTERN.fullmatch(value) is not None


@dataclass(frozen=True)
class MirrorObservation:
    path: str
    version: str | None


@dataclass(frozen=True)
class DriftReport:
    schema: str
    status: str
    canonicalSource: str
    canonicalVersion: str | None
    mirrors: tuple[dict[str, object], ...]
    reason: str | None
    offendingPaths: tuple[str, ...]
    sideEffects: str = "NONE"

    def as_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": self.schema,
            "status": self.status,
            "contract": VERSION_CONTRACT,
            "canonicalSource": self.canonicalSource,
            "canonicalVersion": self.canonicalVersion,
            "mirrors": list(self.mirrors),
            "reason": self.reason,
            "offendingPaths": list(self.offendingPaths),
            "sideEffects": self.sideEffects,
        }


def evaluate_version_drift(canonical: str | None, mirrors: tuple[MirrorObservation, ...]) -> DriftReport:
    """Deterministic drift law over already-read manifest values.

    A mirror is correct only when it parses as strict SemVer *and* equals the
    canonical version exactly. Anything else is drift and fails closed.
    """
    observations = tuple(
        {"path": mirror.path, "version": mirror.version, "valid": is_valid_version(mirror.version)}
        for mirror in mirrors
    )

    def report(status: str, reason: str | None, offending: tuple[str, ...]) -> DriftReport:
        return DriftReport(
            schema=VERIFIER_SCHEMA,
            status=status,
            canonicalSource=CANONICAL_SOURCE,
            canonicalVersion=canonical,
            mirrors=observations,
            reason=reason,
            offendingPaths=offending,
        )

    if canonical is None:
        return report("INVALID", "missing_canonical_version", (CANONICAL_SOURCE,))
    if not is_valid_version(canonical):
        return report("INVALID", "malformed_canonical_version", (CANONICAL_SOURCE,))

    missing = tuple(m.path for m in mirrors if m.version is None)
    if missing:
        return report("DRIFT", "missing_mirror_version", missing)

    malformed = tuple(m.path for m in mirrors if not is_valid_version(m.version))
    if malformed:
        return report("DRIFT", "malformed_mirror_version", malformed)

    drifted = tuple(m.path for m in mirrors if m.version != canonical)
    if drifted:
        return report("DRIFT", "mirror_drift", drifted)

    return report("LOCKED", None, ())


def _read_json_version(path: Path) -> tuple[str | None, str | None]:
    """Return (version, error). Absence is reported as (None, None)."""
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        return None, f"unreadable:{type(exc).__name__}"
    except json.JSONDecodeError:
        return None, "invalid_json"
    if not isinstance(document, dict):
        return None, "invalid_json"
    value = document.get("version")
    return (value if isinstance(value, str) else None), None


def _read_cargo_version(path: Path) -> tuple[str | None, str | None]:
    try:
        document = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, None
    except OSError as exc:
        return None, f"unreadable:{type(exc).__name__}"
    except tomllib.TOMLDecodeError:
        return None, "invalid_toml"
    package = document.get("package")
    if not isinstance(package, dict):
        return None, "invalid_toml"
    value = package.get("version")
    return (value if isinstance(value, str) else None), None


def inspect() -> DriftReport:
    canonical_version, canonical_error = _read_json_version(TAURI_CONFIG)
    if canonical_error is not None:
        return DriftReport(
            schema=VERIFIER_SCHEMA,
            status="INVALID",
            canonicalSource=CANONICAL_SOURCE,
            canonicalVersion=None,
            mirrors=(),
            reason=canonical_error,
            offendingPaths=(CANONICAL_SOURCE,),
        )

    cargo_version, cargo_error = _read_cargo_version(CARGO_MANIFEST)
    package_version, package_error = _read_json_version(PACKAGE_MANIFEST)

    mirrors = (
        MirrorObservation(path="apps/desktop/src-tauri/Cargo.toml", version=cargo_version if cargo_error is None else "!"),
        MirrorObservation(path="apps/desktop/package.json", version=package_version if package_error is None else "!"),
    )
    return evaluate_version_drift(canonical_version, mirrors)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Hive Coder product-version drift verifier (read-only)")
    parser.add_argument("--json", action="store_true", help="Emit the full machine report")
    args = parser.parse_args(argv)

    report = inspect()
    if args.json:
        print(json.dumps(report.as_dict(), indent=2, sort_keys=True))
    else:
        print(f"VERSION_CONTRACT={VERSION_CONTRACT}")
        print(f"CANONICAL_VERSION_SOURCE={CANONICAL_SOURCE}")
        print(f"CANONICAL_VERSION={report.canonicalVersion}")
        for mirror in report.mirrors:
            print(f"MIRROR={mirror['path']}:{mirror['version']}")
        if report.reason is not None:
            print(f"REASON={report.reason}")
            print(f"OFFENDING={','.join(report.offendingPaths)}")
        print(f"VERSION_DRIFT={report.status}")
    return 0 if report.status == "LOCKED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
