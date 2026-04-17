"""Convert Pandoc-derived per-product manual markdown into MkDocs chapter pages.

Reads:
    E:/Hydronia Dropbox/.../markdown_output/{RF2D,OF2D,HBF}_Plugin_Manual_EN.md

Writes, per product, one chapter per file under docs/<product>/:
    new-project.md, export.md, maps.md, animation.md, cross-sections.md,
    tools.md, context-menus.md, appendix.md
and copies referenced images into docs/<product>/img/.

Transforms performed:
  * Pandoc <figure><span class="image placeholder"> ... blocks → standard
    markdown images `![caption](img/file.png){ width=W }`.
  * Inline [image]{.image .placeholder ...} spans → inline
    `![](img/file.png){ width=W }`.
  * Strip header attribute blocks `{#chap:xxx}`/`{#sec:xxx}`/etc.
  * Strip Pandoc cross-ref trailers `{reference-type="ref" reference="..."}`.
  * Rewrite anchor-only links `(#label)` to `(<chapter>.md#<slug>)` when the
    label resolves to a known heading in another chapter.
  * Fix image paths `images/FOO.png` → `img/FOO.png`.
  * Strip the front-matter/title/legal-notice section (everything before the
    first `# ... {#chap:...}` heading).

Run:  python scripts/convert_manual.py
"""

from __future__ import annotations

import re
import shutil
import sys
import unicodedata
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_ROOT = REPO_ROOT / "docs"

MANUAL_ROOT = Path(
    r"E:/Hydronia Dropbox/Nick Calero/Manuals/"
    r"QGIS_Plugin_Reference_Manual_Latex"
)
MD_DIR = MANUAL_ROOT / "markdown_output"
IMAGES_DIR = MANUAL_ROOT / "images"

PRODUCTS = [
    # (source markdown file, product docs slug, friendly name)
    ("RF2D_Plugin_Manual_EN.md", "riverflow2d", "RiverFlow2D"),
    ("OF2D_Plugin_Manual_EN.md", "oilflow2d", "OilFlow2D"),
    ("HBF_Plugin_Manual_EN.md", "hydrobid-flood", "HydroBID Flood"),
]

# Map Pandoc chapter label -> MkDocs page slug (without .md).
CHAPTER_SLUGS = {
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

# ---------------------------------------------------------------------------
# Slug helpers (must match MkDocs/Python-Markdown default slugify)
# ---------------------------------------------------------------------------

_SLUG_STRIP = re.compile(r"[^\w\s-]", re.UNICODE)
_SLUG_SPACE = re.compile(r"[\s_-]+")


def slugify(text: str) -> str:
    """Approximate the default MkDocs heading slug."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = text.lower().strip()
    text = _SLUG_STRIP.sub("", text)
    text = _SLUG_SPACE.sub("-", text).strip("-")
    return text


# ---------------------------------------------------------------------------
# Pandoc pattern transforms
# ---------------------------------------------------------------------------

# <figure id="..."><span class="image placeholder" data-original-image-src="images/X.png" data-original-image-title="" width="W%"></span><figcaption>CAP</figcaption></figure>
FIGURE_RE = re.compile(
    r"<figure[^>]*>\s*"
    r'<span class="image placeholder"\s+'
    r'data-original-image-src="images/(?P<src>[^"]+)"'
    r'[^>]*?'
    r'(?:\s+width="(?P<width>[^"]+)")?'
    r'[^>]*></span>\s*'
    r"<figcaption>(?P<cap>.*?)</figcaption>\s*"
    r"</figure>",
    re.DOTALL | re.IGNORECASE,
)

# Inline: [image]{.image .placeholder original-image-src="images/X.png" original-image-title="" width="W%"}
INLINE_IMG_RE = re.compile(
    r"\[image\]\{\.image \.placeholder\s+"
    r'original-image-src="images/(?P<src>[^"]+)"'
    r'[^}]*?'
    r'(?:\s+width="(?P<width>[^"]+)")?'
    r'[^}]*\}',
    re.DOTALL,
)

# Header attribute block at end of heading line: `## Heading {#sec:xxx}`
HEADER_ATTR_RE = re.compile(r"\s*\{#[a-zA-Z][\w:+-]*\}\s*$")

# Cross-ref trailer after a link: `[text](#anchor){reference-type="ref" reference="xxx"}`
XREF_TRAILER_RE = re.compile(r'\{reference-type="[^"]*"\s+reference="[^"]*"\}')

# `images/FOO.png` inside generic markdown link/image tags we missed
IMG_PATH_RE = re.compile(r"images/([^\s)\"]+)")


# ---------------------------------------------------------------------------
# Chapter split
# ---------------------------------------------------------------------------

CHAPTER_H1_RE = re.compile(r"^# (?P<title>.+?)\s*\{#(?P<label>[a-zA-Z][\w:+-]*)\}\s*$")


def split_chapters(text: str) -> list[dict]:
    """Return list of {label, title, body} dicts, in source order.

    Everything before the first labeled H1 is discarded (front matter, legal
    notice). H1 lines without an id attribute are also ignored.
    """
    lines = text.splitlines(keepends=True)
    chapters: list[dict] = []
    current: dict | None = None
    for line in lines:
        m = CHAPTER_H1_RE.match(line.rstrip("\n"))
        if m:
            if current is not None:
                chapters.append(current)
            current = {
                "label": m.group("label"),
                "title": m.group("title").strip(),
                "body": [],
            }
            continue
        if current is not None:
            current["body"].append(line)
    if current is not None:
        chapters.append(current)
    for c in chapters:
        c["body"] = "".join(c["body"])
    return chapters


# ---------------------------------------------------------------------------
# Label map (cross-reference resolution)
# ---------------------------------------------------------------------------

HEADING_LINE_RE = re.compile(
    r"^(?P<hashes>#{1,6})\s+(?P<title>.+?)\s*\{#(?P<label>[a-zA-Z][\w:+-]*)\}\s*$",
    re.MULTILINE,
)


def build_label_map(chapters: list[dict]) -> dict[str, tuple[str, str]]:
    """label -> (page_slug, heading_slug)."""
    mapping: dict[str, tuple[str, str]] = {}
    for chap in chapters:
        page = CHAPTER_SLUGS.get(chap["label"])
        if page is None:
            continue
        # Chapter itself points to page root.
        mapping[chap["label"]] = (page, "")
        for m in HEADING_LINE_RE.finditer(chap["body"]):
            label = m.group("label")
            title = m.group("title")
            mapping[label] = (page, slugify(title))
    return mapping


# ---------------------------------------------------------------------------
# Transformation pipeline
# ---------------------------------------------------------------------------


def _figure_sub(match: re.Match) -> str:
    src = match.group("src").lower()  # lowercase for case-sensitive deploy targets
    cap = match.group("cap").strip()
    # Caption may contain markdown/HTML; strip any stray whitespace/newlines.
    cap = re.sub(r"\s+", " ", cap)
    width = match.group("width")
    attrs = f"{{ width={width} }}" if width else ""
    return f"\n![{cap}](img/{src}){attrs}\n"


def _inline_img_sub(match: re.Match) -> str:
    src = match.group("src").lower()
    width = match.group("width")
    attrs = f"{{ width={width} }}" if width else ""
    return f"![](img/{src}){attrs}"


def _rewrite_xref_links(
    body: str, label_map: dict[str, tuple[str, str]], this_page: str
) -> str:
    """Rewrite `[text](#label)` to cross-page links where applicable.

    Pandoc-style `#fig:xxx` / `#tab:xxx` anchors do not exist in MkDocs, so
    we strip those links entirely and keep only the link text.
    Labels that resolve to a known heading are rewritten to point at that
    heading's page+slug.
    """
    full_link_re = re.compile(
        r"\[(?P<text>[^\]]*)\]\(#(?P<label>[a-zA-Z][\w:+-]*)\)"
    )

    def sub(m: re.Match) -> str:
        label = m.group("label")
        text = m.group("text")
        # Figure/table Pandoc anchors have no MkDocs target — strip link.
        if label.startswith(("fig:", "tab:")):
            return text
        target = label_map.get(label)
        if target is None:
            # Unknown label — drop the dead anchor, keep text.
            return text
        page, heading = target
        if page == this_page:
            anchor = f"#{heading}" if heading else ""
            return f"[{text}]({anchor})" if anchor else text
        suffix = f"#{heading}" if heading else ""
        return f"[{text}]({page}.md{suffix})"

    return full_link_re.sub(sub, body)


def clean_body(
    body: str, label_map: dict[str, tuple[str, str]], this_page: str
) -> str:
    # 1. Figure blocks → markdown images.
    body = FIGURE_RE.sub(_figure_sub, body)
    # 2. Inline [image]{...} spans.
    body = INLINE_IMG_RE.sub(_inline_img_sub, body)
    # 3. Remove Pandoc cross-ref trailers.
    body = XREF_TRAILER_RE.sub("", body)
    # 4. Rewrite cross-page link anchors.
    body = _rewrite_xref_links(body, label_map, this_page)
    # 5. Strip header-attr blocks from the ends of heading lines.
    body = re.sub(
        r"^(#{1,6} .*?)\s*\{#[a-zA-Z][\w:+-]*\}\s*$",
        r"\1",
        body,
        flags=re.MULTILINE,
    )
    # 6. Any stray `images/X.png` references → `img/x.png` (lowercased).
    body = IMG_PATH_RE.sub(lambda m: f"img/{m.group(1).lower()}", body)
    # 7. Collapse 3+ blank lines to 2.
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body.strip() + "\n"


# ---------------------------------------------------------------------------
# Image collection
# ---------------------------------------------------------------------------

MD_IMG_REF_RE = re.compile(r"]\(img/([^)\s]+)\)")


def collect_image_refs(text: str) -> set[str]:
    return set(MD_IMG_REF_RE.findall(text))


# ---------------------------------------------------------------------------
# Per-chapter intro text (top of page, above first section)
# ---------------------------------------------------------------------------

CHAPTER_H1_TITLES = {
    "new-project": "New Project / Scenario Tool",
    "export": "Export Tools",
    "maps": "Results vs Time Mapping Tools",
    "animation": "Animation Tool",
    "cross-sections": "Cross Sections Tool",
    "tools": "Tools",
    "context-menus": "Hydronia Tools Context Menus",
    "appendix": "Appendix: QGIS Plugin Layer Attributes Reference",
}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def process_product(md_filename: str, product_slug: str, product_name: str) -> dict:
    src = MD_DIR / md_filename
    if not src.exists():
        raise FileNotFoundError(src)

    text = src.read_text(encoding="utf-8")
    chapters = split_chapters(text)
    label_map = build_label_map(chapters)

    out_dir = DOCS_ROOT / product_slug
    img_dir = out_dir / "img"
    img_dir.mkdir(parents=True, exist_ok=True)

    written_pages: list[str] = []
    missing_images: list[str] = []
    all_img_refs: set[str] = set()

    for chap in chapters:
        page_slug = CHAPTER_SLUGS.get(chap["label"])
        if page_slug is None:
            print(f"[{product_slug}] skip unknown chapter label: {chap['label']}")
            continue
        title = CHAPTER_H1_TITLES.get(page_slug, chap["title"])
        cleaned = clean_body(chap["body"], label_map, page_slug)
        page_text = f"# {title}\n\n{cleaned}"
        out_file = out_dir / f"{page_slug}.md"
        out_file.write_text(page_text, encoding="utf-8")
        written_pages.append(page_slug)
        all_img_refs |= collect_image_refs(page_text)

    # Copy referenced images. Destination name is always lowercase so
    # markdown refs resolve on case-sensitive filesystems (GitHub Pages).
    candidates = list(IMAGES_DIR.glob("*"))
    by_lower = {c.name.lower(): c for c in candidates}
    for img_name in sorted(all_img_refs):
        key = img_name.lower()
        src_img = by_lower.get(key)
        if src_img is None:
            missing_images.append(img_name)
            continue
        dst_img = img_dir / key
        shutil.copyfile(src_img, dst_img)

    return {
        "product": product_slug,
        "pages": written_pages,
        "image_count": len(all_img_refs),
        "missing_images": missing_images,
    }


def remove_stale_files(product_slug: str) -> None:
    """Remove chapter pages that are no longer generated."""
    out_dir = DOCS_ROOT / product_slug
    keep = set(CHAPTER_SLUGS.values()) | {"index"}
    for md in out_dir.glob("*.md"):
        if md.stem not in keep:
            print(f"[{product_slug}] remove stale: {md.name}")
            md.unlink()


def main() -> int:
    for md_name, slug, pretty in PRODUCTS:
        info = process_product(md_name, slug, pretty)
        remove_stale_files(slug)
        print(
            f"[{info['product']}] pages={len(info['pages'])} "
            f"images={info['image_count']} missing={len(info['missing_images'])}"
        )
        for miss in info["missing_images"]:
            print(f"    MISSING: {miss}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
