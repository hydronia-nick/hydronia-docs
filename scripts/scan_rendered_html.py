#!/usr/bin/env python3
"""Scan built MkDocs HTML for obvious rendered text artifacts."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
import re
import sys


DEFAULT_SITE_DIR = Path("site")

SKIP_TAGS = {"script", "style", "svg", "pre", "code", "noscript"}
CONTAINER_TAGS = {"article", "main"}
CONTENT_CLASS_HINTS = {"md-content__inner", "md-typeset"}

CHECKS: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "mojibake",
        re.compile(r"[�]|(?:â[^\s]{0,3})|(?:Â[^\s]{0,2})|(?:Ã[^\s]{0,2})"),
        "Probable encoding artifact.",
    ),
    (
        "unrendered_markdown_link",
        re.compile(r"!?\[[^\]\n]+\]\([^) \n][^)]+?\)"),
        "Markdown link/image syntax is visible in rendered text.",
    ),
    (
        "raw_latex_command",
        re.compile(r"\\[A-Za-z]{2,}\b"),
        "LaTeX command is visible in rendered text.",
    ),
    (
        "raw_anchor_marker",
        re.compile(r"\[\]\{#[^}]+\}"),
        "Pandoc anchor marker is visible in rendered text.",
    ),
    (
        "html_fragment",
        re.compile(r"</?(?:div|span|figure|figcaption|table|tr|td|img|a)\b[^>]*>"),
        "HTML fragment is visible as text.",
    ),
    (
        "directive_leak",
        re.compile(r":::\s*[A-Za-z][\w-]*"),
        "Markdown directive/admonition syntax is visible in rendered text.",
    ),
    (
        "pdf_table_carryover",
        re.compile(r"Table\s+--\s+continued from previous page\\?"),
        "PDF table carryover text is visible in rendered text.",
    ),
    (
        "pdf_layout_artifact",
        re.compile(r"(?:[pm]\d+(?:\.\d+)?(?:cm|in)){2,}"),
        "PDF layout sizing tokens are visible in rendered text.",
    ),
    (
        "tabular_row_leak",
        re.compile(r"(?:^| )[^ \n][^\\\n]*\s&\s[^\\\n]+\\$"),
        "Tabular row syntax is visible in rendered text.",
    ),
    (
        "unresolved_placeholder",
        re.compile(r"\b(?:TODO|TBD|FIXME)\b", re.IGNORECASE),
        "Placeholder text is visible.",
    ),
)


@dataclass(frozen=True)
class TextChunk:
    text: str
    line: int


@dataclass(frozen=True)
class RenderedIssue:
    path: Path
    line: int
    kind: str
    message: str
    snippet: str


class VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self._content_depth = 0
        self._seen_content_container = False
        self._all_chunks: list[TextChunk] = []
        self._content_chunks: list[TextChunk] = []
        self.chunks: list[TextChunk] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in SKIP_TAGS:
            self._skip_depth += 1
            return
        if tag in CONTAINER_TAGS and self._is_content_container(attrs):
            self._content_depth += 1
            self._seen_content_container = True

    def handle_endtag(self, tag: str) -> None:
        if tag in SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1
            return
        if tag in CONTAINER_TAGS and self._content_depth:
            self._content_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        if self._seen_content_container and self._content_depth <= 0:
            return
        text = normalize_text(data)
        if text:
            line, _ = self.getpos()
            chunk = TextChunk(text=text, line=line)
            if self._content_depth > 0:
                self._content_chunks.append(chunk)
            elif not self._seen_content_container:
                self._all_chunks.append(chunk)

    def close(self) -> None:
        super().close()
        self.chunks = self._content_chunks if self._seen_content_container else self._all_chunks

    @staticmethod
    def _is_content_container(attrs: list[tuple[str, str | None]]) -> bool:
        classes = ""
        for name, value in attrs:
            if name == "class" and value:
                classes = value
                break
        class_names = set(classes.split())
        return bool(class_names & CONTENT_CLASS_HINTS)


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def strip_math_text(text: str) -> str:
    """Remove common MathJax source spans before raw-LaTeX checks."""
    text = re.sub(r"\\\(.+?\\\)", " ", text)
    text = re.sub(r"\\\[.+?\\\]", " ", text)
    text = re.sub(r"\$\$.+?\$\$", " ", text)
    text = re.sub(r"(?<!\\)\$.+?(?<!\\)\$", " ", text)
    return text


def extract_visible_text(html: str) -> list[TextChunk]:
    parser = VisibleTextParser()
    parser.feed(html)
    parser.close()
    return parser.chunks


def format_snippet(text: str, match: re.Match[str], width: int = 130) -> str:
    start = max(0, match.start() - width // 2)
    end = min(len(text), match.end() + width // 2)
    snippet = text[start:end].strip()
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet += "..."
    return snippet


def scan_html_file(path: Path) -> list[RenderedIssue]:
    html = path.read_text(encoding="utf-8", errors="replace")
    issues: list[RenderedIssue] = []
    for chunk in extract_visible_text(html):
        for kind, pattern, message in CHECKS:
            text = strip_math_text(chunk.text) if kind == "raw_latex_command" else chunk.text
            for match in pattern.finditer(text):
                issues.append(
                    RenderedIssue(
                        path=path,
                        line=chunk.line,
                        kind=kind,
                        message=message,
                        snippet=format_snippet(chunk.text, match),
                    )
                )
    return issues


def iter_html_files(site_dir: Path, include: str | None) -> list[Path]:
    files = sorted(site_dir.rglob("*.html"))
    if include:
        normalized = include.replace("\\", "/").strip("/")
        files = [path for path in files if normalized in path.as_posix()]
    return files


def print_issues(issues: list[RenderedIssue], site_dir: Path) -> None:
    for issue in issues:
        try:
            rel = issue.path.relative_to(site_dir)
        except ValueError:
            rel = issue.path
        print(f"{rel}:{issue.line}: {issue.kind}: {issue.message}")
        print(f"  {issue.snippet}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--site-dir",
        type=Path,
        default=DEFAULT_SITE_DIR,
        help="Built MkDocs output directory. Defaults to site/.",
    )
    parser.add_argument(
        "--include",
        help="Only scan rendered paths containing this fragment, e.g. engine-reference.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=200,
        help="Maximum issues to print before truncating output. Use 0 for no limit.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    args = parse_args(argv)
    site_dir = args.site_dir.resolve()
    if not site_dir.exists():
        raise SystemExit(f"site directory not found: {site_dir}")

    html_files = iter_html_files(site_dir, args.include)
    issues: list[RenderedIssue] = []
    for html_file in html_files:
        issues.extend(scan_html_file(html_file))

    printable = issues if args.limit == 0 else issues[: args.limit]
    print_issues(printable, site_dir)

    if args.limit and len(issues) > args.limit:
        remaining = len(issues) - args.limit
        print(f"... {remaining} more issue(s) not shown; rerun with --limit 0.")

    print(
        f"Scanned {len(html_files)} HTML file(s); found {len(issues)} issue(s).",
        file=sys.stderr,
    )
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
