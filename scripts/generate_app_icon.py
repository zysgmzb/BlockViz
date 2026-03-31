"""Generate BlockViz icon assets from a tiny built-in raster."""

from __future__ import annotations

import math
import struct
import zlib
from pathlib import Path

SIZE = 256
ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
PNG_PATH = ASSETS / "blockviz.png"
ICO_PATH = ASSETS / "blockviz.ico"


def _clamp(value: float) -> int:
    return max(0, min(255, int(round(value))))


def _blend(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return (
        _clamp(a[0] + (b[0] - a[0]) * t),
        _clamp(a[1] + (b[1] - a[1]) * t),
        _clamp(a[2] + (b[2] - a[2]) * t),
    )


def _chunk(kind: bytes, payload: bytes) -> bytes:
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)


def build_rgba_pixels() -> bytes:
    rows = bytearray()
    background_a = (11, 18, 38)
    background_b = (49, 46, 129)
    accent_a = (139, 92, 246)
    accent_b = (34, 211, 238)
    diamond_outer = 72
    diamond_inner = 50
    center = SIZE / 2

    for y in range(SIZE):
        rows.append(0)
        for x in range(SIZE):
            dx = x - center
            dy = y - center
            radial = min(1.0, math.sqrt((dx * dx) + (dy * dy)) / (SIZE * 0.72))
            base = _blend(background_b, background_a, radial)

            glow_x = (x - SIZE * 0.26) / SIZE
            glow_y = (y - SIZE * 0.24) / SIZE
            glow = max(0.0, 1.0 - math.sqrt(glow_x * glow_x + glow_y * glow_y) * 2.4)
            glow_color = _blend(accent_b, accent_a, 0.35)
            base = (
                _clamp(base[0] + glow_color[0] * glow * 0.28),
                _clamp(base[1] + glow_color[1] * glow * 0.28),
                _clamp(base[2] + glow_color[2] * glow * 0.28),
            )

            manhattan = abs(dx) + abs(dy)
            if manhattan <= diamond_outer:
                edge_t = min(1.0, manhattan / diamond_outer)
                outer = _blend(accent_a, accent_b, (dx + dy + SIZE) / (SIZE * 1.6))
                rim = _blend((255, 255, 255), outer, min(1.0, edge_t * 1.25))
                color = rim
                if manhattan <= diamond_inner:
                    inner_t = min(1.0, manhattan / diamond_inner)
                    fill = _blend((245, 247, 255), outer, inner_t * 0.72)
                    color = fill
                rows.extend((color[0], color[1], color[2], 255))
            else:
                rows.extend((base[0], base[1], base[2], 255))
    return bytes(rows)


def build_png() -> bytes:
    pixels = build_rgba_pixels()
    ihdr = struct.pack(">IIBBBBB", SIZE, SIZE, 8, 6, 0, 0, 0)
    compressed = zlib.compress(pixels, level=9)
    return b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", compressed) + _chunk(b"IEND", b"")


def build_ico(png_bytes: bytes) -> bytes:
    header = struct.pack("<HHH", 0, 1, 1)
    width = 0
    height = 0
    directory = struct.pack("<BBBBHHII", width, height, 0, 0, 1, 32, len(png_bytes), 22)
    return header + directory + png_bytes


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    png_bytes = build_png()
    PNG_PATH.write_bytes(png_bytes)
    ICO_PATH.write_bytes(build_ico(png_bytes))
    print(f"wrote {PNG_PATH}")
    print(f"wrote {ICO_PATH}")


if __name__ == "__main__":
    main()
