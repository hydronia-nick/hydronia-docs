#!/usr/bin/env python3
"""Render the new standalone chapter PDF to PNGs and produce an HTML
side-by-side comparison against the reference PNGs.

Prerequisites (run these first for the target chapter):
    python build_chapter.py <N>
    python extract_reference.py <N>

Then:
    python diff_chapter.py <N>             -> diff/NN-slug.html + chapter-pngs/NN-slug/
    python diff_chapter.py <N> --dpi 150   -> match DPI you used for extract_reference

Opens the report automatically with --open. The HTML file is standalone
(uses file:// paths); you can share it or keep it for reference.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import webbrowser
from pathlib import Path

import config


HTML_HEAD = """<!doctype html>
<html><head><meta charset='utf-8'>
<title>Engine Reference - Chapter {num} diff</title>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 0; padding: 1rem;
         background: #1a1a1a; color: #eee; }}
  h1 {{ margin-top: 0; }}
  .summary {{ background: #2a2a2a; padding: 1rem; border-radius: 6px;
              margin-bottom: 1rem; }}
  .row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;
          margin-bottom: 1rem; padding: 0.5rem;
          background: #222; border-radius: 4px; }}
  .row h3 {{ margin: 0 0 0.5rem 0; font-size: 0.9rem; color: #aaa; }}
  .page {{ background: white; padding: 2px; border-radius: 3px; }}
  .page img {{ width: 100%; display: block; }}
  .missing {{ padding: 2rem; text-align: center; color: #888;
              background: #2a2a2a; border-radius: 3px; }}
  .controls {{ position: sticky; top: 0; background: #1a1a1a; padding: 0.5rem 0;
               border-bottom: 1px solid #333; margin-bottom: 1rem; }}
  .controls label {{ margin-right: 1rem; }}
</style>
<script>
function setZoom(z) {{
  document.querySelectorAll('.page img').forEach(i => i.style.width = z + '%');
}}
</script>
</head><body>
<h1>Chapter {num}: {slug}</h1>
<div class='summary'>
  Reference pages {ref_first}..{ref_last} (printed) in full manual<br>
  New chapter build: {new_pdf}<br>
  Reference pages: {ref_count} | New pages: {new_count}
</div>
<div class='controls'>
  <label>Zoom:
    <input type='range' min='25' max='200' value='100'
           oninput='setZoom(this.value)'>
  </label>
</div>
"""

HTML_ROW = """<div class='row'>
  <div><h3>Reference (printed p{printed})</h3>
    {ref_img}
  </div>
  <div><h3>New build (page {new_idx})</h3>
    {new_img}
  </div>
</div>
"""

HTML_TAIL = "</body></html>\n"


def render_chapter_pdf_to_pngs(pdf: Path, out_dir: Path, dpi: int) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    # Clear stale PNGs so stale-file mismatches don't confuse the report
    for old in out_dir.glob("p*.png"):
        old.unlink()
    prefix = out_dir / "p"
    subprocess.check_call([
        "pdftoppm", "-r", str(dpi), "-png",
        str(pdf), str(prefix),
    ])
    pngs = sorted(out_dir.glob("p*.png"))
    return pngs


def img_tag(p: Path | None) -> str:
    if p is None or not p.is_file():
        return "<div class='missing'>(no page)</div>"
    uri = p.as_uri()
    return f"<div class='page'><img src='{uri}' loading='lazy'></div>"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("num", type=int)
    ap.add_argument("--dpi", type=int, default=100)
    ap.add_argument("--open", action="store_true",
                    help="Open the HTML report in the default browser")
    args = ap.parse_args()

    num, slug, ref_first, ref_last = config.lookup(args.num)

    new_pdf = config.CHAPTER_PDFS / f"{num:02d}-{slug}.pdf"
    if not new_pdf.is_file():
        sys.exit(f"error: run build_chapter.py {num} first (missing {new_pdf})")

    ref_dir = config.REFERENCE_PNGS / f"{num:02d}-{slug}"
    if not ref_dir.is_dir() or not list(ref_dir.glob("p*.png")):
        sys.exit(f"error: run extract_reference.py {num} first (missing {ref_dir})")

    new_dir = config.CHAPTER_PNGS / f"{num:02d}-{slug}"
    print(f"Rendering {new_pdf.name} -> {new_dir}")
    new_pngs = render_chapter_pdf_to_pngs(new_pdf, new_dir, args.dpi)
    print(f"  {len(new_pngs)} page(s)")

    # Pair pages by index. Reference pages are named p<printed>.png.
    ref_pngs_sorted = sorted(ref_dir.glob("p*.png"))

    # Align: reference pages start at printed page ref_first.
    # New build pages start at index 1 (though some templates might inject
    # an empty leader page — we just align by position in the list).
    rows = []
    max_pairs = max(len(ref_pngs_sorted), len(new_pngs))
    for i in range(max_pairs):
        ref_png = ref_pngs_sorted[i] if i < len(ref_pngs_sorted) else None
        new_png = new_pngs[i] if i < len(new_pngs) else None
        printed = ref_first + i if ref_png is not None else "—"
        rows.append(HTML_ROW.format(
            printed=printed,
            new_idx=i + 1 if new_png is not None else "—",
            ref_img=img_tag(ref_png),
            new_img=img_tag(new_png),
        ))

    config.DIFF_REPORTS.mkdir(parents=True, exist_ok=True)
    out_html = config.DIFF_REPORTS / f"{num:02d}-{slug}.html"
    out_html.write_text(
        HTML_HEAD.format(num=num, slug=slug,
                          ref_first=ref_first, ref_last=ref_last,
                          new_pdf=new_pdf.as_uri(),
                          ref_count=len(ref_pngs_sorted),
                          new_count=len(new_pngs))
        + "".join(rows)
        + HTML_TAIL,
        encoding="utf-8",
    )

    print(f"ok: {out_html}")
    if args.open:
        webbrowser.open(out_html.as_uri())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
