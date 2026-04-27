from __future__ import annotations

import re


PDF_LAYOUT_RE = re.compile(r"^\s*(?:[pm]\d+(?:\.\d+)?(?:cm|in)\\?){2,}\s*$")
PDF_CARRYOVER_RE = re.compile(r"^\s*&?\s*Table\s+[^\n]*continued from previous page\\?\s*$")
LATEX_SPACER_RE = re.compile(r"^\s*(?:&\s*)+\\?\s*$")
BACKSLASH_ONLY_RE = re.compile(r"^\s*\\\s*$")
INLINE_DIRECTIVE_ONLY_RE = re.compile(r"^\s*:::\s*[\w-]+(?:\s+.+?)?\s*:::\s*$")
DIRECTIVE_START_RE = re.compile(r"^\s*:::\s*[\w-]+(?:\s+.+?)?\s*$")
TABULAR_SEPARATOR_RE = re.compile(r"(?:^&\s*|\s+&\s+)")


def cleanup_markdown(text: str) -> str:
    lines = text.splitlines()
    cleaned: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if _is_artifact_line(stripped):
            i += 1
            continue

        if stripped == "::: shader":
            i = _consume_shader_block(lines, i, cleaned)
            continue

        if INLINE_DIRECTIVE_ONLY_RE.match(stripped):
            i += 1
            continue

        if DIRECTIVE_START_RE.match(stripped):
            i = _strip_generic_directive_block(lines, i, cleaned)
            continue

        tabular_rows = _convert_tabular_line(line)
        if tabular_rows is not None:
            cleaned.extend(tabular_rows)
            i += 1
            continue

        cleaned.append(line)
        i += 1

    return _collapse_blank_lines(cleaned)


def on_page_markdown(markdown: str, page, **kwargs) -> str:  # pragma: no cover - exercised via MkDocs build
    src_path = getattr(getattr(page, "file", None), "src_path", "") or ""
    if "engine-reference/" not in src_path.replace("\\", "/"):
        return markdown
    return cleanup_markdown(markdown)


def _consume_shader_block(lines: list[str], start: int, cleaned: list[str]) -> int:
    indent = re.match(r"^\s*", lines[start]).group(0)
    body: list[str] = []
    i = start + 1
    while i < len(lines):
        if lines[i].strip() == ":::":
            break
        body.append(lines[i].strip())
        i += 1

    cleaned.append(f"{indent}!!! note")
    cleaned.append("")
    for body_line in body:
        if body_line:
            cleaned.append(f"{indent}    {body_line}")
        else:
            cleaned.append("")
    return i + 1 if i < len(lines) else i


def _strip_generic_directive_block(lines: list[str], start: int, cleaned: list[str]) -> int:
    block_lines: list[str] = []
    i = start + 1
    while i < len(lines):
        if lines[i].strip() == ":::":
            cleaned.extend(cleanup_markdown("\n".join(block_lines)).splitlines())
            return i + 1
        block_lines.append(lines[i])
        i += 1
    cleaned.extend(cleanup_markdown("\n".join(block_lines)).splitlines())
    return i


def _convert_tabular_fragments(indent: str, body: str) -> list[str]:
    parts = [part.strip() for part in body.split("\\") if part.strip()]
    rows: list[str] = []
    for part in parts:
        cells = [cell.strip().strip('"') for cell in part.split("&")]
        cells = [cell for cell in cells if cell]
        if len(cells) < 2:
            rows.append(f"{indent}{part}")
            continue

        head = cells[0]
        tail = cells[1:]
        summary = "; ".join(tail)
        rows.append(f"{indent}- **{head}:** {summary}")
    return rows


def _convert_tabular_line(line: str) -> list[str] | None:
    stripped = line.strip()
    if "&" not in stripped:
        return None
    if stripped.startswith("&\\"):
        return None

    pieces = [piece.strip().strip('"') for piece in TABULAR_SEPARATOR_RE.split(stripped.rstrip("\\"))]
    cells = [piece for piece in pieces if piece]
    if len(cells) < 2:
        return None

    indent = re.match(r"^\s*", line).group(0)
    head = cells[0]
    tail = cells[1:]
    summary = "; ".join(tail)
    return [f"{indent}- **{head}:** {summary}"]


def _is_artifact_line(stripped: str) -> bool:
    if not stripped:
        return False
    return bool(
        PDF_LAYOUT_RE.match(stripped)
        or PDF_CARRYOVER_RE.match(stripped)
        or LATEX_SPACER_RE.match(stripped)
        or BACKSLASH_ONLY_RE.match(stripped)
    )


def _collapse_blank_lines(lines: list[str]) -> str:
    collapsed: list[str] = []
    blank_run = 0
    for line in lines:
        if line.strip():
            blank_run = 0
            collapsed.append(line)
            continue
        blank_run += 1
        if blank_run <= 2:
            collapsed.append("")
    return "\n".join(collapsed).rstrip() + "\n"
