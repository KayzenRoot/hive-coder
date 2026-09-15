#!/usr/bin/env python3
"""Emit one bounded Hive runtime presentation snapshot.

This diagnostic intentionally reports DISCONNECTED unless a future governed host
injects a trusted live observer. It performs no provider call, model execution,
permission mutation, task mutation, shell command or subprocess launch.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hive_runtime.runtime_status import disconnected_snapshot


def main() -> int:
    print(disconnected_snapshot().to_json())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
