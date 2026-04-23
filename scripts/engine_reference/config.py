"""Shared config for the Engine Reference Manual build harness.

Single source of truth for:
  - where the LaTeX source lives (Dropbox, NOT git-tracked)
  - where build artifacts land (local workspace, gitignored)
  - the chapter → reference-page-range registry

Chapter page ranges below are drawn from the TOC of the 2026-02-25 build of
Rf2D_ReferenceManual_QGIS_2024.tex (the reproduction build done in Phase 0.5
that matched the Dropbox reference PDF to within 3 pages / 1 KB). If the
manual adds/removes chapters, update both the slug and the page range here.
"""
from __future__ import annotations

from pathlib import Path

# --- paths --------------------------------------------------------------

# LaTeX source (stays in Dropbox, untracked)
SRC_DIR = Path(r"E:\Hydronia Dropbox\Nick Calero\Manuals\ENGINE_REFERENCE_MANUAL")
MAIN_TEX = SRC_DIR / "Rf2D_ReferenceManual_QGIS_2024.tex"
CHAPTERS_DIR = SRC_DIR / "chapters"

# Build artifacts (local workspace, gitignored under hydronia-docs/build/)
BUILD_ROOT = Path(r"E:\HydroniaLLC-Workspace\hydronia-docs\build\engine-reference")
CHAPTER_PDFS = BUILD_ROOT / "chapter-pdfs"
REFERENCE_PNGS = BUILD_ROOT / "reference-pngs"
CHAPTER_PNGS = BUILD_ROOT / "chapter-pngs"
DIFF_REPORTS = BUILD_ROOT / "diff"

# Reference PDF for chapter diff reports. This is a PINNED copy of the
# full-manual build (RF2D flavor, Phase 1a verified) — taken before we
# start Phase 2 markdown conversion so it represents "what the LaTeX
# pipeline produces right now" as the regression baseline.
#
# NOT the original 407-page Dropbox build — that one includes the
# notation.tex content we no longer have, which shifts physical page
# numbers non-uniformly across the body. Self-consistent rebuild avoids
# that pitfall.
REFERENCE_PDF = BUILD_ROOT / "reference-rf2d.pdf"

# --- chapter registry ---------------------------------------------------

# (number, slug, ref_page_first, ref_page_last)
# Page numbers are 1-based physical pages in REFERENCE_PDF, matching the
# printed Arabic page numbers on the chapter body.
CHAPTERS: list[tuple[int, str, int, int]] = [
    (1,  "introduction",                       1,   9),
    (2,  "installing-activating",             10,  22),
    (3,  "overview",                          23,  26),
    (4,  "mesh-generation",                   27,  38),
    (5,  "hydrodynamic-model",                39,  56),
    (6,  "sediment-transport",                57,  69),
    (7,  "mud-tailings",                      70,  85),
    (8,  "urban-drainage",                    86,  90),
    (9,  "pollutant-transport",               91,  95),
    (10, "water-quality",                     96, 104),
    (11, "bridge-scour",                     105, 108),
    (12, "code-parallelization",             109, 110),
    (13, "hydraulic-hydrologic-components",  111, 152),
    (14, "dip",                              153, 185),
    (15, "input-data-file",                  186, 318),
    (16, "output-file",                      319, 361),
    (17, "tools",                            362, 364),
    (18, "references",                       365, 404),
]


def lookup(num: int) -> tuple[int, str, int, int]:
    for entry in CHAPTERS:
        if entry[0] == num:
            return entry
    raise SystemExit(
        f"error: no chapter {num}; valid: {[c[0] for c in CHAPTERS]}"
    )


def ref_pdf_pages_offset() -> int:
    """Front-matter offset for the reference PDF.

    The reference PDF has roman-numbered front matter (title, legal, TOC,
    list of figures, list of tables) that precedes the Arabic body. Printed
    page N corresponds to physical PDF page N + offset. Verified against
    the 2026-02-25 build: physical page 29 shows body page 10 (Ch 2), so
    offset is 19.
    """
    return 19
