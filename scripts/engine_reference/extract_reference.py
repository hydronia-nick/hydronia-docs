#!/usr/bin/env python3
"""Render the reference PDF's pages for a single chapter to PNGs.

Uses the chapter page range from config.CHAPTERS + the front-matter offset
to translate printed page numbers to physical PDF pages, then pipes
pdftoppm to rasterize each one.

Usage:
    python extract_reference.py <N>
    python extract_reference.py 7              # ch 7 pages -> reference-pngs/07-mud-tailings/
    python extract_reference.py 7 --dpi 150    # higher DPI for closer inspection

Outputs: BUILD_ROOT/reference-pngs/NN-slug/pNNN.png where NNN is the
printed page number (not physical PDF page), padded to 3 digits.

This is idempotent — re-running overwrites existing PNGs. Useful when the
reference PDF gets rebuilt.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import config


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("num", type=int, help="Chapter number (1-18)")
    ap.add_argument("--dpi", type=int, default=100,
                    help="Render DPI (default 100; 150 for detail)")
    args = ap.parse_args()

    num, slug, printed_first, printed_last = config.lookup(args.num)
    offset = config.ref_pdf_pages_offset()
    pdf_first = printed_first + offset
    pdf_last = printed_last + offset

    if not config.REFERENCE_PDF.is_file():
        sys.exit(f"error: reference PDF not found: {config.REFERENCE_PDF}")

    out_dir = config.REFERENCE_PNGS / f"{num:02d}-{slug}"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Chapter {num} ({slug}): printed p{printed_first}-{printed_last} "
          f"-> PDF pages {pdf_first}-{pdf_last}")
    print(f"Rendering at {args.dpi} DPI to {out_dir}")

    # pdftoppm appends the physical page number (padded to match the PDF's
    # total-page-count digit width) as a suffix. E.g. for a 407-page PDF,
    # page 381 lands as "<prefix>-381.png". Rename each produced file to
    # p<printed>.png so diff_chapter can align by printed-page order.
    for printed in range(printed_first, printed_last + 1):
        physical = printed + offset
        out_prefix = out_dir / f"p{printed:03d}"
        subprocess.check_call([
            "pdftoppm", "-r", str(args.dpi),
            "-f", str(physical), "-l", str(physical),
            "-png", str(config.REFERENCE_PDF), str(out_prefix),
        ])
        target = out_prefix.with_suffix(".png")
        if not target.is_file():
            # Accept any suffix pdftoppm produced and rename it.
            candidates = list(out_dir.glob(f"p{printed:03d}-*.png"))
            if not candidates:
                sys.exit(f"error: pdftoppm produced no output for printed={printed}")
            # There should be exactly one since we asked for a single page.
            candidates[0].rename(target)

    count = len(list(out_dir.glob("p*.png")))
    print(f"ok: {count} page(s) rendered")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
