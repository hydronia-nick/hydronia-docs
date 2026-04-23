#!/usr/bin/env python3
"""Extract one inline chapter from the Engine Reference main .tex into
chapters/NN-slug.tex, replacing the inline content with \\input{chapters/NN-slug.tex}.

Runs one chapter at a time so each extraction is individually buildable /
revertable. Usage:

    python extract_chapter.py <N> <slug> <start_line> <end_line>

Example:

    python extract_chapter.py 1 introduction 526 859

Line numbers are 1-based, matching the numbers `grep -n` or an editor shows.
`end_line` is exclusive — it's the line number of the *next* chapter's
opening (or of the next `\\input{}` that follows this chapter's content).

Contract with iftoggle-wrapped chapters: if the chapter is introduced by
a `\\iftoggle{...}{...}{...}` block that wraps different titles per flavor
(e.g. Ch 5's Hydrodynamic-vs-Overland-Viscous-Flow titles), pass the
start_line as the line containing the opening `\\iftoggle{...}%`. That
block is lifted verbatim into the new chapter file, preserving flavor
branching.

Side effect: edits the main .tex in place. Make a .original backup before
running the series.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SOURCE_DIR = Path(r"E:\Hydronia Dropbox\Nick Calero\Manuals\ENGINE_REFERENCE_MANUAL")
MAIN_TEX = SOURCE_DIR / "Rf2D_ReferenceManual_QGIS_2024.tex"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("num", type=int, help="Chapter number (1-18)")
    ap.add_argument("slug", type=str, help="Kebab-case slug, e.g. 'introduction'")
    ap.add_argument("start_line", type=int, help="1-based start line (inclusive)")
    ap.add_argument("end_line", type=int, help="1-based end line (exclusive)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print what would happen without writing anything")
    args = ap.parse_args()

    lines = MAIN_TEX.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    if args.start_line < 1 or args.end_line > len(lines) + 1 or args.start_line >= args.end_line:
        sys.exit(f"error: bad range {args.start_line}..{args.end_line} "
                 f"against {len(lines)} lines")

    # 1-based inclusive start → 0-based index
    s = args.start_line - 1
    e = args.end_line - 1  # exclusive end is same as 0-based non-inclusive

    extracted = lines[s:e]
    head_preview = "".join(extracted[:3]).rstrip()

    chapters_dir = SOURCE_DIR / "chapters"
    dst = chapters_dir / f"{args.num:02d}-{args.slug}.tex"

    # Build the replacement line. Keep the trailing newline consistent with the
    # rest of main.tex.
    replacement = f"\\input{{chapters/{args.num:02d}-{args.slug}.tex}}\n"

    print(f"Source : {MAIN_TEX}")
    print(f"Range  : lines {args.start_line}..{args.end_line - 1} "
          f"({e - s} lines)")
    print(f"Head   : {head_preview!r}")
    print(f"Target : {dst}")
    print(f"Replace with: {replacement.rstrip()}")

    if args.dry_run:
        print("(dry-run — no files written)")
        return 0

    if dst.exists():
        sys.exit(f"error: {dst} already exists, refusing to overwrite")

    # Write extracted content
    dst.write_text("".join(extracted), encoding="utf-8")

    # Splice the replacement into the main tex
    new_lines = lines[:s] + [replacement] + lines[e:]
    MAIN_TEX.write_text("".join(new_lines), encoding="utf-8")

    print(f"wrote {len(extracted)} lines to {dst.name}")
    print(f"main.tex: {len(lines)} -> {len(new_lines)} lines")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
