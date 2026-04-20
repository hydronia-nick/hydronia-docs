"""Pure string transforms used by the Pandoc PDF pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import html
import re
import unicodedata
import warnings

__all__ = [
    "neutralize_raw_figure_blocks",
    "rewrite_cross_chapter_links",
    "strip_cross_doc_links",
    "strip_frontmatter",
    "unescape_pandoc_quotes",
]


_FRONTMATTER_RE = re.compile(
    r"\A---\s*\r?\n.*?\r?\n(?:---|\.\.\.)\s*\r?\n+",
    re.S,
)
_FIGURE_BLOCK_RE = re.compile(r"<figure\b[^>]*>.*?</figure>", re.S | re.I)
_INLINE_LINK_RE = re.compile(r"(?<!\!)\[(?P<text>[^\]]+)\]\((?P<dest>[^)]+)\)")
_HEADING_RE = re.compile(
    r"^(?P<level>#{1,6})\s+(?P<title>.+?)(?:\s*\{#(?P<id>[A-Za-z][\w:+-]*)[^}]*\})?\s*$"
)
_FENCED_BLOCK_RE = re.compile(r"(^```.*?^```|^~~~.*?^~~~)", re.M | re.S)
_CHAPTER_HEADING_RE = re.compile(r"^#\s+")


@dataclass(frozen=True)
class HeadingInfo:
    level: int
    title: str
    explicit_id: str | None
    slug: str


@dataclass(frozen=True)
class ChapterBlock:
    slug: str
    text: str
    headings: list[HeadingInfo]


def slugify(text: str) -> str:
    """Return a stable, lower-case heading slug."""

    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


def strip_frontmatter(text: str) -> str:
    """Remove YAML front matter from the top of a chapter.

    Example:
        Before: "---\ntitle: Demo\n---\n# Demo"
        After:  "# Demo"
    """

    return _FRONTMATTER_RE.sub("", text, count=1)


def neutralize_raw_figure_blocks(text: str) -> str:
    """Replace caption-only raw figure blocks with bold caption text.

    Example:
        Before: "<figure><figcaption>Export KMZ Dialog</figcaption></figure>"
        After:  "**Export KMZ Dialog**"
    """

    def replace(match: re.Match[str]) -> str:
        block = match.group(0)
        if re.search(r"<(?:img|picture|source)\b", block, re.I):
            return block
        caption_match = re.search(r"<figcaption>(?P<cap>.*?)</figcaption>", block, re.S | re.I)
        if not caption_match:
            return block
        caption = html.unescape(re.sub(r"<[^>]+>", "", caption_match.group("cap")))
        caption = re.sub(r"\s+", " ", caption).strip()
        if not caption:
            return block
        return f"\n\n**{caption}**\n\n"

    return _FIGURE_BLOCK_RE.sub(replace, text)


def _transform_outside_fenced_code(text: str, transform) -> str:
    parts: list[str] = []
    last = 0
    for match in _FENCED_BLOCK_RE.finditer(text):
        parts.append(transform(text[last : match.start()]))
        parts.append(match.group(0))
        last = match.end()
    parts.append(transform(text[last:]))
    return "".join(parts)


def unescape_pandoc_quotes(text: str) -> str:
    """Unescape Pandoc backslash-escaped punctuation outside code blocks.

    Example:
        Before: 'The label is \\"All times\\".'
        After:  'The label is "All times".'
    """

    def transform(segment: str) -> str:
        return segment.replace('\\"', '"').replace("\\.", ".")

    return _transform_outside_fenced_code(text, transform)


def strip_cross_doc_links(text: str) -> str:
    """Drop links that point outside the manual tree.

    Example:
        Before: "[Getting Started](../getting-started/index.md)"
        After:  "Getting Started"
    """

    def transform(segment: str) -> str:
        def replace(match: re.Match[str]) -> str:
            dest = match.group("dest").strip()
            if dest.startswith("../") or dest.startswith("..\\"):
                return match.group("text")
            return match.group(0)

        return _INLINE_LINK_RE.sub(replace, segment)

    return _transform_outside_fenced_code(text, transform)


def _scan_headings(text: str) -> list[HeadingInfo]:
    headings: list[HeadingInfo] = []
    in_fence = False
    fence_marker = ""
    for line in text.splitlines():
        stripped = line.rstrip("\r\n")
        fence_match = re.match(r"^(```|~~~)", stripped)
        if fence_match:
            marker = fence_match.group(1)
            if not in_fence:
                in_fence = True
                fence_marker = marker
            elif stripped.startswith(fence_marker):
                in_fence = False
                fence_marker = ""
            continue
        if in_fence:
            continue
        match = _HEADING_RE.match(stripped)
        if not match:
            continue
        explicit_id = match.group("id")
        title = match.group("title").strip()
        headings.append(
            HeadingInfo(
                level=len(match.group("level")),
                title=title,
                explicit_id=explicit_id,
                slug=slugify(title),
            )
        )
    return headings


def _split_chapter_blocks(text: str, chapters: list[str]) -> list[ChapterBlock]:
    lines = text.splitlines(keepends=True)
    starts = [index for index, line in enumerate(lines) if _CHAPTER_HEADING_RE.match(line)]
    if not starts:
        return [ChapterBlock(slug=Path(chapters[0]).stem if chapters else "chapter", text=text, headings=_scan_headings(text))]
    blocks: list[ChapterBlock] = []
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else len(lines)
        chapter_slug = Path(chapters[index]).stem if index < len(chapters) else f"chapter-{index + 1}"
        block_text = "".join(lines[start:end])
        blocks.append(ChapterBlock(slug=chapter_slug, text=block_text, headings=_scan_headings(block_text)))
    return blocks


def rewrite_cross_chapter_links(text: str, chapters: list[str]) -> str:
    """Rewrite chapter links after concatenation.

    Example:
        Before: "[See](new-project.md#workflow)"
        After:  "[See](#new-project-workflow)"
    """

    chapter_slugs = [Path(chapter).stem for chapter in chapters]
    blocks = _split_chapter_blocks(text, chapter_slugs)
    if not blocks:
        return text

    chapter_title_slugs: dict[str, set[str]] = {}
    chapter_explicit_ids: dict[str, set[str]] = {}
    slug_to_chapters: dict[str, set[str]] = {}

    for block in blocks:
        title_slugs: set[str] = set()
        explicit_ids: set[str] = set()
        for heading in block.headings:
            if heading.explicit_id:
                explicit_ids.add(heading.explicit_id)
            else:
                title_slugs.add(heading.slug)
                slug_to_chapters.setdefault(heading.slug, set()).add(block.slug)
        chapter_title_slugs[block.slug] = title_slugs
        chapter_explicit_ids[block.slug] = explicit_ids

    duplicate_title_slugs = {slug for slug, values in slug_to_chapters.items() if len(values) > 1}
    warned_slugs: set[str] = set()

    def rewrite_block(block: ChapterBlock) -> str:
        seen_duplicate_slugs: set[str] = set()

        def insert_anchor_before_headings(segment: str) -> str:
            out: list[str] = []
            in_fence = False
            fence_marker = ""
            for line in segment.splitlines(keepends=True):
                stripped = line.rstrip("\r\n")
                fence_match = re.match(r"^(```|~~~)", stripped)
                if fence_match:
                    marker = fence_match.group(1)
                    if not in_fence:
                        in_fence = True
                        fence_marker = marker
                    elif stripped.startswith(fence_marker):
                        in_fence = False
                        fence_marker = ""
                    out.append(line)
                    continue
                if in_fence:
                    out.append(line)
                    continue
                match = _HEADING_RE.match(stripped)
                if match and not match.group("id"):
                    slug = slugify(match.group("title").strip())
                    if slug in duplicate_title_slugs and slug not in seen_duplicate_slugs:
                        out.append(f"[]{{#{block.slug}-{slug}}}\n\n")
                        seen_duplicate_slugs.add(slug)
                out.append(line)
            return "".join(out)

        def rewrite_links(segment: str) -> str:
            def replace(match: re.Match[str]) -> str:
                dest = match.group("dest").strip()
                page, sep, anchor = dest.partition("#")
                if not sep:
                    return match.group(0)
                page_slug = Path(page).stem
                if page_slug not in chapter_slugs:
                    return match.group(0)
                if anchor in chapter_explicit_ids.get(page_slug, set()):
                    return f"[{match.group('text')}](#{anchor})"
                if anchor in chapter_title_slugs.get(page_slug, set()):
                    if anchor in duplicate_title_slugs:
                        if anchor not in warned_slugs:
                            warnings.warn(
                                f"slug collision for '{anchor}' across chapters; using '#{page_slug}-{anchor}'",
                                UserWarning,
                                stacklevel=2,
                            )
                            warned_slugs.add(anchor)
                        return f"[{match.group('text')}](#{page_slug}-{anchor})"
                    return f"[{match.group('text')}](#{anchor})"
                warnings.warn(
                    f"unresolved manual link target '{dest}'",
                    UserWarning,
                    stacklevel=2,
                )
                return match.group("text")

            return _INLINE_LINK_RE.sub(replace, segment)

        transformed = _transform_outside_fenced_code(block.text, insert_anchor_before_headings)
        transformed = _transform_outside_fenced_code(transformed, rewrite_links)
        return transformed

    result = "".join(rewrite_block(block) for block in blocks)
    if text.endswith("\n") and not result.endswith("\n"):
        result += "\n"
    return result
