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
