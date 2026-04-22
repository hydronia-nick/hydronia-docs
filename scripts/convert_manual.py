"""Convert Hydronia manual source markdown into MkDocs chapter pages."""

from __future__ import annotations

import argparse
import html
import re
import shutil
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts import pandoc_preprocess as preprocess


REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_ROOT = REPO_ROOT / "docs"

REFERENCE_SOURCE_ROOT = Path(
    r"E:/Hydronia Dropbox/Nick Calero/Manuals/QGIS_Plugin_Reference_Manual_Latex"
)
REFERENCE_MD_DIR = REFERENCE_SOURCE_ROOT / "markdown_output"
REFERENCE_IMAGES_DIR = REFERENCE_SOURCE_ROOT / "images"

TUTORIAL_SOURCE_ROOT = Path(r"E:/Hydronia Dropbox/Nick Calero/Manuals/Rf2D-QGIS_Tutorial_Files")
TUTORIAL_MD_DIR = TUTORIAL_SOURCE_ROOT / "docs"
TUTORIAL_IMAGES_DIR = TUTORIAL_SOURCE_ROOT / "images"
TUTORIAL_IMAGES_PV_DIR = TUTORIAL_SOURCE_ROOT / "imagesParaview"

LABEL_TOKEN = r"[A-Za-z][\w:/+-]*"


@dataclass(frozen=True)
class ManualSpec:
    source_path: Path
    product_slug: str
    product_name: str
    subtitle: str
    output_subdir: str
    kind: str
    image_roots: dict[str, Path]
    chapter_slug_map: dict[str, str] | None = None
    chapter_title_overrides: dict[str, str] | None = None
    start_title: str | None = None
    require_labeled_h1: bool = False
    generate_index: bool = False


@dataclass
class ManualResult:
    product_slug: str
    output_subdir: str
    chapters: list[dict[str, str]]
    page_slugs: list[str]
    image_count: int


REFERENCE_CHAPTER_SLUGS = {
    "chap:new_project": "new-project",
    "cha:export_tool": "export",
    "chap:export_tool": "export",
    "chap:mapping_tools": "maps",
    "chap:animation_tool": "animation",
    "chap:cross_sections_tool": "cross-sections",
    "chap:tools": "tools",
    "chap:hydronia_tools_context_menus": "context-menus",
    "chap:appendix_i": "appendix",
}

REFERENCE_CHAPTER_TITLES = {
    "new-project": "New Project / Scenario Tool",
    "export": "Export Tools",
    "maps": "Results vs Time Mapping Tools",
    "animation": "Animation Tool",
    "cross-sections": "Cross Sections Tool",
    "tools": "Tools",
    "context-menus": "Hydronia Tools Context Menus",
    "appendix": "Appendix: QGIS Plugin Layer Attributes Reference",
}

REFERENCE_SPECS = [
    ManualSpec(
        source_path=REFERENCE_MD_DIR / "RF2D_Plugin_Manual_EN.md",
        product_slug="riverflow2d",
        product_name="RiverFlow2D",
        subtitle="Two-Dimensional Flood and River Dynamics Model",
        output_subdir="qgis-reference",
        kind="qgis-reference",
        image_roots={"images": REFERENCE_IMAGES_DIR},
        chapter_slug_map=REFERENCE_CHAPTER_SLUGS,
        chapter_title_overrides=REFERENCE_CHAPTER_TITLES,
        require_labeled_h1=True,
    ),
    ManualSpec(
        source_path=REFERENCE_MD_DIR / "OF2D_Plugin_Manual_EN.md",
        product_slug="oilflow2d",
        product_name="OilFlow2D",
        subtitle="Oil Spill Modeling for Land and Water",
        output_subdir="qgis-reference",
        kind="qgis-reference",
        image_roots={"images": REFERENCE_IMAGES_DIR},
        chapter_slug_map=REFERENCE_CHAPTER_SLUGS,
        chapter_title_overrides={
            "new-project": "New Project / Scenario Tool",
            "export": "Export Tools",
            "maps": "Results vs Time Mapping Tools",
            "animation": "Animation Tool",
            "cross-sections": "Cross Sections Tool",
            "tools": "Tools",
            "context-menus": "Hydronia Tools Context Menus",
            "appendix": "Appendix: QGIS Plugin Layer Attributes Reference",
        },
        require_labeled_h1=True,
    ),
    ManualSpec(
        source_path=REFERENCE_MD_DIR / "HBF_Plugin_Manual_EN.md",
        product_slug="hydrobid-flood",
        product_name="HydroBID Flood",
        subtitle="IDB Flood Mitigation and Urban Drainage Edition",
        output_subdir="qgis-reference",
        kind="qgis-reference",
        image_roots={"images": REFERENCE_IMAGES_DIR},
        chapter_slug_map=REFERENCE_CHAPTER_SLUGS,
        chapter_title_overrides=REFERENCE_CHAPTER_TITLES,
        require_labeled_h1=True,
    ),
]

TUTORIAL_SPECS = [
    ManualSpec(
        source_path=TUTORIAL_MD_DIR / "RF2D_Tutorial_EN.md",
        product_slug="riverflow2d",
        product_name="RiverFlow2D",
        subtitle="Two-Dimensional Flood and River Dynamics Model",
        output_subdir="tutorials",
        kind="tutorials",
        image_roots={
            "images": TUTORIAL_IMAGES_DIR,
            "imagesparaview": TUTORIAL_IMAGES_PV_DIR,
        },
        start_title="Introduction",
        generate_index=True,
    ),
    ManualSpec(
        source_path=TUTORIAL_MD_DIR / "OF2D_Tutorial_EN.md",
        product_slug="oilflow2d",
        product_name="OilFlow2D",
        subtitle="Oil Spill Model",
        output_subdir="tutorials",
        kind="tutorials",
        image_roots={
            "images": TUTORIAL_IMAGES_DIR,
            "imagesparaview": TUTORIAL_IMAGES_PV_DIR,
        },
        start_title="Introduction",
        generate_index=True,
    ),
    ManualSpec(
        source_path=TUTORIAL_MD_DIR / "HBF_Tutorial_EN.md",
        product_slug="hydrobid-flood",
        product_name="HydroBID Flood",
        subtitle="Flood Modeling System",
        output_subdir="tutorials",
        kind="tutorials",
        image_roots={
            "images": TUTORIAL_IMAGES_DIR,
            "imagesparaview": TUTORIAL_IMAGES_PV_DIR,
        },
        start_title="Introduction",
        generate_index=True,
    ),
]

ALL_SPECS = [*REFERENCE_SPECS, *TUTORIAL_SPECS]


H1_RE = re.compile(rf"^# (?P<title>.+?)(?:\s*\{{#(?P<label>{LABEL_TOKEN})\}})?\s*$")
HEADING_RE = re.compile(
    rf"^(?P<hashes>#{1,6})\s+(?P<title>.+?)(?:\s*\{{#(?P<label>{LABEL_TOKEN})\}})?\s*$",
    re.MULTILINE,
)

FIGURE_RE = re.compile(
    # Leading indent (empty when the block is at col 0 / not inside a list).
    # Capturing it here lets _figure_sub re-apply it to the emitted image so
    # the image stays as a list-item continuation rather than escaping to
    # top-level.
    rf'(?P<indent>^[ \t]*)'
    rf'<figure[^>]*>\s*'
    rf'<span class="image placeholder"\s+'
    rf'data-original-image-src="(?P<folder>images(?:Paraview)?)/(?P<src>[^"]+)"'
    rf'[^>]*></span>\s*'
    # Figcaption is OPTIONAL. Captionless figures are common for toolbar-
    # button screenshots inserted inline in lists; without this branch they
    # slip through as raw HTML and Pandoc renders the image at natural
    # resolution (a tiny icon blown up to fill the page).
    rf"(?:<figcaption>(?P<cap>.*?)</figcaption>\s*)?"
    rf"</figure>",
    re.DOTALL | re.IGNORECASE | re.MULTILINE,
)

INLINE_IMG_RE = re.compile(
    r'\[image\]\{\.image \.placeholder\s+'
    r'original-image-src="(?P<folder>images(?:Paraview)?)/(?P<src>[^"]+)"'
    r'[^}]*\}',
    re.DOTALL,
)

GENERIC_IMG_RE = re.compile(rf"(?P<folder>images(?:Paraview)?)/(?P<src>[^\s)\"]+)")
HEADER_ATTR_RE = re.compile(r"^(#{1,6} .*?)\s*\{#[^}]+\}\s*$", re.MULTILINE)
XREF_TRAILER_RE = re.compile(r'\{reference-type="[^"]*"\s+reference="[^"]*"\}')
INLINE_LINK_RE = re.compile(rf"\[(?P<text>[^\]]*)\]\(#(?P<label>{LABEL_TOKEN})\)")
WWW_LINK_RE = re.compile(r"\]\((www\.[^) \t\r\n]+)\)")
BARE_WWW_LINK_RE = re.compile(r"\]\((www\.[^)]+)\)")

WIDTH_ATTR_RE = re.compile(r'width="([^"]+)"')
HEIGHT_ATTR_RE = re.compile(r'height="([^"]+)"')

_INLINE_IMG_WIDTH_RE = re.compile(
    r"!\[[^\]]*\]\([^)]+\)\s*\{[^}]*\bwidth\s*=\s*(?P<w>\d+)%[^}]*\}"
)
_LIST_ITEM_MARKER_RE = re.compile(r"^(?P<indent>\s*)(?:\d+\.\s+|[-*+]\s+)")
_LARGE_IMAGE_WIDTH_THRESHOLD = 15

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[\"'(\[]?[A-Z0-9])")


def slugify(text: str) -> str:
    text = re.sub(r"[\\/]+", " ", text)
    text = normalize_source_text(text)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text).strip("-")
    return text


def normalize_source_text(text: str) -> str:
    return text.replace("\u00c2\u00a0", " ").replace("\xa0", " ")


def split_chapters(
    text: str,
    *,
    start_title: str | None = None,
    require_labeled_h1: bool = False,
) -> list[dict[str, str]]:
    """Split a manual source into chapter blocks."""

    lines = text.splitlines(keepends=True)
    chapters: list[dict[str, str]] = []
    current: dict[str, Any] | None = None
    started = start_title is None and not require_labeled_h1

    for line in lines:
        match = H1_RE.match(line.rstrip("\r\n"))
        if match:
            title = re.sub(
                r"\s+",
                " ",
                normalize_source_text(match.group("title").strip()),
            ).strip()
            label = match.group("label")
            if not started:
                if start_title is not None and title == start_title:
                    started = True
                elif require_labeled_h1 and label:
                    started = True
                else:
                    continue
            if current is not None:
                chapters.append(current)
            current = {"title": title, "label": label or "", "body": []}
            continue
        if started and current is not None:
            current["body"].append(line)

    if current is not None:
        chapters.append(current)

    for chapter in chapters:
        chapter["body"] = "".join(chapter["body"])
    return chapters


def build_label_map(
    chapters: list[dict[str, str]],
    *,
    page_slug_for_chapter,
    map_unlabeled_h1_to_page_slug: bool = False,
) -> dict[str, tuple[str, str]]:
    mapping: dict[str, tuple[str, str]] = {}
    for chapter in chapters:
        page_slug = page_slug_for_chapter(chapter)
        if page_slug is None:
            continue
        title_slug = slugify(chapter["title"])
        label = chapter.get("label") or ""
        if label:
            mapping[label] = (page_slug, "")
        elif map_unlabeled_h1_to_page_slug and title_slug:
            mapping[title_slug] = (page_slug, "")

        for heading in HEADING_RE.finditer(chapter["body"]):
            heading_label = heading.group("label")
            if not heading_label:
                continue
            heading_title = heading.group("title").strip()
            mapping[heading_label] = (page_slug, slugify(heading_title))
    return mapping


_LEADING_DOT_DIM_RE = re.compile(r"^(\.)(\d)")
# `\textwidth`, `0.8\textwidth`, etc. — LaTeX-isms Pandoc's attribute parser
# drops silently. Coerce to percentage form so Pandoc emits real widths.
_TEXTWIDTH_SCALED_RE = re.compile(r"^(\d+(?:\.\d+)?)\\textwidth$")
_TEXTWIDTH_PLAIN_RE = re.compile(r"^\\textwidth$")


def _normalize_dim(value: str) -> str:
    # Pandoc's markdown attribute parser silently drops width/height values
    # that don't match its numeric-unit grammar. The LaTeX Gin fallback
    # then takes over — which used to blow small icons up to line width
    # and now (since we ship the \maxwidth idiom) lets large screenshots
    # render at natural DPI and overflow the page. Either way, dropped
    # widths are a bug we want to prevent at the source.
    #
    # Known Pandoc-hostile patterns found in Hydronia manuals:
    #   `.6cm`          → `0.6cm`   (leading-dot)
    #   `\textwidth`    → `100%`
    #   `0.8\textwidth` → `80%`     (fractional-textwidth)
    value = _LEADING_DOT_DIM_RE.sub(r"0.\2", value)
    m = _TEXTWIDTH_SCALED_RE.match(value)
    if m:
        return f"{int(round(float(m.group(1)) * 100))}%"
    if _TEXTWIDTH_PLAIN_RE.match(value):
        return "100%"
    return value


def _extract_dimensions(match: re.Match[str]) -> dict[str, str]:
    text = match.group(0)
    dims: dict[str, str] = {}
    width = WIDTH_ATTR_RE.search(text)
    height = HEIGHT_ATTR_RE.search(text)
    if width:
        dims["width"] = _normalize_dim(width.group(1))
    if height:
        dims["height"] = _normalize_dim(height.group(1))
    return dims


def _format_dim_attrs(dims: dict[str, str]) -> str:
    if not dims:
        return ""
    return "{ " + " ".join(f"{k}={v}" for k, v in dims.items()) + " }"


def _clean_caption(text: str | None) -> str:
    # FIGURE_RE's figcaption group is optional; a captionless figure block
    # returns None here.
    if text is None:
        return ""
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text)
    return normalize_source_text(text).strip()


def _resolve_image_source(
    folder: str, src: str, image_roots: dict[str, Path]
) -> Path:
    root = image_roots.get(folder.lower())
    if root is None:
        raise FileNotFoundError(f"Unsupported image source folder: {folder}")
    candidate = root / src
    if candidate.is_file():
        return candidate

    requested = Path(src)
    requested_name = requested.name.lower()
    requested_stem = requested.stem.lower()

    exact_matches: list[Path] = []
    stem_matches: list[Path] = []
    for item in root.iterdir():
        if not item.is_file():
            continue
        name_lower = item.name.lower()
        if name_lower == requested_name:
            exact_matches.append(item)
        elif item.stem.lower() == requested_stem:
            stem_matches.append(item)

    if len(exact_matches) == 1:
        return exact_matches[0]
    if len(exact_matches) > 1:
        raise FileNotFoundError(
            f"Ambiguous image reference {src!r} in {folder}: "
            + ", ".join(str(path) for path in exact_matches)
        )
    if len(stem_matches) == 1:
        return stem_matches[0]
    if len(stem_matches) > 1:
        raise FileNotFoundError(
            f"Ambiguous image reference {src!r} in {folder}: "
            + ", ".join(str(path) for path in stem_matches)
        )

    return candidate


def _record_image(
    image_sources: dict[str, Path],
    image_roots: dict[str, Path],
    folder: str,
    src: str,
) -> str:
    # Tutorial source has images nested in sub-folders (e.g.
    # images/multiscenarioproject/image4.png and
    # images/SimulatingPollutants/image4.png) where a bare filename
    # collides. Flatten the nested path into the destination name so the
    # per-product img/ dir keeps every screenshot unique.
    src_path = Path(src)
    parts = [p for p in src_path.parts if p not in (".", "..")]
    if len(parts) > 1:
        # Join the subdir + filename with underscores, preserve extension.
        stem = "_".join(parts[:-1] + [src_path.stem])
        dest_name = f"{stem}{src_path.suffix}".lower()
    else:
        dest_name = src_path.name.lower()
    source_path = _resolve_image_source(folder, src, image_roots)
    existing = image_sources.get(dest_name)
    if existing is not None and existing != source_path:
        raise ValueError(
            f"image destination collision for {dest_name!r}: {existing} vs {source_path}"
        )
    image_sources[dest_name] = source_path
    return dest_name


def _figure_sub(
    match: re.Match[str], image_roots: dict[str, Path], image_sources: dict[str, Path]
) -> str:
    folder = match.group("folder")
    src = match.group("src")
    dest_name = _record_image(image_sources, image_roots, folder, src)
    caption = _clean_caption(match.group("cap"))
    attrs = _format_dim_attrs(_extract_dimensions(match))
    # Preserve the source line's leading indent — when the figure block is
    # nested inside a numbered list item (`    <figure>...`), the generated
    # markdown image must keep the same indent so Pandoc treats it as list
    # continuation rather than a sibling paragraph.
    indent = match.groupdict().get("indent") or ""
    return f"\n{indent}![{caption}](img/{dest_name}){attrs}\n"


def _inline_img_sub(
    match: re.Match[str], image_roots: dict[str, Path], image_sources: dict[str, Path]
) -> str:
    folder = match.group("folder")
    src = match.group("src")
    dest_name = _record_image(image_sources, image_roots, folder, src)
    attrs = _format_dim_attrs(_extract_dimensions(match))
    return f"![](img/{dest_name}){attrs}"


def _generic_img_sub(
    match: re.Match[str], image_roots: dict[str, Path], image_sources: dict[str, Path]
) -> str:
    folder = match.group("folder")
    src = match.group("src")
    dest_name = _record_image(image_sources, image_roots, folder, src)
    return f"img/{dest_name}"


def _rewrite_xref_links(
    body: str, label_map: dict[str, tuple[str, str]], this_page: str
) -> str:
    """Rewrite anchor-style links to chapter page links when possible."""

    def sub(match: re.Match[str]) -> str:
        label = match.group("label")
        text = match.group("text")
        if label.startswith(("fig:", "tab:")):
            return text
        target = label_map.get(label)
        if target is None:
            return text
        page_slug, heading_slug = target
        if page_slug == this_page:
            if heading_slug:
                return f"[{text}](#{heading_slug})"
            return text
        suffix = f"#{heading_slug}" if heading_slug else ""
        return f"[{text}]({page_slug}.md{suffix})"

    return INLINE_LINK_RE.sub(sub, body)


def _rewrite_bare_web_links(body: str) -> str:
    return BARE_WWW_LINK_RE.sub(lambda match: f"](https://{match.group(1)})", body)


def _split_large_trailing_inline_images(body: str) -> str:
    """Move large images from trailing list-item text to their own paragraph.

    Only rewrites lines where the image is truly trailing inline — i.e.
    the line has other text before the image. Lines that are already an
    image on its own (possibly indented for list-continuation) are left
    alone, because re-processing them would strip the indent and make the
    image escape the list.
    """
    new_lines: list[str] = []
    for line in body.split("\n"):
        matches = list(_INLINE_IMG_WIDTH_RE.finditer(line))
        if not matches:
            new_lines.append(line)
            continue
        last = matches[-1]
        width = int(last.group("w"))
        trailing = line[last.end():].strip()
        preceding = line[: last.start()].strip()
        # Preceding empty means the image is already on its own line —
        # respect the line's existing indent and skip.
        if not preceding:
            new_lines.append(line)
            continue
        if trailing or width <= _LARGE_IMAGE_WIDTH_THRESHOLD:
            new_lines.append(line)
            continue
        marker = _LIST_ITEM_MARKER_RE.match(line)
        indent = " " * len(marker.group(0)) if marker else ""
        before_img = line[: last.start()].rstrip()
        new_lines.append(before_img)
        new_lines.append("")
        new_lines.append(f"{indent}{last.group(0)}")
    return "\n".join(new_lines)


def clean_body(
    body: str,
    label_map: dict[str, tuple[str, str]],
    this_page: str,
    image_roots: dict[str, Path],
    image_sources: dict[str, Path],
) -> str:
    body = normalize_source_text(body)
    body = preprocess.strip_frontmatter(body)
    body = preprocess.neutralize_raw_figure_blocks(body)
    body = preprocess.strip_cross_doc_links(body)
    body = preprocess.unescape_pandoc_quotes(body)
    body = FIGURE_RE.sub(
        lambda match: _figure_sub(match, image_roots, image_sources),
        body,
    )
    body = INLINE_IMG_RE.sub(
        lambda match: _inline_img_sub(match, image_roots, image_sources),
        body,
    )
    body = XREF_TRAILER_RE.sub("", body)
    body = _rewrite_xref_links(body, label_map, this_page)
    body = _rewrite_bare_web_links(body)
    body = HEADER_ATTR_RE.sub(r"\1", body)
    body = GENERIC_IMG_RE.sub(
        lambda match: _generic_img_sub(match, image_roots, image_sources),
        body,
    )
    body = WWW_LINK_RE.sub(r"](https://\1)", body)
    body = _split_large_trailing_inline_images(body)
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body.strip() + "\n"


def chapter_summary(body: str) -> str:
    body = normalize_source_text(body)
    body = preprocess.strip_frontmatter(body)
    body = preprocess.neutralize_raw_figure_blocks(body)
    body = preprocess.strip_cross_doc_links(body)
    body = preprocess.unescape_pandoc_quotes(body)

    current: list[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped:
            if current:
                sentence = first_sentence(" ".join(current))
                if sentence:
                    return sentence
                current = []
            continue
        if re.match(r"^(#{1,6}\s+|!\[|<figure\b|:::|>\s*|\|\s*|-+\s*$|\d+[.)]\s+)", stripped):
            if current:
                sentence = first_sentence(" ".join(current))
                if sentence:
                    return sentence
                current = []
            continue
        current.append(stripped)

    if current:
        sentence = first_sentence(" ".join(current))
        if sentence:
            return sentence
    return ""


def strip_inline_markdown(text: str) -> str:
    text = normalize_source_text(text)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)(?:\{[^}]*\})?", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def first_sentence(text: str) -> str:
    text = strip_inline_markdown(text)
    if not text:
        return ""
    parts = _SENTENCE_SPLIT_RE.split(text, 1)
    return parts[0].strip()


def page_slug_for_chapter(spec: ManualSpec, chapter: dict[str, str]) -> str | None:
    if spec.chapter_slug_map is not None:
        label = chapter.get("label") or ""
        return spec.chapter_slug_map.get(label)
    return slugify(chapter["title"])


def page_title_for_chapter(spec: ManualSpec, chapter: dict[str, str], page_slug: str) -> str:
    if spec.chapter_title_overrides is not None:
        title = spec.chapter_title_overrides.get(page_slug)
        if title:
            return re.sub(r"\s+", " ", normalize_source_text(title)).strip()
    return re.sub(r"\s+", " ", normalize_source_text(chapter["title"])).strip()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def remove_stale_markdown_files(out_dir: Path, keep: set[str]) -> None:
    for path in out_dir.glob("*.md"):
        if path.stem not in keep:
            path.unlink()
    for path in out_dir.glob("*.markdown"):
        if path.stem not in keep:
            path.unlink()


def copy_referenced_images(image_sources: dict[str, Path], img_dir: Path) -> int:
    """Copy source images into the destination ``img/`` directory.

    PNG copies are routed through Pillow so we can strip DPI metadata.
    Some tutorial screenshots were saved with DPI ≈ 0.99 (looks like a
    pt-vs-px confusion in the original toolchain); XeLaTeX's graphics
    package reads that DPI to compute the physical size of the image for
    aspect-ratio math and throws ``Package graphics Error: Division by 0``
    when it evaluates absurdly close to zero. Pillow lets us strip the
    pHYs chunk entirely so the graphics driver falls back to a sane
    default (72 DPI).
    """
    try:
        from PIL import Image  # local import so non-PNG users don't need Pillow
    except Exception:  # pragma: no cover - Pillow is a hard dep today
        Image = None  # type: ignore[assignment]

    img_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    missing: list[Path] = []
    for dest_name, source_path in sorted(image_sources.items()):
        if not source_path.is_file():
            missing.append(source_path)
            continue
        dest_path = img_dir / dest_name
        ext = source_path.suffix.lower()
        if Image is not None and ext == ".png":
            try:
                with Image.open(source_path) as im:
                    im.load()
                    # Downsample oversized screenshots so the generated PDF
                    # stays well under GitHub Pages' 100 MB per-file cap.
                    # Tutorial sources ship 2200x1750+ PNGs; ~1600 px on
                    # the long edge is plenty for a PDF rendered at 96 DPI.
                    MAX_EDGE = 1600
                    w, h = im.size
                    longest = max(w, h)
                    if longest > MAX_EDGE:
                        ratio = MAX_EDGE / longest
                        im = im.resize(
                            (round(w * ratio), round(h * ratio)),
                            Image.LANCZOS,
                        )
                    # UI screenshots (the bulk of tutorial content) are
                    # flat-colour diagrams that compress ~4x smaller as
                    # 256-colour palette PNG than as RGB PNG. Photographic
                    # imagery keeps full colour depth. Heuristic: if the
                    # image has <= 256 unique colours, palettise. For
                    # RGBA/alpha images we stay 24-bit to preserve the
                    # channel.
                    has_alpha = im.mode in ("RGBA", "LA") or (
                        im.mode == "P" and "transparency" in im.info
                    )
                    if not has_alpha:
                        if im.mode != "RGB":
                            im = im.convert("RGB")
                        try:
                            # getcolors returns None if unique colours >
                            # maxcolors. 256 is the palette-PNG ceiling.
                            if im.getcolors(maxcolors=256) is not None:
                                im = im.convert("P", palette=Image.ADAPTIVE, colors=256)
                            else:
                                # Many colours (photo, gradient, rendered
                                # visualisation) — quantise to 256 anyway;
                                # screenshot-heavy docs tolerate the loss.
                                im = im.quantize(colors=256, method=Image.FASTOCTREE)
                        except Exception:
                            pass  # keep original mode on failure
                    # Re-save WITHOUT the info dict (drops pHYs DPI chunk)
                    # and with PNG-level optimization enabled.
                    im.save(dest_path, format="PNG", optimize=True)
            except Exception:
                # Pillow failed — fall back to byte-level copy so we never
                # silently drop an image.
                shutil.copy2(source_path, dest_path)
        else:
            shutil.copy2(source_path, dest_path)
        count += 1
    if missing:
        missing_text = "\n".join(f"  {path}" for path in missing)
        raise FileNotFoundError(f"Missing source image(s):\n{missing_text}")
    return count


def render_tutorial_index(spec: ManualSpec, chapter_entries: list[dict[str, str]]) -> str:
    lines = [
        "---",
        f"title: {spec.product_name} Tutorials",
        "---",
        "",
        f"# {spec.product_name} Tutorials",
        "",
        f"**{spec.subtitle}**",
        "",
        "Hands-on tutorial chapters in source order.",
        "",
        "## Tutorial chapters",
        "",
        "Chapters follow the order of the source tutorial.",
        "",
    ]
    for number, chapter in enumerate(chapter_entries, start=1):
        summary = chapter.get("summary") or "Summary unavailable."
        lines.append(
            f"{number}. [{chapter['title']}]({chapter['slug']}.md) - {summary}"
        )
    lines.append("")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def process_manual(spec: ManualSpec) -> ManualResult:
    if not spec.source_path.exists():
        raise FileNotFoundError(spec.source_path)

    text = spec.source_path.read_text(encoding="utf-8")
    chapters = split_chapters(
        text,
        start_title=spec.start_title,
        require_labeled_h1=spec.require_labeled_h1,
    )
    if not chapters:
        raise ValueError(f"No chapters found in {spec.source_path}")

    page_slug_for = lambda chapter: page_slug_for_chapter(spec, chapter)
    label_map = build_label_map(
        chapters,
        page_slug_for_chapter=page_slug_for,
        map_unlabeled_h1_to_page_slug=spec.kind == "tutorials",
    )

    out_dir = DOCS_ROOT / spec.product_slug / spec.output_subdir
    img_dir = out_dir / "img"
    out_dir.mkdir(parents=True, exist_ok=True)
    img_dir.mkdir(parents=True, exist_ok=True)

    chapter_entries: list[dict[str, str]] = []
    image_sources: dict[str, Path] = {}

    for chapter in chapters:
        page_slug = page_slug_for(chapter)
        if page_slug is None:
            continue
        title = page_title_for_chapter(spec, chapter, page_slug)
        body = clean_body(
            chapter["body"],
            label_map,
            page_slug,
            spec.image_roots,
            image_sources,
        )
        page_path = out_dir / f"{page_slug}.md"
        write_text(page_path, f"# {title}\n\n{body}")
        chapter_entries.append(
            {
                "slug": page_slug,
                "title": title,
                "summary": chapter_summary(chapter["body"]),
            }
        )

    image_count = copy_referenced_images(image_sources, img_dir)

    manual_pages = [entry["slug"] for entry in chapter_entries]
    if spec.generate_index:
        index_text = render_tutorial_index(spec, chapter_entries)
        write_text(out_dir / "index.md", index_text)
        manual_pages = ["index", *manual_pages]

    remove_stale_markdown_files(out_dir, set(manual_pages) | {"index"})

    return ManualResult(
        product_slug=spec.product_slug,
        output_subdir=spec.output_subdir,
        chapters=chapter_entries,
        page_slugs=manual_pages,
        image_count=image_count,
    )


def print_result(spec: ManualSpec, result: ManualResult) -> None:
    manual_label = f"{spec.product_slug}/{spec.output_subdir}"
    print(
        f"[{manual_label}] pages={len(result.page_slugs)} "
        f"images={result.image_count}"
    )
    print(f"  chapters: {', '.join(result.page_slugs)}")
    if spec.generate_index:
        print(
            f"  tutorial entries: {len(result.chapters)} "
            f"(index + {len(result.chapters)} chapter files)"
        )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert Hydronia manual source markdown into MkDocs pages."
    )
    parser.add_argument(
        "mode",
        nargs="?",
        choices=("all", "reference", "tutorials"),
        default="all",
        help="Which manual set to generate.",
    )
    return parser.parse_args(argv)


def specs_for_mode(mode: str) -> list[ManualSpec]:
    if mode == "reference":
        return REFERENCE_SPECS
    if mode == "tutorials":
        return TUTORIAL_SPECS
    return ALL_SPECS


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    for spec in specs_for_mode(args.mode):
        result = process_manual(spec)
        print_result(spec, result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
