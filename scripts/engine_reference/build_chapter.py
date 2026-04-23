#!/usr/bin/env python3
"""Build a standalone PDF for one chapter of the Engine Reference Manual.

Copies the preamble from the main .tex (so the chapter renders with the
same packages/fonts/colors as the full manual), then emits a minimal
driver that jumps straight to that one chapter's \\input{} and exits. No
title page, no legal page, no TOC, no LoF/LoT — those would waste build
time when iterating on a single chapter.

Chapter numbering is set to match the reference PDF via
\\setcounter{chapter}{N-1}. That keeps figure/table/section labels
(e.g. "Figure 2.3") stable so they can be diffed against the reference.

Usage:
    python build_chapter.py <N>
    python build_chapter.py 7           # builds ch 7 (mud-tailings)

Output lands at BUILD_ROOT/chapter-pdfs/NN-slug.pdf.

Runs pdflatex -> bibtex -> pdflatex -> pdflatex so citations resolve. A
chapter with zero \\cite's still needs the bibtex step to be harmless;
it is.

Build artifacts (aux, log, bbl, etc.) land in BUILD_ROOT/_work/<N>/ and
stay there so you can inspect failed builds. They're gitignored.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import config


def read_preamble(main_tex: Path) -> str:
    """Return everything in main.tex from the top up to (but not including)
    the line containing `\\begin{document}`."""
    text = main_tex.read_text(encoding="utf-8", errors="replace")
    marker = chr(0x5c) + "begin{document}"
    idx = text.find(marker)
    if idx < 0:
        sys.exit(f"error: no {marker} in {main_tex}")
    return text[:idx]


def build_driver_tex(num: int, slug: str) -> str:
    """Assemble the single-chapter driver .tex content."""
    preamble = read_preamble(config.MAIN_TEX)
    chapter_input = f"chapters/{num:02d}-{slug}.tex"

    return f"""{preamble}\\begin{{document}}

% Single-chapter build: skip title / legal / TOC / LoF / LoT pages.
% Match the reference PDF's chapter numbering by seeding the counter.
\\pagestyle{{empty}}
\\setcounter{{chapter}}{{{num - 1}}}
\\pagenumbering{{arabic}}
\\setcounter{{page}}{{1}}

\\input{{{chapter_input}}}

\\bibliographystyle{{agsm}}
\\bibliography{{biblio}}

\\end{{document}}
"""


def run(cmd: list[str], cwd: Path, log: Path) -> int:
    with log.open("ab") as fh:
        fh.write(f"\n=== {' '.join(cmd)} ===\n".encode())
        p = subprocess.Popen(cmd, cwd=str(cwd), stdout=fh, stderr=subprocess.STDOUT)
        p.wait()
        return p.returncode


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("num", type=int, help="Chapter number (1-18)")
    ap.add_argument("--keep-driver", action="store_true",
                    help="Leave the generated driver.tex next to the source")
    args = ap.parse_args()

    num, slug, ref_start, ref_end = config.lookup(args.num)
    chapter_file = config.CHAPTERS_DIR / f"{num:02d}-{slug}.tex"
    if not chapter_file.is_file():
        sys.exit(f"error: chapter file not found: {chapter_file}")

    driver_name = f"_ch{num:02d}_{slug}_driver"
    driver_tex = config.SRC_DIR / f"{driver_name}.tex"

    config.CHAPTER_PDFS.mkdir(parents=True, exist_ok=True)
    work_dir = config.BUILD_ROOT / "_work" / f"{num:02d}-{slug}"
    work_dir.mkdir(parents=True, exist_ok=True)
    log = work_dir / "build.log"
    log.write_bytes(b"")

    print(f"Building chapter {num} ({slug}) from {chapter_file.name}...")
    driver_tex.write_text(build_driver_tex(num, slug), encoding="utf-8")

    # pdflatex has to run in SRC_DIR so relative image/chapter paths resolve.
    # Use -jobname to prefix outputs so we don't collide with the main build.
    def px(*args: str) -> int:
        return run(
            ["pdflatex", "-interaction=nonstopmode", f"-jobname={driver_name}",
             *args, str(driver_tex.name)],
            cwd=config.SRC_DIR, log=log,
        )

    # Pass 1
    px()
    # Bibtex (references only resolve after this)
    run(["bibtex", driver_name], cwd=config.SRC_DIR, log=log)
    # Passes 2 and 3
    px()
    px()

    produced = config.SRC_DIR / f"{driver_name}.pdf"
    if not produced.is_file():
        sys.exit(f"error: pdflatex did not produce {produced} — see {log}")

    dst = config.CHAPTER_PDFS / f"{num:02d}-{slug}.pdf"
    shutil.move(str(produced), str(dst))
    print(f"ok: {dst}")

    # Move intermediates into work_dir so SRC_DIR stays clean
    for ext in ("aux", "bbl", "blg", "log", "out", "toc", "lof", "lot"):
        intermediate = config.SRC_DIR / f"{driver_name}.{ext}"
        if intermediate.is_file():
            shutil.move(str(intermediate), str(work_dir / intermediate.name))

    if not args.keep_driver:
        driver_tex.unlink()

    # Summarize
    from subprocess import check_output
    try:
        info = check_output(["pdfinfo", str(dst)], text=True)
        for line in info.splitlines():
            if line.startswith("Pages:") or line.startswith("File size:"):
                print(f"  {line}")
    except Exception:
        pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
