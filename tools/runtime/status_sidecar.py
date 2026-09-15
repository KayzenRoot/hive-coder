#!/usr/bin/env python3
"""Single-purpose Hive runtime-status sidecar.

Serves exactly one bounded, canonical, non-authoritative status request over
stdio and exits. It has no provider/model/permission/task mutation path and no
generic command mode.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hive_runtime.runtime_status import disconnected_snapshot
from hive_runtime.runtime_status_protocol import serve_one

MODE = "--stdio-status-v1"
EXIT_USAGE = 64
EXIT_PROTOCOL = 65


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args != [MODE]:
        return EXIT_USAGE

    try:
        snapshot = disconnected_snapshot()
        serve_one(sys.stdin, sys.stdout, snapshot)
    except (ValueError, OSError, UnicodeError):
        return EXIT_PROTOCOL
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
