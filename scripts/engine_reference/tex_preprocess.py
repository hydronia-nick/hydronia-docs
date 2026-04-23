#!/usr/bin/env python3
"""Pre-process a flavor-filtered LaTeX chapter file to make it friendly for
Pandoc's LaTeX reader.

Pandoc's LaTeX reader has subtle issues with:
  - Macros whose names share a prefix and contain digits (e.g. \\rf2d and
    \\rf2dc). Defining both causes Pandoc to fail to expand the shorter
    one. We sidestep this by expanding Hydronia's product macros via text
    replacement before Pandoc sees them.
  - Line comments whose trailing content contains braces. The cleanest
    fix is to strip line comments entirely.
  - Cross-reference commands (\\label, \\ref, \\cite) that don't map to
    markdown usefully without a bibliography. Strip or transform them.
  - Stray LaTeX spacing / kerning commands (\\ , ~, \\,) that survive as
    literal text. Normalize them.

The output is still LaTeX — just cleaner LaTeX that Pandoc can digest into
markdown without surprises. All content decisions live in one place here
so the conversion is reproducible.

Usage:
    python tex_preprocess.py <input.tex> <output.tex>
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# Hydronia product / concept macros. Text-expanded BEFORE Pandoc. Order
# matters: longer macro names must be matched first so `\rf2dc` doesn't
# get partially swallowed by `\rf2d`'s pattern.
#
# The trailing `\b`-like behaviour for numeric-suffix macros is handled
# by using negative lookahead `(?![A-Za-z0-9])` so `\rf2d` doesn't match
# inside `\rf2dc`.
MACRO_MAP: list[tuple[str, str]] = [
    # Longest first
    (r"\rfpgpu",  "RiverFlow2D GPU"),
    (r"\rfpsms",  "RiverFlow2D SMS edition"),
    (r"\rfqgis",  "RiverFlow2D"),
    (r"\rfDIP",   "RiverFlow2D Data Input Program"),
    (r"\hbflood", "HydroBID Flood"),
    (r"\hbfqgis", "HydroBID Flood"),
    (r"\ofqgis",  "OilFlow2D"),
    (r"\rf2dc",   "RiverFlow2D"),
    (r"\rf2d",    "RiverFlow2D"),
    (r"\of2d",    "OilFlow2D"),
    (r"\rflo",    "RiverFlow2D"),
    (r"\rfp",     "RiverFlow2D"),
    (r"\rfe",     "RiverFlow2D FE"),
    (r"\dip",     "DIP"),
    (r"\qgis",    "QGIS"),
    (r"\gmsh",    "GMSH"),
    (r"\sms",     "SMS"),
    # Case-sensitive singulars
    (r"\Water",   "Water"),
    (r"\water",   "water"),
]


def strip_comments(text: str) -> str:
    """Strip LaTeX line comments (% to EOL), honouring escaped percent
    signs (\\%)."""
    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c == "%" and (i == 0 or text[i - 1] != chr(0x5c)):
            # Skip to end-of-line (keep the newline to preserve paragraph
            # breaks).
            nl = text.find("\n", i)
            if nl < 0:
                break
            out.append("\n")
            i = nl + 1
            continue
        out.append(c)
        i += 1
    return "".join(out)


def expand_macros(text: str) -> str:
    """Text-replace Hydronia product macros with plain strings.

    Matches macro NAME followed by anything that is not a letter or
    digit (so `\\rf2d` doesn't match the `\\rf2dc` prefix). A trailing
    space is preserved as a space; a trailing brace-pair `{}` is
    swallowed (LaTeX idiom `\\rfqgis{}` forces a space-free boundary);
    a trailing `\\ ` (forced space) is replaced with a single space.
    """
    for macro, replacement in MACRO_MAP:
        # Pattern: \NAME followed by either:
        #   - empty braces {} (LaTeX no-op to force end of macro name)
        #   - \  (forced space)
        #   - other non-alphanumeric
        # Using negative-lookahead on the character class [A-Za-z0-9] so
        # partial prefixes don't match.
        name_esc = re.escape(macro)
        pat = re.compile(
            name_esc + r"(?![A-Za-z0-9])"
            + r"(\s*\{\}|\s*" + re.escape(chr(0x5c) + " ") + r")?"
        )
        def subfn(m: re.Match) -> str:
            trailer = m.group(1)
            # Insert a single space where the LaTeX source had boilerplate
            # for forcing one — preserves word spacing around the macro.
            if trailer:
                return replacement + " "
            return replacement
        text = pat.sub(subfn, text)
    return text


# Constructs we want to drop or simplify so Pandoc doesn't choke on them.
DROP_PATTERNS: list[tuple[str, str]] = [
    # \label{...}  — not needed for markdown output
    (r"\\label\{[^}]*\}", ""),
    # \ref{...}, \pageref{...}, \eqref{...}, \autoref{...}, \cref{...}
    # — the docs portal has no cross-reference machinery; replacing with
    # empty keeps surrounding prose readable. (Without this, Pandoc emits
    # `[\[fig:X\]](#fig:X){reference-type=...}` in the markdown which also
    # breaks the image regex on alt text containing these patterns.)
    (r"\\(?:page|eq|auto|c)?ref\{[^}]*\}", ""),
    # \cite{...} and friends — strip for now; citations not wired in the portal
    (r"\\cite[tp]?\{[^}]*\}", ""),
    (r"\\harvardcite\{[^}]*\}", ""),
    # \index{foo}{bar} (multind) — lose
    (r"\\index\{[^}]*\}\{[^}]*\}", ""),
    # \degree (gensymb/textcomp) — the docs-portal template doesn't load
    # those packages; remap inline math `$\degree$` to `^\circ` so it
    # round-trips through Pandoc into markdown that compiles in LaTeX.
    (r"\\degree\b", r"^\\circ "),
    # \FloatBarrier — no equivalent in markdown
    (r"\\FloatBarrier\b", ""),
    # \newpage — markdown has no page concept
    (r"\\newpage\b", ""),
    # \noindent — markdown flow only
    (r"\\noindent\b", ""),
    # \clearpage, \cleardoublepage
    (r"\\cleardoublepage\b", ""),
    (r"\\clearpage\b", ""),
    # Normalize LaTeX non-breaking-ish spaces to real spaces
    (r"\\\\,", " "),
    (r"\\\\;", " "),
    (r"\\\\:", " "),
    # ~ is tricky — in LaTeX it's a non-breaking space, but in markdown
    # it's literal. Replace with space where safe (inside words rare).
    # Commented out — may cause surprising edits, prefer to leave alone.
]


def drop_patterns(text: str) -> str:
    for pat, repl in DROP_PATTERNS:
        text = re.sub(pat, repl, text)
    return text


# Math shortcut macros defined in the main LaTeX preamble that Pandoc
# cannot see (we feed it one chapter at a time). Text-expand them so the
# generated markdown contains only standard LaTeX math the docs-portal
# template already supports.
_MATH_MACRO_ZERO_ARG: list[tuple[str, str]] = [
    # Replacement strings use doubled backslashes because re.sub treats
    # `\f`/`\p`/etc. as escape sequences in the replacement; we want
    # literal backslashes preserved so the LaTeX output is valid.
    (r"\tpderiv", "\\\\frac{\\\\partial}{\\\\partial t}"),
    (r"\xpderiv", "\\\\frac{\\\\partial}{\\\\partial x}"),
    (r"\ypderiv", "\\\\frac{\\\\partial}{\\\\partial y}"),
    (r"\zpderiv", "\\\\frac{\\\\partial}{\\\\partial z}"),
]


def expand_math_macros(text: str) -> str:
    """Text-expand the custom math shortcut macros from the preamble.

    Zero-arg shortcuts (``\\tpderiv`` ... ``\\zpderiv``) map to
    ``\\frac{\\partial}{\\partial <var>}`` and the two-argument
    ``\\pderiv{A}{B}`` maps to ``\\frac{\\partial A}{\\partial B}``.

    The ``{A}`` and ``{B}`` arguments may nest braces one level deep
    (e.g. ``\\pderiv{(\\rho h)}{t}``); we match single-level `{...}`
    bodies, which covers every occurrence in the Engine Reference source.
    """
    for macro, replacement in _MATH_MACRO_ZERO_ARG:
        pat = re.compile(re.escape(macro) + r"(?![A-Za-z0-9])")
        text = pat.sub(replacement, text)

    # Two-arg \pderiv{A}{B} → \frac{\partial A}{\partial B}. Balanced
    # single-level brace matching is enough for the real source.
    pderiv_pat = re.compile(
        r"\\pderiv\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}"
    )
    text = pderiv_pat.sub(
        "\\\\frac{\\\\partial \\1}{\\\\partial \\2}", text
    )
    return text


def normalize_inline_math_digit_boundary(text: str) -> str:
    """Insert a space between inline math `$...$` and a following digit.

    Pandoc's tex_math_dollars rule refuses to parse `$X$` as math when the
    closing `$` is immediately followed by a digit (disambiguation from
    currency). The Engine Reference source has many cases like
    `$\\ge$0` or `$>$26` inside tables. Inserting a space between the
    closing `$` and the digit is semantically equivalent in the printed
    output (single space) and unblocks Pandoc's math parser.
    """
    return re.sub(r"(\$[^$\n]+\$)(\d)", r"\1 \2", text)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("input_tex", type=Path)
    ap.add_argument("output_tex", type=Path)
    args = ap.parse_args()

    if not args.input_tex.is_file():
        sys.exit(f"error: no such file: {args.input_tex}")

    src = args.input_tex.read_text(encoding="utf-8", errors="replace")

    stripped = strip_comments(src)
    expanded = expand_macros(stripped)
    cleaned = drop_patterns(expanded)

    args.output_tex.parent.mkdir(parents=True, exist_ok=True)
    args.output_tex.write_text(cleaned, encoding="utf-8")

    print(f"{args.input_tex.name} -> {args.output_tex.name}")
    print(f"  {len(src)} -> {len(cleaned)} bytes")
    # Quick before/after sanity — count remaining LaTeX backslashes
    before_slashes = src.count(chr(0x5c))
    after_slashes = cleaned.count(chr(0x5c))
    print(f"  backslashes: {before_slashes} -> {after_slashes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
