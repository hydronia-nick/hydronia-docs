"""Build Hydronia PDF manuals from the MkDocs chapter sources."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts import pandoc_preprocess as preprocess

try:
    import yaml
except ImportError as exc:  # pragma: no cover - environment issue
    raise SystemExit(
        "PyYAML is required to build the manuals. Install it with `pip install pyyaml`."
    ) from exc


REPO_ROOT = Path(__file__).resolve().parent.parent
PANDOC_DIR = REPO_ROOT / "pandoc"
BUILD_DIR = REPO_ROOT / "build"
BUILD_PANDOC_DIR = BUILD_DIR / "pandoc"
BUILD_PDF_DIR = BUILD_DIR / "pdf"
DEFAULTS_PATH = PANDOC_DIR / "manuals.defaults.yaml"
REGISTRY_PATH = PANDOC_DIR / "manuals.yaml"
METADATA_PATH = PANDOC_DIR / "metadata.yaml"
TEMPLATE_PATH = PANDOC_DIR / "hydronia.tex"
BASELINES_PATH = PANDOC_DIR / "baselines.json"

MARKDOWN_EXTENSIONS = (
    "markdown+pipe_tables+grid_tables+yaml_metadata_block+tex_math_dollars+raw_tex+fenced_divs+bracketed_spans+link_attributes"
)


@dataclass
class BuildOutcome:
    manual_id: str
    markdown_path: Path
    meta_path: Path
    build_pdf_path: Path
    output_pdf_path: Path
    pandoc_exit_code: int | None = None
    size_bytes: int | None = None
    page_count: int | None = None
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    copied_output: bool = False

    @property
    def succeeded(self) -> bool:
        return not self.errors and (self.pandoc_exit_code in {None, 0})


def load_yaml_file(path: Path) -> Any:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return {} if data is None else data


def save_yaml_file(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        yaml.safe_dump(data, handle, sort_keys=False, allow_unicode=True)


def merge_dicts(*parts: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for part in parts:
        merged.update(part)
    return merged


def extract_year(text: str, fallback: int | None = None) -> int:
    match = re.search(r"(\d{4})\s*$", text.strip())
    if match:
        return int(match.group(1))
    if fallback is not None:
        return fallback
    return datetime.now().year


def chapter_title_from_text(text: str) -> str | None:
    for line in text.splitlines():
        stripped = line.strip()
        match = re.match(r"^#\s+(?P<title>.+?)(?:\s*\{#.*\})?\s*$", stripped)
        if match:
            return match.group("title").strip()
    return None


def chapter_titles_from_source(manual: dict[str, Any]) -> list[str]:
    source_dir = REPO_ROOT / str(manual["source_dir"])
    titles: list[str] = []
    for chapter_name in manual["chapters"]:
        path = chapter_path(source_dir, chapter_name)
        if not path.exists():
            continue
        raw_text = path.read_text(encoding="utf-8")
        cleaned_text = clean_chapter_text(raw_text)
        title = chapter_title_from_text(cleaned_text)
        if title:
            titles.append(title)
    return titles


def load_manuals() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    defaults = load_yaml_file(DEFAULTS_PATH)
    registry = load_yaml_file(REGISTRY_PATH)
    manuals = registry.get("manuals", [])
    if not isinstance(manuals, list):
        raise ValueError(f"Expected a list of manuals in {REGISTRY_PATH}")
    return defaults, manuals


def validate_manual_spec(manual: dict[str, Any]) -> None:
    required = {"id", "source_dir", "chapters", "output", "title", "language"}
    missing = sorted(required - manual.keys())
    if missing:
        raise ValueError(f"Manual {manual.get('id', '<unknown>')} is missing: {', '.join(missing)}")
    if not re.fullmatch(r"[a-z0-9-]+", str(manual["id"])):
        raise ValueError(f"Manual id must match [a-z0-9-]+: {manual['id']}")


def merged_manual(defaults: dict[str, Any], manual: dict[str, Any]) -> dict[str, Any]:
    validate_manual_spec(manual)
    merged = merge_dicts(defaults, manual)
    title = str(merged["title"])
    date = str(merged.get("date", defaults.get("date", "")))
    start_year = int(merged.get("copyrightYearsStart", defaults.get("copyrightYearsStart", 2011)))
    end_year = extract_year(date, fallback=start_year)
    merged["date"] = date
    merged["author"] = merged.get("author") or defaults.get("author") or "Hydronia LLC"
    merged["subject"] = merged.get("subject") or title
    merged["keywords"] = merged.get("keywords") or f"{title}, {merged.get('product', '')}, Hydronia LLC, QGIS"
    merged["copyrightYears"] = f"{start_year}-{end_year}"
    return merged


def chapter_path(source_dir: Path, chapter_name: str) -> Path:
    path = source_dir / f"{chapter_name}.md"
    if path.exists():
        return path
    return source_dir / f"{chapter_name}.markdown"


def clean_chapter_text(raw_text: str) -> str:
    text = preprocess.strip_frontmatter(raw_text)
    text = preprocess.neutralize_raw_figure_blocks(text)
    text = preprocess.strip_cross_doc_links(text)
    text = preprocess.unescape_pandoc_quotes(text)
    return text


def build_manual_markdown(manual: dict[str, Any], keep_build: bool) -> tuple[Path, Path, Path, list[str], str]:
    manual_id = manual["id"]
    source_dir = REPO_ROOT / str(manual["source_dir"])
    markdown_path = BUILD_PANDOC_DIR / f"{manual_id}.md"
    meta_path = BUILD_PANDOC_DIR / f"{manual_id}.meta.yaml"
    BUILD_PANDOC_DIR.mkdir(parents=True, exist_ok=True)

    chapter_texts: list[str] = []
    chapter_titles: list[str] = []
    for chapter_name in manual["chapters"]:
        path = chapter_path(source_dir, chapter_name)
        if not path.exists():
            raise FileNotFoundError(f"Missing chapter file: {path}")
        raw_text = path.read_text(encoding="utf-8")
        cleaned_text = clean_chapter_text(raw_text)
        title = chapter_title_from_text(cleaned_text) or chapter_name
        chapter_titles.append(title)
        chapter_texts.append(cleaned_text.rstrip() + "\n")

    combined = "\n".join(chapter_texts)
    combined = preprocess.rewrite_cross_chapter_links(combined, list(manual["chapters"]))
    with markdown_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(combined)

    meta = {
        "title": manual["title"],
        "subtitle": manual.get("subtitle", ""),
        "author": manual["author"],
        "date": manual["date"],
        "lang": manual["language"],
        "subject": manual["subject"],
        "keywords": manual["keywords"],
        "useQuotchap": bool(manual.get("useQuotchap", True)),
        "coverLogo": manual.get("coverLogo", ""),
        "hidelinks": bool(manual.get("hidelinks", False)),
        "copyrightYears": manual["copyrightYears"],
    }
    save_yaml_file(meta_path, meta)
    return markdown_path, meta_path, source_dir, chapter_titles, combined


def run_pandoc(manual: dict[str, Any], markdown_path: Path, meta_path: Path, build_pdf_path: Path) -> subprocess.CompletedProcess[str]:
    build_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    template_path = TEMPLATE_PATH.resolve()
    metadata_path = METADATA_PATH.resolve()
    resource_path = os.pathsep.join(
        [
            str(markdown_path.parent.resolve()),
            str((REPO_ROOT / manual["source_dir"]).resolve()),
        ]
    )
    args = [
        "pandoc",
        str(markdown_path.resolve()),
        "--from=" + MARKDOWN_EXTENSIONS,
        "--to=pdf",
        "--pdf-engine=xelatex",
        "--template=" + str(template_path),
        "--metadata-file=" + str(metadata_path),
        "--metadata-file=" + str(meta_path.resolve()),
        "--resource-path=" + resource_path,
        "--toc",
        "--toc-depth=3",
        "--number-sections",
        "--top-level-division=chapter",
        "--listings",
        "--highlight-style=tango",
        "--output",
        str(build_pdf_path.resolve()),
    ]
    return subprocess.run(args, cwd=REPO_ROOT, text=True, capture_output=True)


def read_baseline_pages(manual_id: str) -> int | None:
    if not BASELINES_PATH.exists():
        return None
    data = load_yaml_file(BASELINES_PATH) if BASELINES_PATH.suffix in {".yaml", ".yml"} else None
    if data is None:
        with BASELINES_PATH.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    entry = data.get(manual_id) if isinstance(data, dict) else None
    if isinstance(entry, dict) and isinstance(entry.get("pages"), int):
        return entry["pages"]
    manuals = data.get("manuals") if isinstance(data, dict) else None
    if isinstance(manuals, dict):
        entry = manuals.get(manual_id)
        if isinstance(entry, dict) and isinstance(entry.get("pages"), int):
            return entry["pages"]
    return None


def verify_pdf(manual: dict[str, Any], pdf_path: Path, chapter_titles: list[str]) -> tuple[list[str], int | None, int | None]:
    warnings_list: list[str] = []
    if not pdf_path.exists():
        return [f"missing PDF: {pdf_path}"], None, None
    size_bytes = pdf_path.stat().st_size
    if size_bytes <= 100_000:
        warnings_list.append(f"PDF is smaller than 100 KB: {pdf_path} ({size_bytes} bytes)")

    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - environment issue
        return [
            "pypdf is required for PDF verification. Install it with `pip install pypdf`."
        ], size_bytes, None

    reader = PdfReader(str(pdf_path))
    page_count = len(reader.pages)

    baseline = read_baseline_pages(manual["id"])
    if baseline is not None:
        lower = max(1, int(baseline * 0.9))
        upper = max(lower, int((baseline * 1.1) + 0.9999))
        if not (lower <= page_count <= upper):
            warnings_list.append(
            f"page count {page_count} is outside the +/-10% baseline window ({lower}-{upper}) for {manual['id']}"
            )

    extracted = "\n".join((page.extract_text() or "") for page in reader.pages)
    normalized = re.sub(r"\s+", " ", extracted)
    for title in chapter_titles:
        if not title:
            continue
        if re.sub(r"\s+", " ", title.strip()) not in normalized:
            warnings_list.append(f"chapter title not found in extracted text: {title}")

    return warnings_list, size_bytes, page_count


def cleanup_transient_files(markdown_path: Path, meta_path: Path, keep_build: bool, build_succeeded: bool) -> None:
    if keep_build or not build_succeeded:
        return
    for path in (markdown_path, meta_path):
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def build_single_manual(manual: dict[str, Any], dry_run: bool, keep_build: bool) -> BuildOutcome:
    manual_id = manual["id"]
    markdown_path = BUILD_PANDOC_DIR / f"{manual_id}.md"
    meta_path = BUILD_PANDOC_DIR / f"{manual_id}.meta.yaml"
    build_pdf_path = BUILD_PDF_DIR / f"{manual_id}.pdf"
    output_pdf_path = REPO_ROOT / str(manual["output"])
    outcome = BuildOutcome(
        manual_id=manual_id,
        markdown_path=markdown_path,
        meta_path=meta_path,
        build_pdf_path=build_pdf_path,
        output_pdf_path=output_pdf_path,
    )

    try:
        markdown_path, meta_path, _, chapter_titles, _ = build_manual_markdown(manual, keep_build)
    except Exception as exc:
        outcome.errors.append(str(exc))
        return outcome

    if dry_run:
        outcome.warnings.append("dry-run: pandoc was not executed")
        cleanup_transient_files(markdown_path, meta_path, keep_build, build_succeeded=not outcome.errors)
        return outcome

    if shutil.which("pandoc") is None:
        outcome.errors.append("pandoc is not installed or not on PATH. Install Pandoc and try again.")
        return outcome
    if shutil.which("xelatex") is None:
        outcome.errors.append("xelatex is not installed or not on PATH. Install TeX Live or MiKTeX and try again.")
        return outcome

    result = run_pandoc(manual, markdown_path, meta_path, build_pdf_path)
    outcome.pandoc_exit_code = result.returncode
    if result.returncode != 0:
        outcome.errors.append(f"pandoc failed with exit code {result.returncode}")
        if result.stdout.strip():
            print(result.stdout, end="")
        if result.stderr.strip():
            print(result.stderr, end="", file=sys.stderr)
        return outcome

    verify_warnings, size_bytes, page_count = verify_pdf(manual, build_pdf_path, chapter_titles)
    outcome.warnings.extend(verify_warnings)
    outcome.size_bytes = size_bytes
    outcome.page_count = page_count

    if build_pdf_path.exists():
        output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(build_pdf_path, output_pdf_path)
        outcome.copied_output = True
    else:
        outcome.errors.append(f"pandoc reported success but did not produce {build_pdf_path}")

    cleanup_transient_files(markdown_path, meta_path, keep_build, build_succeeded=not outcome.errors)
    return outcome


def select_manuals(defaults: dict[str, Any], manuals: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    merged = [merged_manual(defaults, manual) for manual in manuals]
    if args.verify_only:
        selected = [manual for manual in merged if manual["id"] == args.verify_only]
        if not selected:
            raise SystemExit(f"Unknown manual id: {args.verify_only}")
        return selected
    if args.manual:
        selected = [manual for manual in merged if manual["id"] == args.manual]
        if not selected:
            raise SystemExit(f"Unknown manual id: {args.manual}")
        return selected
    if args.product:
        selected = [manual for manual in merged if manual.get("product") == args.product]
        if not selected:
            raise SystemExit(f"No manuals found for product: {args.product}")
        return selected
    return merged


def verify_only(manual: dict[str, Any]) -> BuildOutcome:
    manual_id = manual["id"]
    markdown_path = BUILD_PANDOC_DIR / f"{manual_id}.md"
    meta_path = BUILD_PANDOC_DIR / f"{manual_id}.meta.yaml"
    build_pdf_path = BUILD_PDF_DIR / f"{manual_id}.pdf"
    output_pdf_path = REPO_ROOT / str(manual["output"])
    outcome = BuildOutcome(
        manual_id=manual_id,
        markdown_path=markdown_path,
        meta_path=meta_path,
        build_pdf_path=build_pdf_path,
        output_pdf_path=output_pdf_path,
    )

    candidate = output_pdf_path if output_pdf_path.exists() else build_pdf_path
    if not candidate.exists():
        outcome.errors.append(f"No pre-built PDF found for {manual_id}")
        return outcome

    chapter_titles = chapter_titles_from_source(manual)
    verify_warnings, size_bytes, page_count = verify_pdf(manual, candidate, chapter_titles)
    outcome.warnings.extend(verify_warnings)
    outcome.size_bytes = size_bytes
    outcome.page_count = page_count
    outcome.pandoc_exit_code = 0
    outcome.copied_output = candidate == output_pdf_path
    return outcome


def print_outcome(outcome: BuildOutcome) -> None:
    status = "ok" if outcome.succeeded else "failed"
    detail_bits = [f"status={status}"]
    if outcome.pandoc_exit_code is not None:
        detail_bits.append(f"pandoc={outcome.pandoc_exit_code}")
    if outcome.page_count is not None:
        detail_bits.append(f"pages={outcome.page_count}")
    if outcome.size_bytes is not None:
        detail_bits.append(f"size={outcome.size_bytes}")
    detail_bits.append(f"output={outcome.output_pdf_path}")
    print(f"[{outcome.manual_id}] " + " ".join(detail_bits))
    if outcome.warnings:
        for warning in outcome.warnings:
            print(f"  warning: {warning}")
    if outcome.errors:
        for error in outcome.errors:
            print(f"  error: {error}")
    if outcome.copied_output:
        print(f"  copied: {outcome.build_pdf_path} -> {outcome.output_pdf_path}")
    if outcome.markdown_path.exists():
        print(f"  markdown: {outcome.markdown_path}")
    if outcome.meta_path.exists():
        print(f"  metadata: {outcome.meta_path}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--manual", help="Build a single manual by id")
    selection.add_argument("--product", help="Build all manuals for a product slug")
    selection.add_argument("--all", action="store_true", help="Build all manuals")
    selection.add_argument("--verify-only", help="Verify a pre-built PDF for the given manual id")
    parser.add_argument("--dry-run", action="store_true", help="Concatenate and preprocess only")
    parser.add_argument("--keep-build", action="store_true", help="Keep build/pandoc artifacts")
    parser.add_argument("--parallel", action="store_true", help="Build manuals in parallel")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    defaults, manuals = load_manuals()
    selected = select_manuals(defaults, manuals, args)

    if args.verify_only:
        outcomes = [verify_only(selected[0])]
    elif args.parallel and len(selected) > 1:
        outcomes = []
        with ProcessPoolExecutor() as executor:
            futures = {
                executor.submit(build_single_manual, manual, args.dry_run, args.keep_build): manual["id"]
                for manual in selected
            }
            for future in as_completed(futures):
                try:
                    outcomes.append(future.result())
                except Exception as exc:  # pragma: no cover - parallel worker failure
                    manual_id = futures[future]
                    outcomes.append(
                        BuildOutcome(
                            manual_id=manual_id,
                            markdown_path=BUILD_PANDOC_DIR / f"{manual_id}.md",
                            meta_path=BUILD_PANDOC_DIR / f"{manual_id}.meta.yaml",
                            build_pdf_path=BUILD_PDF_DIR / f"{manual_id}.pdf",
                            output_pdf_path=REPO_ROOT / "site" / "pdf" / f"{manual_id}.pdf",
                            errors=[str(exc)],
                        )
                    )
    else:
        outcomes = [build_single_manual(manual, args.dry_run, args.keep_build) for manual in selected]

    for outcome in outcomes:
        print_outcome(outcome)

    if any(outcome.errors for outcome in outcomes):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
