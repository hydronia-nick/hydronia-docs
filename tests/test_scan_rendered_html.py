from __future__ import annotations

from pathlib import Path

from scripts.scan_rendered_html import extract_visible_text, scan_html_file


def test_extract_visible_text_prefers_article_and_skips_code() -> None:
    html = """
    <html>
      <body>
        <nav>Navigation â€” ignored</nav>
        <article class="md-content__inner md-typeset">
          <h1>Water quality</h1>
          <p>Rendered paragraph.</p>
          <pre>\\badlatex</pre>
          <script>const text = "â€” ignored";</script>
        </article>
      </body>
    </html>
    """

    chunks = extract_visible_text(html)
    text = "\n".join(chunk.text for chunk in chunks)

    assert "Water quality" in text
    assert "Rendered paragraph." in text
    assert "Navigation" not in text
    assert "\\badlatex" not in text
    assert "ignored" not in text


def test_scan_html_file_flags_rendered_text_smoke_issues(tmp_path: Path) -> None:
    html_path = tmp_path / "site" / "riverflow2d" / "engine-reference" / "index.html"
    html_path.parent.mkdir(parents=True)
    html_path.write_text(
        """
        <article class="md-content__inner md-typeset">
          <h1>Engine Reference</h1>
          <p>Bad mojibake â€” this should be an em dash.</p>
          <p>Raw markdown [chapter](chapter.md) leaked through.</p>
          <p>Raw LaTeX command \\phantomsection leaked through.</p>
        </article>
        """,
        encoding="utf-8",
    )

    issues = scan_html_file(html_path)
    kinds = {issue.kind for issue in issues}

    assert "mojibake" in kinds
    assert "unrendered_markdown_link" in kinds
    assert "raw_latex_command" in kinds


def test_scan_html_file_flags_pdf_conversion_artifacts(tmp_path: Path) -> None:
    html_path = tmp_path / "site" / "riverflow2d" / "engine-reference" / "index.html"
    html_path.parent.mkdir(parents=True)
    html_path.write_text(
        """
        <article class="md-content__inner md-typeset">
          <h1>Hydrodynamic Model</h1>
          <p>::: shader Reboot will be required. :::</p>
          <p>p2.9cmp3.8cmp3.9cm</p>
          <p>Table -- continued from previous page\\</p>
          <p>Subcritical &amp; Q or Velocity &amp; Water Surface Elevation\\</p>
        </article>
        """,
        encoding="utf-8",
    )

    issues = scan_html_file(html_path)
    kinds = {issue.kind for issue in issues}

    assert "directive_leak" in kinds
    assert "pdf_layout_artifact" in kinds
    assert "pdf_table_carryover" in kinds
    assert "tabular_row_leak" in kinds
