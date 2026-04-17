"""Generate the layered-triangle hero SVG for the Hydronia docs portal.

The Hydronia brand aesthetic uses overlapping translucent blue triangles
(see the 2020 brochure cover). This script reproduces that look
programmatically so the background can be regenerated, re-palleted, or
re-tuned without manual SVG editing.

Usage:
    python scripts/generate_hero_bg.py [--palette subdued|cool|velocity]
                                        [--out docs/assets/hero/mesh-hero.svg]
                                        [--seed 7]
                                        [--width 1920] [--height 800]
"""

from __future__ import annotations

import argparse
import math
import random
from dataclasses import dataclass
from pathlib import Path

# Three palette variants so we can show each and decide. Each palette is a
# list of (hex_color, alpha) tuples sampled when drawing each triangle.
PALETTES: dict[str, list[tuple[str, float]]] = {
    # Subdued professional — official Hydronia palette from marketing/BRAND.md.
    "subdued": [
        ("#0E367C", 0.18),  # secondary (dark blue)
        ("#014589", 0.18),  # primary
        ("#2c5fa0", 0.16),  # interpolated
        ("#5974B1", 0.14),  # tertiary (light blue)
        ("#8fa4ce", 0.12),  # lighter tertiary
        ("#b6c4e0", 0.10),
        ("#dbe3f0", 0.08),
        ("#eef2f9", 0.06),
    ],
    # Cool flow — water-coded, adds teal + cyan highlights.
    "cool": [
        ("#0b2545", 0.20),
        ("#143a5e", 0.18),
        ("#1f5e8a", 0.18),
        ("#2e7fa6", 0.16),
        ("#3fa7b7", 0.14),
        ("#6ecadd", 0.12),
        ("#a5dfeb", 0.10),
    ],
    # Velocity ramp — classic CFD palette, deep blue -> red.
    "velocity": [
        ("#0d1b4c", 0.20),
        ("#1a3a8e", 0.18),
        ("#2d75b6", 0.16),
        ("#4fa7c7", 0.14),
        ("#f3c969", 0.12),
        ("#e08040", 0.11),
        ("#c23b22", 0.10),
    ],
}


@dataclass(frozen=True)
class Triangle:
    pts: tuple[tuple[float, float], tuple[float, float], tuple[float, float]]
    fill: str
    alpha: float


def random_triangle(
    rng: random.Random,
    width: int,
    height: int,
    palette: list[tuple[str, float]],
    size_range: tuple[float, float],
    bias_left: float = 0.0,
) -> Triangle:
    """Generate one right-leaning triangle with a sampled palette color.

    bias_left pulls the centroid toward the left edge (the brochure style);
    0.0 = uniform over the canvas, 1.0 = strongly biased to the left third.
    """
    # Centroid placement — weighted toward left if requested.
    u = rng.random()
    u = u ** (1.0 + 2.5 * bias_left)  # skew toward 0 as bias_left grows
    cx = u * width
    cy = rng.random() * height

    size = rng.uniform(*size_range)
    # Mostly tall-ish isosceles / right-triangle vibes like the brochure.
    rotation = rng.uniform(0, 2 * math.pi)

    # Base triangle pointing up, then rotate.
    base = [
        (0.0, -size * 0.7),
        (-size * 0.5, size * 0.5),
        (size * 0.6, size * 0.4),
    ]
    cos_r, sin_r = math.cos(rotation), math.sin(rotation)
    pts = tuple(
        (cx + x * cos_r - y * sin_r, cy + x * sin_r + y * cos_r) for x, y in base
    )
    fill, alpha_base = rng.choice(palette)
    # Jitter alpha slightly so layering feels organic.
    alpha = max(0.04, min(0.9, alpha_base * rng.uniform(0.7, 1.3)))
    return Triangle(pts=pts, fill=fill, alpha=alpha)  # type: ignore[arg-type]


def build_svg(
    width: int,
    height: int,
    palette_name: str,
    seed: int,
) -> str:
    rng = random.Random(seed)
    palette = PALETTES[palette_name]

    # Two density layers: fewer large background triangles, more small accents.
    bg_layer = [
        random_triangle(
            rng, width, height, palette,
            size_range=(width * 0.25, width * 0.55),
            bias_left=0.55,
        )
        for _ in range(18)
    ]
    mid_layer = [
        random_triangle(
            rng, width, height, palette,
            size_range=(width * 0.08, width * 0.22),
            bias_left=0.35,
        )
        for _ in range(42)
    ]
    accent_layer = [
        random_triangle(
            rng, width, height, palette,
            size_range=(width * 0.02, width * 0.08),
            bias_left=0.20,
        )
        for _ in range(70)
    ]

    tris = bg_layer + mid_layer + accent_layer

    # Background gradient — very pale top-left to white bottom-right,
    # so triangles visually "fade off" to the right.
    gradient = """  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%"   stop-color="#eef3f9"/>
      <stop offset="60%"  stop-color="#ffffff"/>
      <stop offset="100%" stop-color="#ffffff"/>
    </linearGradient>
    <linearGradient id="fadeRight" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%"   stop-color="#ffffff" stop-opacity="0"/>
      <stop offset="70%"  stop-color="#ffffff" stop-opacity="0"/>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="1"/>
    </linearGradient>
  </defs>
"""

    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'preserveAspectRatio="xMinYMid slice" role="img" aria-hidden="true">',
        gradient,
        f'  <rect width="{width}" height="{height}" fill="url(#bgGrad)"/>',
    ]

    for t in tris:
        pts_str = " ".join(f"{x:.1f},{y:.1f}" for x, y in t.pts)
        parts.append(
            f'  <polygon points="{pts_str}" fill="{t.fill}" '
            f'fill-opacity="{t.alpha:.3f}" />'
        )

    # Right-side fade overlay so the triangles dissolve into clean whitespace
    # where text sits (right 30% of the hero).
    parts.append(
        f'  <rect width="{width}" height="{height}" fill="url(#fadeRight)"/>'
    )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--palette", choices=sorted(PALETTES), default="subdued")
    p.add_argument("--out", type=Path, default=Path("docs/assets/hero/mesh-hero.svg"))
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--width", type=int, default=1920)
    p.add_argument("--height", type=int, default=800)
    args = p.parse_args()

    svg = build_svg(args.width, args.height, args.palette, args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(svg, encoding="utf-8")
    print(f"Wrote {args.out} ({len(svg):,} bytes, palette={args.palette}, seed={args.seed})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
