from __future__ import annotations

from pathlib import Path

import pytest

from scripts.pandoc_preprocess import (
    neutralize_raw_figure_blocks,
    rewrite_cross_chapter_links,
    strip_cross_doc_links,
    strip_frontmatter,
    unescape_pandoc_quotes,
)


ANIMATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "docs"
    / "riverflow2d"
    / "qgis-reference"
    / "animation.md"
)


def animation_lines() -> list[str]:
    return ANIMATION_PATH.read_text(encoding="utf-8").splitlines()


def test_strip_frontmatter_removes_leading_yaml() -> None:
    lines = animation_lines()
    text = "---\ntitle: Demo\n---\n" + "\n".join(lines[:4]) + "\n"

    result = strip_frontmatter(text)

    assert result.startswith("# Animation Tool")
    assert "title: Demo" not in result


def test_neutralize_raw_figure_blocks_replaces_caption_only_figure() -> None:
    text = "\n".join(
        [
            "## Export KMZ Dialog",
            "<figure id=\"fig:animation_export_kmz\">",
            "",
            "<figcaption>Export KMZ Dialog</figcaption>",
            "</figure>",
        ]
    )

    result = neutralize_raw_figure_blocks(text)

    assert "**Export KMZ Dialog**" in result
    assert "<figure" not in result


def test_unescape_pandoc_quotes_leaves_fenced_code_blocks() -> None:
    lines = animation_lines()
    quoted_line = next(line for line in lines if '\\"All times\\"' in line)
    ellipsis_line = next(line for line in lines if "\\..." in line)
    text = "\n".join(
        [
            quoted_line,
            "",
            ellipsis_line,
            "",
            "```text",
            'value = "\\\"keep me\\\""',
            "dots = \\.",
            "```",
            "",
        ]
    )

    result = unescape_pandoc_quotes(text)

    assert '"All times"' in result
    assert "..." in result
    assert '\\"keep me\\"' in result
    assert "\\." in result


def test_strip_cross_doc_links_drops_external_manual_link() -> None:
    lines = animation_lines()
    intro = lines[2]
    text = f"{intro}\n\nSee [Getting Started](../getting-started/index.md) for setup.\n"

    result = strip_cross_doc_links(text)

    assert "[Getting Started]" not in result
    assert "Getting Started for setup." in result


def test_rewrite_cross_chapter_links_handles_collisions() -> None:
    lines = animation_lines()
    intro = lines[2]
    text = "\n".join(
        [
            "# Animation Tool",
            "",
            intro,
            "",
            "## Workflow",
            "See [workflow](new-project.md#workflow).",
            "",
            "# New Project / Scenario Tool",
            "",
            "## Workflow",
            "This is the target section.",
            "",
        ]
    )

    with pytest.warns(UserWarning, match="slug collision"):
        result = rewrite_cross_chapter_links(text, ["animation", "new-project"])

    assert "[workflow](#new-project-workflow)" in result
    assert "[]{#new-project-workflow}" in result
