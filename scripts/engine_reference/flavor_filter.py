#!/usr/bin/env python3
"""Resolve \\iftoggle{...}{...}{...} branches in a LaTeX file for a given
flavor.

The Engine Reference Manual's LaTeX source uses etoolbox's \\iftoggle to
branch content between three product flavors: RiverFlow2D, OilFlow2D, and
HydroBID Flood. The `\\toggletrue{X}` lines in the main manual's preamble
select the flavor; LaTeX evaluates the toggles at compile time.

For markdown conversion we need to resolve those branches statically — the
markdown pipeline is one-file-per-flavor, so we pre-compute the flavor's
content before feeding anything to Pandoc.

Toggle semantics:
  \\iftoggle{FLAG}{TRUE}{FALSE}  → keep TRUE if FLAG set, FALSE otherwise.
  \\iftoggle{FLAG}{TRUE}         → keep TRUE if FLAG set, nothing otherwise.

Supports:
  - Arbitrary nesting: \\iftoggle wrapping \\iftoggle
  - Mixed whitespace / comments between argument groups
  - `{TRUE}{FALSE}` on same line or across lines
  - Comment lines inside branches (preserves them)

Usage:
    python flavor_filter.py <input.tex> <flavor> <output.tex>

Flavors:
    riverflow2d   - sets iRiverFlow=true
    oilflow2d     - sets iOilFlow=true
    hydrobid-flood - sets hBIDFlood=true

Example:
    python flavor_filter.py chapters/01-introduction.tex riverflow2d \\
        build/flavor-tex/riverflow2d/01-introduction.tex
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


FLAVOR_TOGGLES = {
    "riverflow2d":    {"iRiverFlow": True,  "iOilFlow": False, "hBIDFlood": False},
    "oilflow2d":      {"iRiverFlow": False, "iOilFlow": True,  "hBIDFlood": False},
    "hydrobid-flood": {"iRiverFlow": False, "iOilFlow": False, "hBIDFlood": True},
}


def find_matching_brace(text: str, start: int) -> int:
    """Given text[start] == '{', return index of matching '}'.

    Tracks depth and ignores braces inside LaTeX line comments (after an
    unescaped '%' until end of line).
    """
    assert text[start] == "{"
    depth = 0
    i = start
    n = len(text)
    while i < n:
        c = text[i]
        if c == "%" and (i == 0 or text[i - 1] != chr(0x5c)):
            # Skip to end of line
            nl = text.find("\n", i)
            if nl < 0:
                return -1
            i = nl + 1
            continue
        if c == chr(0x5c) and i + 1 < n:
            # Escape: skip the next char (could be \{ or \})
            i += 2
            continue
        if c == "{":
            depth += 1
            i += 1
            continue
        if c == "}":
            depth -= 1
            if depth == 0:
                return i
            i += 1
            continue
        i += 1
    return -1


def skip_whitespace_and_comments(text: str, i: int) -> int:
    """Advance past whitespace and LaTeX line comments."""
    n = len(text)
    while i < n:
        c = text[i]
        if c.isspace():
            i += 1
            continue
        if c == "%" and (i == 0 or text[i - 1] != chr(0x5c)):
            nl = text.find("\n", i)
            if nl < 0:
                return n
            i = nl + 1
            continue
        break
    return i


def _is_in_line_comment(text: str, idx: int) -> bool:
    """Return True if position `idx` is inside a LaTeX line comment.

    Walks back from `idx` to the previous newline and checks whether an
    unescaped `%` appears before `idx` on that line. Needed because the
    source occasionally comments out \\iftoggle directives for manual
    toggling (e.g. `%\\iftoggle{iOilFlow}{%`), which were being treated
    as live directives by the naive `text.find('\\iftoggle', i)` search
    and consuming unrelated downstream content until the next `}`.
    """
    # Find start of current line
    line_start = text.rfind("\n", 0, idx) + 1
    # Scan from line_start to idx looking for an unescaped `%`
    j = line_start
    while j < idx:
        c = text[j]
        if c == "%" and (j == 0 or text[j - 1] != chr(0x5c)):
            return True
        j += 1
    return False


def resolve_iftoggle(text: str, toggles: dict[str, bool]) -> str:
    """Resolve every \\iftoggle{FLAG}{TRUE}{FALSE?} in `text` using the
    given toggle map. Nested iftoggles are resolved recursively.

    Skips occurrences inside LaTeX line comments — the source sometimes
    has commented-out iftoggles that must remain inert.
    """
    TOKEN = chr(0x5c) + "iftoggle"
    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        idx = text.find(TOKEN, i)
        if idx < 0:
            out.append(text[i:])
            break
        # Skip commented-out iftoggles: emit the literal up to and
        # including the token, then continue scanning past it.
        if _is_in_line_comment(text, idx):
            out.append(text[i:idx + len(TOKEN)])
            i = idx + len(TOKEN)
            continue
        # Emit everything before the token
        out.append(text[i:idx])
        # Parse \iftoggle{FLAG}{TRUE}{FALSE?}
        j = idx + len(TOKEN)
        # Allow whitespace before the `{`
        j = skip_whitespace_and_comments(text, j)
        if j >= n or text[j] != "{":
            # Malformed — emit the token verbatim and move on
            out.append(TOKEN)
            i = idx + len(TOKEN)
            continue
        flag_end = find_matching_brace(text, j)
        if flag_end < 0:
            out.append(text[idx:])
            break
        flag = text[j + 1:flag_end]
        # True branch
        k = skip_whitespace_and_comments(text, flag_end + 1)
        if k >= n or text[k] != "{":
            # No true branch — malformed. Emit verbatim.
            out.append(text[idx:flag_end + 1])
            i = flag_end + 1
            continue
        true_end = find_matching_brace(text, k)
        if true_end < 0:
            out.append(text[idx:])
            break
        true_branch = text[k + 1:true_end]
        # Optional false branch
        m = skip_whitespace_and_comments(text, true_end + 1)
        false_branch = ""
        end_pos = true_end + 1
        if m < n and text[m] == "{":
            false_end = find_matching_brace(text, m)
            if false_end >= 0:
                false_branch = text[m + 1:false_end]
                end_pos = false_end + 1
        # Select the branch
        flag_value = toggles.get(flag, False)
        selected = true_branch if flag_value else false_branch
        # Recursively resolve iftoggles inside the selected branch
        out.append(resolve_iftoggle(selected, toggles))
        i = end_pos
    return "".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("input_tex", type=Path)
    ap.add_argument("flavor", choices=sorted(FLAVOR_TOGGLES.keys()))
    ap.add_argument("output_tex", type=Path)
    args = ap.parse_args()

    if not args.input_tex.is_file():
        sys.exit(f"error: no such file: {args.input_tex}")

    toggles = FLAVOR_TOGGLES[args.flavor]
    src = args.input_tex.read_text(encoding="utf-8", errors="replace")
    dst = resolve_iftoggle(src, toggles)

    args.output_tex.parent.mkdir(parents=True, exist_ok=True)
    args.output_tex.write_text(dst, encoding="utf-8")

    # Report stats
    n_before = src.count(chr(0x5c) + "iftoggle")
    n_after = dst.count(chr(0x5c) + "iftoggle")
    print(f"{args.input_tex.name} -> {args.output_tex.name}")
    print(f"  flavor: {args.flavor}  toggles: {toggles}")
    print(f"  \\iftoggle before: {n_before}, after: {n_after}")
    print(f"  size: {len(src)} -> {len(dst)} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
