# hydronia-docs

Source for the Hydronia user-facing documentation portal. Built with [MkDocs](https://www.mkdocs.org/) + [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/). Deployed to GitHub Pages via the workflow in `.github/workflows/deploy.yml`.

## Local development

```bash
python -m venv .venv
.venv\Scripts\activate    # Windows
pip install -r requirements.txt
mkdocs serve
```

The dev server runs at http://127.0.0.1:8000 and hot-reloads on save.

## Build

```bash
mkdocs build --strict
```

Output goes to `site/`.

## Building PDFs locally

Prereqs:
- Pandoc 3.x
- XeLaTeX
- TeX Live on Linux and macOS, or MiKTeX on Windows

Quick install tips:
- Debian/Ubuntu: `sudo apt-get install pandoc texlive-xetex`
- macOS (Homebrew): `brew install pandoc mactex-no-gui`
- Windows (Scoop): `scoop install pandoc miktex`

Build all manuals:

```bash
python scripts/build_pdfs.py --all
```

Build a single manual:

```bash
python scripts/build_pdfs.py --manual <id> --keep-build
```

Dry run:

```bash
python scripts/build_pdfs.py --dry-run
```

Outputs land in `build/pdf/` and `site/pdf/`.

HTML and PDF figure numbering may diverge because Pandoc and LaTeX number figures independently from `mkdocs-caption`.

### Managing manual versions

By default, the PDF title-page date comes from git history. To pin a release date, set `date: "March 2026"` on the manual's row in `pandoc/manuals.yaml`.

## Project layout

```
docs/              # Markdown source
  index.md
  javascripts/     # MathJax config
  stylesheets/     # Brand CSS overrides
mkdocs.yml         # Site config (theme, plugins, nav)
requirements.txt   # Python dependencies
```

Maintained by Hydronia LLC.
