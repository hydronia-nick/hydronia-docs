#!/usr/bin/env python3
"""Scan a built PDF for stretched / undersized images.

Pandoc silently drops some width attributes (notably values starting with
a bare dot, like ``.6cm``). When that happens the LaTeX template's Gin
defaults take over and can blow a 25x29-pixel toolbar icon up to the
full text width. This shows up in the PDF as a tiny source image rendered
at very low effective resolution (x-ppi).

This script wraps Poppler's ``pdfimages -list`` and flags any image whose
effective resolution is below a configurable threshold (default 40 ppi).
It can also render flagged pages to PNG so you can eyeball them.

Usage
-----
Fetch a fresh PDF from the live site and scan::

    python scripts/check_pdf_images.py \\
        --url https://hydronia-nick.github.io/hydronia-docs/pdf/tutorials-riverflow2d-en.pdf

Scan a local build::

    python scripts/build_pdfs.py --manual tutorials-riverflow2d-en --keep-build
    python scripts/check_pdf_images.py site/pdf/tutorials-riverflow2d-en.pdf

Render the flagged pages::

    python scripts/check_pdf_images.py site/pdf/tutorials-riverflow2d-en.pdf --render

Exit code is 0 if no images fall below the threshold, 1 otherwise -- safe
to wire into CI as a regression gate.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path


def _need(tool: str) -> str:
    path = shutil.which(tool)
    if not path:
        sys.exit(f"error: required tool '{tool}' not on PATH")
    return path


def _fetch_pdf(url: str, dest: Path) -> None:
    print(f"fetching {url}", file=sys.stderr)
    with urllib.request.urlopen(url) as resp, dest.open("wb") as out:
        shutil.copyfileobj(resp, out)


def _parse_images(pdf: Path) -> list[dict]:
    pdfimages = _need("pdfimages")
    out = subprocess.check_output([pdfimages, "-list", str(pdf)], text=True)
    lines = out.splitlines()
    # Header + separator on lines 0 and 1.
    records: list[dict] = []
    for line in lines[2:]:
        parts = line.split()
        if len(parts) < 14:
            continue
        try:
            records.append(
                {
                    "page": int(parts[0]),
                    "num": int(parts[1]),
                    "type": parts[2],
                    "width": int(parts[3]),
                    "height": int(parts[4]),
                    "xppi": int(parts[12]),
                    "yppi": int(parts[13]),
                }
            )
        except ValueError:
            continue
    return records


def _render_pages(pdf: Path, pages: list[int], out_dir: Path, dpi: int) -> list[Path]:
    pdftoppm = _need("pdftoppm")
    out_dir.mkdir(parents=True, exist_ok=True)
    rendered: list[Path] = []
    for page in sorted(set(pages)):
        prefix = out_dir / f"page-{page:04d}"
        subprocess.check_call(
            [pdftoppm, "-r", str(dpi), "-f", str(page), "-l", str(page),
             "-png", str(pdf), str(prefix)],
        )
        matches = sorted(out_dir.glob(f"page-{page:04d}*.png"))
        rendered.extend(matches)
    return rendered


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("pdf", nargs="?", help="Path to local PDF")
    ap.add_argument("--url", help="Download PDF from URL instead of reading local file")
    ap.add_argument(
        "--threshold", type=int, default=40,
        help="Flag images whose x-ppi falls below this (default: 40). Catches "
             "stretched icons rendered below natural DPI.",
    )
    ap.add_argument(
        "--max-width-in", type=float, default=6.5,
        help="Flag images whose rendered width exceeds this many inches "
             "(default: 6.5). Catches large screenshots rendered at natural "
             "DPI that overflow the text block. Text width on letter with "
             "the Hydronia template is 6.0in; 6.5in leaves a tolerance.",
    )
    ap.add_argument(
        "--max-height-in", type=float, default=9.0,
        help="Flag images whose rendered height exceeds this many inches "
             "(default: 9.0). Text height on letter is ~9.25in.",
    )
    ap.add_argument(
        "--render", action="store_true",
        help="Render flagged pages to PNGs next to the PDF",
    )
    ap.add_argument(
        "--render-dpi", type=int, default=100, help="DPI for page renders",
    )
    ap.add_argument(
        "--top", type=int, default=30, help="How many worst offenders to list",
    )
    args = ap.parse_args(argv)

    if not args.pdf and not args.url:
        ap.error("pass a PDF path or --url")

    with tempfile.TemporaryDirectory() as tmpdir:
        if args.url:
            pdf = Path(tmpdir) / "downloaded.pdf"
            _fetch_pdf(args.url, pdf)
        else:
            pdf = Path(args.pdf)
            if not pdf.is_file():
                sys.exit(f"error: no such file: {pdf}")

        records = _parse_images(pdf)
        for r in records:
            # Rendered size in inches. If xppi/yppi is 0 (rare pathological
            # cases), treat as infinitely stretched.
            r["rendered_w_in"] = (r["width"] / r["xppi"]) if r["xppi"] else float("inf")
            r["rendered_h_in"] = (r["height"] / r["yppi"]) if r["yppi"] else float("inf")

        low_ppi = [r for r in records if r["xppi"] < args.threshold]
        too_wide = [
            r for r in records
            if r["rendered_w_in"] > args.max_width_in
            or r["rendered_h_in"] > args.max_height_in
        ]
        # Union, preserving order: worst ppi first, then worst overflow
        seen = set()
        flagged: list[dict] = []
        for r in sorted(low_ppi, key=lambda r: (r["xppi"], r["page"])):
            key = (r["page"], r["num"])
            if key not in seen:
                seen.add(key)
                r["reason"] = "low-ppi"
                flagged.append(r)
        for r in sorted(too_wide, key=lambda r: (-r["rendered_w_in"], r["page"])):
            key = (r["page"], r["num"])
            if key not in seen:
                seen.add(key)
                r["reason"] = "overflow"
                flagged.append(r)

        print(f"total images : {len(records)}")
        print(f"ppi gate     : x-ppi < {args.threshold}                -> {len(low_ppi)} flagged")
        print(f"size gate    : rendered > {args.max_width_in}in x {args.max_height_in}in -> {len(too_wide)} flagged")
        print(f"total flagged: {len(flagged)}")
        if flagged:
            print()
            print(f"{'page':>5}  {'w':>5}  {'h':>5}  {'xppi':>5}  {'rend-in':>10}  reason")
            for r in flagged[: args.top]:
                rend = f"{r['rendered_w_in']:.1f}x{r['rendered_h_in']:.1f}"
                print(f"{r['page']:>5}  {r['width']:>5}  {r['height']:>5}  "
                      f"{r['xppi']:>5}  {rend:>10}  {r['reason']}")
            if len(flagged) > args.top:
                print(f"... and {len(flagged) - args.top} more")

        if args.render and flagged:
            out_dir = pdf.with_suffix("").parent / (pdf.stem + "_flagged_pages")
            pages = [r["page"] for r in flagged]
            rendered = _render_pages(pdf, pages, out_dir, args.render_dpi)
            print()
            print(f"rendered {len(rendered)} page(s) -> {out_dir}")

        return 1 if flagged else 0


if __name__ == "__main__":
    raise SystemExit(main())
