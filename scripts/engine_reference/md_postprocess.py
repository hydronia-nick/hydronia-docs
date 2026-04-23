#!/usr/bin/env python3
"""Post-process raw Pandoc markdown for the Engine Reference pipeline.

Pandoc is a good LaTeX reader, but a few of its markdown habits do not fit
the house style used by the docs site:

* image widths sometimes arrive in LaTeX-flavored attribute syntax that the
  downstream renderer does not interpret consistently;
* source images still point at ``images/`` or ``imagesOUTPUT/`` instead of
  the docs-site ``img/`` folder;
* stripped citations leave awkward punctuation gaps;
* ``::: shaded`` blocks should become MkDocs Material admonitions; and
* Pandoc inserts extra blank lines between list items.

This module keeps those fixes in one place. The public helper returns the
cleaned markdown plus the copied image pairs so the orchestrator can report
what happened. Missing images are warned about rather than crashing so the
caller can decide whether to treat them as fatal.
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

_LEADING_DOT_DIM_RE = re.compile(r"^(\.)(\d)")
_TEXTWIDTH_SCALED_RE = re.compile(r"^(\d+(?:\.\d+)?)\\textwidth$")
_TEXTWIDTH_PLAIN_RE = re.compile(r"^\\textwidth$")

_ATTR_TOKEN_RE = re.compile(
    r"(?P<id>#fig:[^\s{}]+)"
    r"|(?P<key>width|height)\s*=\s*(?P<value>\"[^\"]*\"|'[^']*'|[^\s{}]+)"
)

_IMAGE_RE = re.compile(
    r"!\[(?P<alt>[^\]]*)\]\((?P<path>[^)]+)\)"
    r"(?P<attrs>(?:\s*\{[^{}\n]*\}"
    r"|\s+(?:(?:#fig:[^\s{}]+|width\s*=\s*(?:\"[^\"]+\"|[^\s{}]+)"
    r"|height\s*=\s*(?:\"[^\"]+\"|[^\s{}]+))"
    r"(?:\s+(?:#fig:[^\s{}]+|width\s*=\s*(?:\"[^\"]+\"|[^\s{}]+)"
    r"|height\s*=\s*(?:\"[^\"]+\"|[^\s{}]+)))*))?)"
)

_HEADING_UNNUMBERED_RE = re.compile(r"^(?P<prefix>#{1,6}\s+.*?)(?:\s*\{-\})\s*$")
_LIST_ITEM_RE = re.compile(r"^(?P<indent>[ \t]*)(?:[-*+]|\d+[.)])\s+")
_CODE_FENCE_OPEN_RE = re.compile(
    r"^(?P<indent>[ \t]*)(?P<fence>`{3,}|~{3,})(?P<info>[^\n]*)$"
)
_SHADED_OPEN_RE = re.compile(r"^(?P<indent>[ \t]*)(?P<colons>:{3,})\s+shaded\s*$")


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _normalize_dim(value: str) -> str:
    """Normalize a Pandoc width/height value into the downstream-friendly form."""

    value = _strip_quotes(value)
    while "\\\\" in value:
        value = value.replace("\\\\", "\\")
    value = _LEADING_DOT_DIM_RE.sub(r"0.\2", value)
    m = _TEXTWIDTH_SCALED_RE.match(value)
    if m:
        return f"{int(float(m.group(1)) * 100 + 0.5)}%"
    if _TEXTWIDTH_PLAIN_RE.match(value):
        return "100%"
    return value


def _format_dim_attrs(dims: list[tuple[str, str]]) -> str:
    if not dims:
        return ""
    return "{ " + " ".join(f"{key}={value}" for key, value in dims) + " }"


def _split_leading_indent(text: str) -> tuple[str, str]:
    i = 0
    n = len(text)
    while i < n and text[i] in " \t":
        i += 1
    return text[:i], text[i:]


def _normalize_attr_suffix(attrs: str) -> str:
    """Normalize a markdown attribute suffix while discarding figure IDs.

    Pandoc can emit either a real attribute block (``{...}``) or a bare
    trailing attribute list. We only preserve width/height, and we drop
    ``#fig:...`` identifiers because the downstream markdown pages do not
    use them.
    """

    if not attrs:
        return ""

    stripped = attrs.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        content = stripped[1:-1].strip()
    else:
        content = stripped

    dims: list[tuple[str, str]] = []
    relevant = False
    for match in _ATTR_TOKEN_RE.finditer(content):
        if match.group("id"):
            relevant = True
            continue
        key = match.group("key")
        value = match.group("value")
        if key and value:
            dims.append((key, _normalize_dim(value)))
            relevant = True

    if not relevant:
        return attrs
    return _format_dim_attrs(dims)


_DISPLAY_MATH_OPEN_RE = re.compile(r"^\s*\$\$(?!\$)")
_DISPLAY_MATH_CLOSE_RE = re.compile(r"\$\$\s*$")


_FENCE_RE = re.compile(r"^\s*(?P<colons>:{3,})\s*(?P<label>\S+)?\s*$")

# Pandoc multiline-table separator: a leading-indented line of dash runs
# separated by spaces. Used to detect and clean up tables produced from
# LaTeX ``\\begin{longtable}``.
_MULTILINE_TABLE_SEP_RE = re.compile(r"^\s*-+(?:\s+-+)+\s*$")
_LONGTABLE_CONTINUATION_RE = re.compile(
    r"^\s*Table\s*--\s*continued from previous page\s*$"
)


def _parse_column_boundaries(sep_line: str) -> list[tuple[int, int]]:
    """Return [(start, end)] positions of each dash run in a multiline
    table separator line."""
    bounds: list[tuple[int, int]] = []
    in_run = False
    start = 0
    for i, c in enumerate(sep_line):
        if c == "-" and not in_run:
            in_run = True
            start = i
        elif c != "-" and in_run:
            in_run = False
            bounds.append((start, i))
    if in_run:
        bounds.append((start, len(sep_line)))
    return bounds


def _normalize_pandoc_multiline_tables(text: str) -> str:
    """Clean up Pandoc multiline tables emitted from LaTeX longtable.

    Two passes happen here:

    1. Drop phantom rows (blank separators, ``Table -- continued from
       previous page`` artifacts) that terminate Pandoc's re-read of its
       own multiline table early — without this the data rows fall out
       of the table and render as a verbatim block overflowing the page.

    2. When every data row has an empty first column (common in LaTeX
       longtables with a decorative leading ``p{3cm}`` that the source
       never populated), collapse that column out of the markdown
       entirely. Pandoc's subsequent LaTeX writer emits one fewer
       ``p{...}`` specification and the table_widths Lua filter then
       has sensible widths to assign to the real data columns.
    """
    lines = text.split("\n")
    out: list[str] = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if not _MULTILINE_TABLE_SEP_RE.match(line):
            out.append(line)
            i += 1
            continue
        # Collect the block: the preceding header row, separator, and
        # following data rows until a clear terminator. Terminators are
        # lines that signal we've left the table entirely: a blank line
        # followed by any non-indented content (heading, prose, fence),
        # a fence closer, or a caption starter. Inside the block we
        # silently drop the ``Table -- continued from previous page``
        # phantom rows that otherwise break Pandoc's re-parse.
        header_idx = len(out) - 1 if out else -1
        header_line = out[header_idx] if header_idx >= 0 else ""

        block_rows: list[str] = []
        sep_line = line
        i += 1
        while i < n:
            inner = lines[i]
            stripped = inner.strip()
            if stripped.startswith(":::") or stripped.startswith(": "):
                break
            # Blank line: look ahead. If the next non-blank line still
            # looks like a table row (2+ leading spaces + content), this
            # is a sparse continuation row — drop it. Otherwise the table
            # is ending — emit the blank as terminator and exit.
            if not stripped:
                j = i + 1
                while j < n and not lines[j].strip():
                    j += 1
                if j < n and lines[j].startswith("  ") and not lines[j].lstrip().startswith(("#", "*", "-", "+", "1", "2", "3", "4", "5", "6", "7", "8", "9")):
                    # Looks like a continuation row — drop this blank
                    i += 1
                    continue
                # Not a table continuation — table ended here
                break
            if _LONGTABLE_CONTINUATION_RE.match(inner):
                i += 1
                continue
            block_rows.append(inner)
            i += 1

        # Check if the first column is empty across header + all rows
        bounds = _parse_column_boundaries(sep_line)
        first_col_empty = False
        if len(bounds) >= 2:
            first_start, first_end = bounds[0]
            def _col1_empty(row: str) -> bool:
                if len(row) < first_end:
                    return not row[first_start:].strip()
                return not row[first_start:first_end].strip()

            rows_to_check: list[str] = []
            if header_line.strip():
                rows_to_check.append(header_line)
            rows_to_check.extend(block_rows)
            if rows_to_check and all(_col1_empty(r) for r in rows_to_check):
                first_col_empty = True

        if first_col_empty:
            second_start = bounds[1][0]
            # Use a 2-space indent (Pandoc multiline-table convention)
            # so the row isn't misread as an indented code block. The
            # column separators inside the row remain 2+ spaces wide,
            # which `_cleanup_text` preserves by virtue of its
            # multiline-table detector below.
            indent = "  "

            def _strip_first_col(row: str) -> str:
                if len(row) <= second_start:
                    return row
                return indent + row[second_start:]

            if header_line.strip():
                out[header_idx] = _strip_first_col(header_line)
            # Rebuild separator with the same preserved indent.
            new_sep = indent + sep_line[second_start:]
            out.append(new_sep)
            for r in block_rows:
                out.append(_strip_first_col(r))
        else:
            out.append(sep_line)
            out.extend(block_rows)

    return "\n".join(out)


def _strip_pseudo_longtables(text: str) -> str:
    """Unwrap ``:::: center`` / ``::: longtable`` fenced divs that Pandoc
    emits from ``\\begin{center}\\begin{longtable}``.

    These fenced divs never render as useful tables in mkdocs because the
    Pandoc output preserves the LaTeX ``&`` column separators and
    ``\\endhead`` / ``\\endfoot`` stubs as loose text — mkdocs has no way
    to recover the table structure. Worse, the ``mkdocs-caption`` plugin
    occasionally crashes on certain shapes of these blocks (observed on
    Engine Reference Ch 14, breaking strict builds). We drop just the
    paired opener/closer fence lines for ``center`` and ``longtable``;
    ``shaded`` blocks and everything else are untouched so the admonition
    rewriting in ``_process_lines`` still fires.
    """
    lines = text.split("\n")
    out: list[str] = []
    # Stack of colon-counts whose opener had a label we want to strip
    strip_stack: list[int] = []
    for line in lines:
        m = _FENCE_RE.match(line)
        if m:
            colons = len(m.group("colons"))
            label = m.group("label")
            if label in {"center", "longtable"}:
                strip_stack.append(colons)
                continue
            if label is None and strip_stack and strip_stack[-1] == colons:
                strip_stack.pop()
                continue
        out.append(line)
    return "\n".join(out)


def _normalize_bare_urls(text: str) -> str:
    """Normalize scheme-less URLs emitted by Pandoc as ``[X](X){.uri}``.

    When the source LaTeX uses ``\\url{www.hydronia.com}`` or writes a
    bare email address, Pandoc emits ``[www.hydronia.com](www.hydronia.com){.uri}``
    — a link whose target is a relative path. MkDocs strict mode fails
    the build because the target isn't a documentation file. Rewrite
    these to proper absolute links: ``<https://...>`` for web URLs and
    ``<mailto:...>`` for email addresses. The ``{.uri}`` class marker is
    dropped in both cases.
    """

    def _sub(m: re.Match[str]) -> str:
        label, target = m.group("label"), m.group("target")
        if label != target:
            # Different label/target — preserve the label but rewrite target
            if "@" in target and "/" not in target:
                scheme = "mailto:"
            elif not re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*://", target):
                scheme = "https://"
            else:
                scheme = ""
            return f"[{label}]({scheme}{target})"
        # Same label and target — autolink form
        if "@" in target and "/" not in target:
            return f"<mailto:{target}>"
        if re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*://", target):
            return f"<{target}>"
        return f"<https://{target}>"

    return re.sub(
        r"\[(?P<label>[^\]\n]+)\]\((?P<target>[^)\s]+)\)\{\.uri\}",
        _sub,
        text,
    )


def _align_to_aligned(text: str) -> str:
    """Rewrite ``\\begin{align}...\\end{align}`` to ``aligned`` when wrapped
    in display-math ``$$...$$``.

    Pandoc renders LaTeX ``align`` environments by wrapping them in ``$$``
    on output, but ``align`` is itself a display environment and is
    invalid inside ``$$``; the body won't compile. ``aligned`` is the
    inner counterpart designed to live inside math mode and takes the
    same syntax. We only rewrite when the opener appears on a line
    starting with ``$$`` to avoid touching bare ``align`` environments
    that users actually wrote at document level.
    """
    # Swap the opener only when preceded by ``$$`` (same line or
    # previous line that's just ``$$``) to avoid clobbering bare align
    # blocks. In practice Pandoc always emits ``$$\begin{align}`` on the
    # same line, so a simple pair-level substitution is enough.
    text = re.sub(r"\$\$\s*\\begin\{align\}", r"$$\\begin{aligned}", text)
    text = re.sub(r"\\end\{align\}\s*\$\$", r"\\end{aligned}$$", text)
    return text


def _collapse_blank_lines_in_display_math(text: str) -> str:
    """Replace blank lines inside ``$$...$$`` display-math blocks with a
    single newline.

    Pandoc's ``tex_math_dollars`` extension treats a blank line as an
    end-of-math delimiter; any blank line between the opening and closing
    ``$$`` splits one display-math block into two, and the second opener
    ends up escaped as literal ``\\$\\$`` in the LaTeX output. The source
    LaTeX frequently has visual spacing inside nested ``\\begin{array}``
    environments (e.g. between ``\\mathbf{F}`` and ``\\mathbf{G}`` rows).

    Detection rules — we only enter display-math collapsing when a line
    starts with ``$$`` (ignoring leading whitespace) AND does not close
    the same math on the same line. We exit when we see a line ending
    with ``$$``. This avoids false positives from adjacent inline-math
    pairs like ``$^2$$^\\circ$`` which also contain the substring ``$$``
    but are not display math.
    """
    lines = text.split("\n")
    out: list[str] = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if _DISPLAY_MATH_OPEN_RE.match(line) and not _DISPLAY_MATH_CLOSE_RE.search(
            line.lstrip()[2:]  # ignore the opener when checking for a same-line close
        ):
            # Display math opener on its own line. Collect until a line
            # that ends with ``$$``, collapsing blank interior lines.
            out.append(line)
            i += 1
            while i < n:
                inner = lines[i]
                if not inner.strip():
                    # Skip blank lines inside the math block
                    i += 1
                    continue
                out.append(inner)
                if _DISPLAY_MATH_CLOSE_RE.search(inner):
                    i += 1
                    break
                i += 1
            continue
        out.append(line)
        i += 1
    return "\n".join(out)


class MarkdownPostProcessor:
    """Apply the manual-specific markdown cleanups and image copying."""

    def __init__(self, source_dir_for_images: Path, target_img_dir: Path) -> None:
        self.source_dir_for_images = Path(source_dir_for_images)
        self.target_img_dir = Path(target_img_dir)
        self.copied_images: dict[str, tuple[Path, Path]] = {}
        self.warnings: list[str] = []
        self._warned_missing: set[str] = set()

    def process(self, raw_md_text: str) -> str:
        """Return cleaned markdown for a single chapter."""

        text = raw_md_text.replace("\r\n", "\n").replace("\r", "\n")
        text = _collapse_blank_lines_in_display_math(text)
        text = _align_to_aligned(text)
        text = _normalize_bare_urls(text)
        text = _strip_pseudo_longtables(text)
        text = _normalize_pandoc_multiline_tables(text)
        processed = self._process_lines(text.splitlines(keepends=True))
        processed = self._collapse_list_spacing(processed)
        return processed.rstrip("\n") + "\n"

    @property
    def copied_image_pairs(self) -> list[tuple[Path, Path]]:
        return list(self.copied_images.values())

    def _warn(self, message: str) -> None:
        self.warnings.append(message)
        print(message, file=sys.stderr)

    def _process_lines(self, lines: list[str]) -> str:
        out: list[str] = []
        i = 0
        n = len(lines)
        while i < n:
            line = lines[i]
            core = line.rstrip("\n")

            code_open = _CODE_FENCE_OPEN_RE.match(core)
            if code_open:
                fence = code_open.group("fence")
                indent = code_open.group("indent")
                fence_char = fence[0]
                fence_len = len(fence)
                out.append(line)
                i += 1
                while i < n:
                    body_line = lines[i]
                    body_core = body_line.rstrip("\n")
                    out.append(body_line)
                    if body_core.startswith(indent):
                        trailer = body_core[len(indent) :]
                        if re.fullmatch(rf"{re.escape(fence_char)}{{{fence_len},}}\s*", trailer):
                            i += 1
                            break
                    i += 1
                continue

            shaded = _SHADED_OPEN_RE.match(core)
            if shaded:
                min_colons = len(shaded.group("colons"))
                indent = shaded.group("indent")
                close_idx = self._find_shaded_close(lines, i + 1, min_colons)
                if close_idx is None:
                    # Malformed block. Emit the line verbatim and keep going.
                    out.append(self._process_normal_line(line))
                    i += 1
                    continue

                body_text = "".join(lines[i + 1 : close_idx])
                body_clean = self._process_lines(body_text.splitlines(keepends=True))
                body_clean = body_clean.strip("\n")
                out.append(f"{indent}!!! note\n")
                if body_clean:
                    body_indent = f"{indent}    "
                    for body_line in body_clean.splitlines(keepends=True):
                        if body_line.endswith("\n"):
                            out.append(f"{body_indent}{body_line}")
                        else:
                            out.append(f"{body_indent}{body_line}\n")
                i = close_idx + 1
                continue

            out.append(self._process_normal_line(line))
            i += 1

        return "".join(out)

    def _find_shaded_close(self, lines: list[str], start: int, min_colons: int) -> int | None:
        for idx in range(start, len(lines)):
            core = lines[idx].rstrip("\n")
            if re.fullmatch(rf"[ \t]*:{{{min_colons},}}\s*", core):
                return idx
        return None

    def _process_normal_line(self, line: str) -> str:
        core = line.rstrip("\n")
        if not core.strip():
            return "\n"

        core = self._rewrite_images(core)
        core = _HEADING_UNNUMBERED_RE.sub(r"\g<prefix>", core)
        core = self._cleanup_text(core)
        return core + "\n"

    def _cleanup_text(self, text: str) -> str:
        # Strip Pandoc's HTML-comment-as-raw-inline artifact. Pandoc emits
        # `<!-- -->`{=html} after inline math (e.g. `$>$`) to prevent the
        # following text from being merged into the math token. In our
        # markdown output the wrapper is pure noise and corrupts rendering
        # under mkdocs-material.
        text = re.sub(r"`<!--\s*-->`\{=html\}", "", text)
        text = re.sub(r"\(\s*\)", "", text)
        text = re.sub(r"(?<=\S)\s+\.(?=(?:\s|$|[)\]\}\"']))", ".", text)
        # Collapse runs of 2+ whitespace only when the line isn't
        # carrying column boundaries. Two shapes preserve their spacing:
        #   (a) Heavy leading indent (10+ spaces) — classic Pandoc
        #       multiline-table rows before the col1-strip step.
        #   (b) Two or more interior multi-space runs — the signature of
        #       a multiline-table row after col1 is stripped (e.g.
        #       `TriMesh    Polygon    Contains the mesh…`).
        # Collapsing either would flatten the table into one column.
        leading, rest = _split_leading_indent(text)
        interior_multi_runs = len(re.findall(r"\S[ \t]{2,}\S", rest))
        if len(leading) < 10 and interior_multi_runs < 2:
            rest = re.sub(r"[ \t]{2,}", " ", rest)
        return leading + rest

    def _rewrite_images(self, text: str) -> str:
        return _IMAGE_RE.sub(self._rewrite_image_match, text)

    def _rewrite_image_match(self, match: re.Match[str]) -> str:
        alt = match.group("alt")
        raw_path = match.group("path").strip()
        attrs = match.group("attrs") or ""
        dest_name = self._copy_image(raw_path)
        normalized_attrs = _normalize_attr_suffix(attrs)
        # Pandoc emits ``![image](path)`` as a placeholder alt when it
        # converts a LaTeX ``\begin{figure}\includegraphics{...}\end{figure}``
        # that had no ``\caption{}`` in the source. On the return trip
        # through Pandoc's markdown → LaTeX writer, a non-empty alt
        # becomes both the figure caption and a "List of Figures" entry,
        # which is how captionless source figures leak in as literal
        # "image" lines in the TOC. Dropping the placeholder alt lets
        # Pandoc emit a plain ``\includegraphics`` that stays inline and
        # out of the LOF.
        if alt.strip().lower() == "image":
            alt = ""
        return f"![{alt}](img/{dest_name}){normalized_attrs}"

    def _copy_image(self, raw_path: str) -> str:
        requested = self._sanitize_requested_path(raw_path)
        dest_name = requested.name.lower()
        source_path = self._resolve_image_source(requested)

        if source_path is None:
            key = raw_path.casefold()
            if key not in self._warned_missing:
                self._warned_missing.add(key)
                self._warn(
                    f"warning: image not found: {raw_path} "
                    f"(searched {self.source_dir_for_images / 'images'} "
                    f"and {self.source_dir_for_images / 'imagesOUTPUT'})"
                )
            return dest_name

        existing = self.copied_images.get(dest_name)
        if existing is not None:
            existing_src, _ = existing
            if existing_src != source_path:
                raise ValueError(
                    f"image destination collision for {dest_name!r}: "
                    f"{existing_src} vs {source_path}"
                )
            return dest_name

        self.target_img_dir.mkdir(parents=True, exist_ok=True)
        dest_path = self.target_img_dir / dest_name
        shutil.copy2(source_path, dest_path)
        self.copied_images[dest_name] = (source_path, dest_path)
        return dest_name

    def _sanitize_requested_path(self, raw_path: str) -> Path:
        requested = Path(raw_path)
        parts = [part for part in requested.parts if part not in (".", "..")]
        return Path(*parts) if parts else Path(requested.name)

    def _resolve_image_source(self, requested: Path) -> Path | None:
        parts = tuple(part.lower() for part in requested.parts)
        if not parts:
            return None

        roots: list[Path]
        rel_targets: list[Path]
        if parts[0] == "images":
            roots = [self.source_dir_for_images / "images", self.source_dir_for_images / "imagesOUTPUT"]
            rel_targets = [Path(*requested.parts[1:]), Path(requested.name)]
        elif parts[0].lower() == "imagesoutput":
            roots = [self.source_dir_for_images / "imagesOUTPUT", self.source_dir_for_images / "images"]
            rel_targets = [Path(*requested.parts[1:]), Path(requested.name)]
        else:
            roots = [self.source_dir_for_images / "images", self.source_dir_for_images / "imagesOUTPUT"]
            rel_targets = [Path(*requested.parts), Path(requested.name)]

        for root in roots:
            if not root.exists():
                continue
            for rel_target in rel_targets:
                if not rel_target.parts:
                    continue
                direct = root / rel_target
                if direct.is_file():
                    return direct
                found = self._find_case_insensitive(root, rel_target)
                if found is not None:
                    return found
        return None

    def _find_case_insensitive(self, root: Path, rel_target: Path) -> Path | None:
        wanted_parts = tuple(part.lower() for part in rel_target.parts)
        exact_matches: list[Path] = []
        name_matches: list[Path] = []

        for candidate in root.rglob("*"):
            if not candidate.is_file():
                continue
            rel_parts = tuple(part.lower() for part in candidate.relative_to(root).parts)
            if rel_parts == wanted_parts:
                exact_matches.append(candidate)
            elif candidate.name.lower() == rel_target.name.lower():
                name_matches.append(candidate)

        if len(exact_matches) == 1:
            return exact_matches[0]
        if len(exact_matches) > 1:
            raise FileNotFoundError(
                f"ambiguous image reference {rel_target!s} in {root}: "
                + ", ".join(str(path) for path in exact_matches)
            )
        if len(name_matches) == 1:
            return name_matches[0]
        if len(name_matches) > 1:
            raise FileNotFoundError(
                f"ambiguous image reference {rel_target!s} in {root}: "
                + ", ".join(str(path) for path in name_matches)
            )
        return None

    def _collapse_list_spacing(self, text: str) -> str:
        lines = text.splitlines(keepends=True)
        out: list[str] = []
        i = 0
        prev_nonblank: str | None = None

        while i < len(lines):
            line = lines[i]
            core = line.rstrip("\n")

            code_open = _CODE_FENCE_OPEN_RE.match(core)
            if code_open:
                fence = code_open.group("fence")
                indent = code_open.group("indent")
                fence_char = fence[0]
                fence_len = len(fence)
                out.append(line)
                prev_nonblank = line
                i += 1
                while i < len(lines):
                    body_line = lines[i]
                    body_core = body_line.rstrip("\n")
                    out.append(body_line)
                    prev_nonblank = body_line
                    if body_core.startswith(indent):
                        trailer = body_core[len(indent) :]
                        if re.fullmatch(rf"{re.escape(fence_char)}{{{fence_len},}}\s*", trailer):
                            i += 1
                            break
                    i += 1
                continue

            if not core.strip():
                j = i + 1
                while j < len(lines) and not lines[j].rstrip("\n").strip():
                    j += 1
                if prev_nonblank is not None and j < len(lines):
                    prev_match = _LIST_ITEM_RE.match(prev_nonblank.rstrip("\n"))
                    next_match = _LIST_ITEM_RE.match(lines[j].rstrip("\n"))
                    if prev_match and next_match and prev_match.group("indent") == next_match.group("indent"):
                        i = j
                        continue
                out.append(line)
                i += 1
                continue

            out.append(line)
            prev_nonblank = line
            i += 1

        return "".join(out)


def postprocess_markdown(
    raw_md_text: str,
    source_dir_for_images: Path,
    target_img_dir: Path,
) -> tuple[str, list[tuple[Path, Path]]]:
    """Clean Pandoc markdown and copy any referenced images.

    The return value stays small and convenient for the orchestrator:
    cleaned text plus the copied image pairs.
    """

    processor = MarkdownPostProcessor(source_dir_for_images, target_img_dir)
    cleaned = processor.process(raw_md_text)
    return cleaned, processor.copied_image_pairs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("input_md", type=Path)
    ap.add_argument("source_dir", type=Path)
    ap.add_argument("target_dir", type=Path)
    ap.add_argument("output_md", type=Path)
    args = ap.parse_args()

    if not args.input_md.is_file():
        sys.exit(f"error: no such file: {args.input_md}")

    raw_md = args.input_md.read_text(encoding="utf-8", errors="replace")
    processor = MarkdownPostProcessor(args.source_dir, args.target_dir)
    cleaned = processor.process(raw_md)

    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(cleaned, encoding="utf-8")

    print(f"{args.input_md.name} -> {args.output_md.name}")
    print(f"  size: {len(raw_md)} -> {len(cleaned)} bytes")
    print(f"  images copied: {len(processor.copied_images)}")
    for source_path, dest_path in processor.copied_image_pairs:
        print(f"    {source_path} -> {dest_path}")
    if processor.warnings:
        print(f"  warnings: {len(processor.warnings)}")
    else:
        print("  warnings: none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
