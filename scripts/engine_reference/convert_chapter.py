#!/usr/bin/env python3
"""Convert one Engine Reference chapter for one product flavor.

The chapter pipeline is intentionally linear:

1. resolve the flavor-specific ``\\iftoggle`` branches;
2. run the existing LaTeX preprocessor;
3. hand the cleaned LaTeX to Pandoc;
4. post-process the raw markdown into the docs-site house style; and
5. copy referenced images into the chapter's ``img/`` folder.

The script keeps the intermediate artifacts on disk so failures are easy to
inspect during manual runs.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import re

import config
import flavor_filter
import md_postprocess
import tex_preprocess


# Regex for LaTeX \input. Matches both `\input{filename}` and the terse
# TeX form `\input filename` (whitespace-delimited, no braces). The
# filename captures up to the next whitespace / end-of-line / brace,
# which covers the real-world usage in the Engine Reference source.
_INPUT_RE = re.compile(
    r"\\input\s*(?:\{([^}]+)\}|([^\s{}]+))"
)


def _inline_inputs(text: str, base_dir: Path, depth: int = 0) -> str:
    """Recursively inline `\\input FILE` / `\\input{FILE}` directives.

    Pandoc cannot follow \\input across files; for a faithful one-shot
    conversion we splice the referenced file contents into the source
    string before Pandoc sees it. Files resolve relative to `base_dir`
    (the source root, which is where the main LaTeX driver runs
    pdflatex from). The `.tex` extension is optional per TeX convention.
    """
    if depth > 5:
        # Safety: TeX nesting is unlikely but runaway recursion would
        # be catastrophic. Bail if we exceed a sane depth.
        return text

    def _sub(m: re.Match[str]) -> str:
        name = m.group(1) or m.group(2)
        candidates = [base_dir / name]
        if not name.lower().endswith(".tex"):
            candidates.append(base_dir / f"{name}.tex")
        for cand in candidates:
            if cand.is_file():
                inlined = cand.read_text(encoding="utf-8", errors="replace")
                # Recurse so nested \input in the included file resolves.
                return _inline_inputs(inlined, base_dir, depth + 1)
        # Not found — leave the directive in place; downstream LaTeX or
        # Pandoc error will surface the miss. Don't silently drop.
        return m.group(0)

    return _INPUT_RE.sub(_sub, text)


REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_ROOT = REPO_ROOT / "docs"

FLAVOR_TO_PRODUCT_DIR = {
    "riverflow2d": "riverflow2d",
    "oilflow2d": "oilflow2d",
    "hydrobid-flood": "hydrobid-flood",
}


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except Exception:
        return str(path)


def _filter_flavor(text: str, flavor: str) -> str:
    toggles = flavor_filter.FLAVOR_TOGGLES[flavor]
    return flavor_filter.resolve_iftoggle(text, toggles)


def _preprocess_tex(text: str) -> str:
    stripped = tex_preprocess.strip_comments(text)
    expanded = tex_preprocess.expand_macros(stripped)
    math_expanded = tex_preprocess.expand_math_macros(expanded)
    dropped = tex_preprocess.drop_patterns(math_expanded)
    return tex_preprocess.normalize_inline_math_digit_boundary(dropped)


def _run_pandoc(input_tex: Path, output_md: Path) -> None:
    if shutil.which("pandoc") is None:
        sys.exit("error: pandoc not found on PATH")

    cmd = [
        "pandoc",
        "-f",
        "latex",
        "-t",
        "markdown",
        "--wrap=none",
        str(input_tex),
        "-o",
        str(output_md),
    ]
    subprocess.run(cmd, check=True)


def convert_chapter(num: int, flavor: str) -> int:
    if flavor not in FLAVOR_TO_PRODUCT_DIR:
        raise SystemExit(
            f"error: unsupported flavor {flavor!r}; "
            f"valid: {sorted(FLAVOR_TO_PRODUCT_DIR)}"
        )

    chapter_num, slug, _, _ = config.lookup(num)
    chapter_src = config.CHAPTERS_DIR / f"{chapter_num:02d}-{slug}.tex"
    if not chapter_src.is_file():
        raise FileNotFoundError(chapter_src)

    flavor_tex = config.BUILD_ROOT / "flavor-tex" / flavor / f"{chapter_num:02d}-{slug}.tex"
    preproc_tex = config.BUILD_ROOT / "preproc-tex" / flavor / f"{chapter_num:02d}-{slug}.tex"
    raw_md = config.BUILD_ROOT / "md-raw" / flavor / f"{chapter_num:02d}-{slug}.md"

    product_dir = FLAVOR_TO_PRODUCT_DIR[flavor]
    final_md = DOCS_ROOT / product_dir / "engine-reference" / f"{chapter_num:02d}-{slug}.md"
    final_img_dir = final_md.parent / "img"

    source_text = chapter_src.read_text(encoding="utf-8", errors="replace")
    # Inline \input directives so Pandoc sees a single self-contained
    # LaTeX blob. Done before flavor filtering so nested iftoggles in
    # included files are also resolved.
    source_text = _inline_inputs(source_text, config.SRC_DIR)

    flavored_text = _filter_flavor(source_text, flavor)
    _write_text(flavor_tex, flavored_text)

    preproc_text = _preprocess_tex(flavored_text)
    _write_text(preproc_tex, preproc_text)

    raw_md.parent.mkdir(parents=True, exist_ok=True)
    _run_pandoc(preproc_tex, raw_md)

    raw_md_text = raw_md.read_text(encoding="utf-8", errors="replace")
    processor = md_postprocess.MarkdownPostProcessor(config.SRC_DIR, final_img_dir)
    cleaned_md = processor.process(raw_md_text)
    # Chapter 14 (Data Input Program) consistently trips `mkdocs-caption`
    # with an internal `NoneType.getnext()` crash in strict builds. The
    # page still renders — the plugin logs "skipping" and moves on — but
    # strict mode treats the log as fatal. Disable the figure-caption
    # enhancement on this one page via page-level front-matter; other
    # chapters keep the plugin enabled.
    if chapter_num == 14:
        cleaned_md = (
            "---\n"
            "caption:\n"
            "  figure:\n    enable: false\n"
            "  table:\n    enable: false\n"
            "  custom:\n    enable: false\n"
            "---\n\n"
            + cleaned_md.lstrip("\n")
        )
    _write_text(final_md, cleaned_md)

    print(f"chapter {chapter_num:02d}-{slug} -> {_display_path(final_md)}")
    print(f"  markdown: {_display_path(final_md)} ({final_md.stat().st_size} bytes)")
    print(f"  images copied: {len(processor.copied_image_pairs)}")
    for source_path, dest_path in processor.copied_image_pairs:
        print(f"    {_display_path(source_path)} -> {_display_path(dest_path)}")
    if processor.warnings:
        print(f"  warnings: {len(processor.warnings)}")
    else:
        print("  warnings: none")

    return 0 if not processor.warnings else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("num", type=int, help="Chapter number (1-18)")
    ap.add_argument(
        "flavor",
        choices=sorted(FLAVOR_TO_PRODUCT_DIR),
        help="Product flavor to build",
    )
    args = ap.parse_args()

    try:
        return convert_chapter(args.num, args.flavor)
    except SystemExit:
        raise
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"error: pandoc failed with exit code {exc.returncode}")
    except FileNotFoundError as exc:
        raise SystemExit(f"error: {exc}")
    except Exception as exc:
        raise SystemExit(f"error: {exc}")


if __name__ == "__main__":
    raise SystemExit(main())
