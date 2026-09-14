from __future__ import annotations

import re
import subprocess
from typing import Sequence

from .errors import RuntimePreflightError


def reports_exact_version(output: str, expected: str) -> bool:
    pattern = rf"(?<![0-9A-Za-z.+-]){re.escape(expected)}(?![0-9A-Za-z.+-])"
    return re.search(pattern, output) is not None


def verify_binary_version(
    binary: str,
    expected: str,
    *,
    version_args: Sequence[str] = ("--version",),
    timeout: float = 5.0,
) -> str:
    try:
        result = subprocess.run(
            [binary, *version_args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="strict",
            timeout=timeout,
            check=False,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired, UnicodeError) as exc:
        raise RuntimePreflightError(f"foundation version probe failed: {type(exc).__name__}") from exc
    output = (result.stdout + "\n" + result.stderr).strip()
    if result.returncode != 0:
        raise RuntimePreflightError(f"foundation version probe exited with code {result.returncode}")
    if not reports_exact_version(output, expected):
        raise RuntimePreflightError(f"foundation version mismatch; expected {expected}")
    return output
