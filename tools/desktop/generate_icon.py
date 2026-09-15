from __future__ import annotations

import math
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "apps" / "desktop" / "src-tauri" / "icons" / "icon.ico"
SIZE = 64


def _inside_polygon(x: float, y: float, points: list[tuple[float, float]]) -> bool:
    inside = False
    j = len(points) - 1
    for i, (xi, yi) in enumerate(points):
        xj, yj = points[j]
        crosses = (yi > y) != (yj > y)
        if crosses:
            boundary_x = (xj - xi) * (y - yi) / (yj - yi) + xi
            if x < boundary_x:
                inside = not inside
        j = i
    return inside


def _hexagon(radius: float) -> list[tuple[float, float]]:
    cx = cy = SIZE / 2
    return [
        (
            cx + radius * math.cos(math.radians(-90 + 60 * index)),
            cy + radius * math.sin(math.radians(-90 + 60 * index)),
        )
        for index in range(6)
    ]


def _pixel_rgba(x: int, y: int) -> tuple[int, int, int, int]:
    dark = (11, 13, 18, 255)
    panel = (22, 27, 32, 255)
    lime = (184, 255, 90, 255)
    lime_soft = (218, 255, 159, 255)

    outer = _inside_polygon(x + 0.5, y + 0.5, _hexagon(27.0))
    inner = _inside_polygon(x + 0.5, y + 0.5, _hexagon(23.5))
    color = lime if outer and not inner else panel if inner else dark

    left_bar = 21 <= x <= 25 and 18 <= y <= 46
    right_bar = 39 <= x <= 43 and 18 <= y <= 46
    cross_bar = 21 <= x <= 43 and 30 <= y <= 34
    if left_bar or right_bar or cross_bar:
        color = lime_soft

    dx = x - 32
    dy = y - 32
    if dx * dx + dy * dy <= 7:
        color = lime
    return color


def build_icon() -> bytes:
    xor_rows: list[bytes] = []
    for y in range(SIZE - 1, -1, -1):
        row = bytearray()
        for x in range(SIZE):
            red, green, blue, alpha = _pixel_rgba(x, y)
            row.extend((blue, green, red, alpha))
        xor_rows.append(bytes(row))
    xor_bitmap = b"".join(xor_rows)

    and_stride = ((SIZE + 31) // 32) * 4
    and_bitmap = b"\x00" * (and_stride * SIZE)

    bitmap_info = struct.pack(
        "<IIIHHIIIIII",
        40,
        SIZE,
        SIZE * 2,
        1,
        32,
        0,
        len(xor_bitmap),
        0,
        0,
        0,
        0,
    )
    image_data = bitmap_info + xor_bitmap + and_bitmap

    icon_dir = struct.pack("<HHH", 0, 1, 1)
    icon_entry = struct.pack(
        "<BBBBHHII",
        SIZE,
        SIZE,
        0,
        0,
        1,
        32,
        len(image_data),
        6 + 16,
    )
    return icon_dir + icon_entry + image_data


def main() -> int:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    payload = build_icon()
    OUTPUT.write_bytes(payload)
    if len(payload) < 1024:
        raise RuntimeError("generated icon is unexpectedly small")
    print(f"HIVE_DESKTOP_ICON={OUTPUT.relative_to(ROOT)}")
    print(f"HIVE_DESKTOP_ICON_BYTES={len(payload)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
