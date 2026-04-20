# Pandoc PDF Build Pipeline — Implementation Spec

Implementation target: Pandoc + XeLaTeX pipeline that turns the MkDocs-sourced per-product markdown into publication-grade PDF manuals, replacing the failed `mkdocs-exporter` experiment. This document is the authoritative spec for an implementing agent (Codex). The companion design spec is split across §1 (template) and §2 (pipeline) below.

**Confirmed decisions:**

1. **Use the Hydronia brand palette** (`#014589` primary, `#0E367C` dark, `#5974B1` accent) for chapter/section titles, TOC titles, figure-caption labels, and hyperlinks. The existing LaTeX manual uses plain `blue` — the Pandoc PDFs **upgrade** to the brand.
2. **CI caching via `awalsh128/cache-apt-pkgs-action@v1`** — approved.
3. **Front matter must replicate the existing LaTeX manual**: custom title page, legal/copyright page, TOC, List of Figures. Inspect the LaTeX source (paths below) to lift wording + layout; the Pandoc template must produce a visually equivalent result.

**Important rules:**

- **Do not credit Claude / Anthropic / AI anywhere** in code comments, commit messages, generated PDFs, or documentation.
- **Do not remove existing files** without explicit approval. If something looks dead, leave it and flag in the report.
- **Windows-first repo**. Paths use backslashes in docs but code should use `pathlib.Path` — no hard-coded separators.
- **No Claude Code / Codex attribution in commits.** Normal commit messages only.

---

## §1 — Pandoc template design (`pandoc/hydronia.tex`)

Source of truth for the existing manual's look is the LaTeX preamble at:

```
E:\Hydronia Dropbox\Nick Calero\Manuals\QGIS_Plugin_Reference_Manual_Latex\QGIS_Plugin_Reference_Manual.tex
```

and the toggle files `set_{rf2d,of2d,hbf}{,_es}_toggles.tex` in the same directory. **Only read files inside `QGIS_Plugin_Reference_Manual_Latex\` — do not recurse into the parent Dropbox tree.**

### Document class + geometry

- `\documentclass[letter,10pt,openany]{book}` (`twoside` implicit).
- Use `\usepackage[letterpaper,inner=1.5in,outer=1.0in,top=0.75in,bottom=1.0in,headheight=14pt]{geometry}` (cleaner replacement for the original manual setlength calls). Expose `$geometry$` Pandoc template variable.
- `\setlength\parindent{0pt}` and `\onehalfspacing` (via `setspace`).
- `\setcounter{secnumdepth}{3}` and `\setcounter{tocdepth}{2}`.

### Fonts (XeLaTeX)

The existing manual is **Helvetica-sans throughout**. Match with TeX Live's metric-compatible clone:

```tex
\usepackage{fontspec}
\setmainfont{TeX Gyre Heros}
\setsansfont{TeX Gyre Heros}
\setmonofont{TeX Gyre Cursor}
\renewcommand{\familydefault}{\sfdefault}
```

Template vars `$mainfont$` / `$sansfont$` / `$monofont$` must override defaults.

### Colors

```tex
\usepackage{xcolor}
\definecolor{hydroniaPrimary}{HTML}{014589}
\definecolor{hydroniaDark}{HTML}{0E367C}
\definecolor{hydroniaAccent}{HTML}{5974B1}
\colorlet{tableheadcolor}{hydroniaAccent!20}
```

Replace **every** `\color{blue}` in the existing preamble's `titlesec`, `tocloft`, and `quotchap` calls with `\color{hydroniaPrimary}`.

### Chapter / section styling

- `\usepackage[sf]{titlesec}` with the section/subsection/subsubsection rules quoted in the design report (LARGE/Large/large, sf, raggedright, colored, 0.5em separator).
- Chapters: `\usepackage[avantgarde]{quotchap}` with `\renewcommand\sectfont{\sffamily\color{hydroniaPrimary}}`. Verify it compiles under XeLaTeX; if it fights `fontspec`, fall back to manual `titlesec` chapter styling producing a similar big-numeral-right effect.
- Provide a `$useQuotchap$` flag (default true) so the HBF flavor (which disables quotchap in the original) can render with the plain `titlesec` chapter style.

### TOC + front matter — replicate the existing manual

Order and style must match the existing PDF:

1. **Title page.** Big sans primary-color product name, subtitle if present, date, "Hydronia LLC". The existing source uses a `\titleGM` custom command — inspect its definition in the preamble, replicate the layout using Pandoc template variables `$title$`, `$subtitle$`, `$date$`, `$author$`. Include the Hydronia logo if `$coverLogo$` is provided (path resolved via `\graphicspath`).
2. **Legal / copyright page.** Roman page number, `\footnotesize`, language-aware (EN/ES) wording. Inspect the existing manual's copyright page (directly after `\titleGM` in the master). Copy the wording verbatim for EN; the `Espanol` branch has the ES wording. The Pandoc template should accept `$lang$` (`en` / `es`) and emit the correct text. Include: copyright year range, "All rights reserved" clause, support email, website, last-modified date.
3. **TOC** (`\tableofcontents`), with `tocloft` overrides for huge sans colored titles.
4. **List of Figures** (`\listoffigures`), same styling.
5. `\clearpage`, switch to arabic page numbering, `\pagestyle{fancy}`, body begins.

`tocloft` overrides: `\renewcommand\cfttoctitlefont{\huge\sffamily\color{hydroniaPrimary}}` (same for `\cftloftitlefont`); `\setlength{\cftfignumwidth}{3em}`.

### Figures

- Load `\usepackage{float}` so `[H]` placement works.
- `\usepackage[margin=9pt,font=small,labelfont=bf,labelsep=endash]{caption}` — matches existing style ("**Figure 2.3** – caption text").
- Per-chapter figure numbering is the `book` class default; no override needed.
- Accept `$lang$` to set `\figurename` and `\tablename` to Spanish `Figura`/`Tabla` when `$lang$ == es`.

### Tables

Load `booktabs`, `longtable`, `tabularx`, `array`, `multirow`, `colortbl`. Captions: same style as figures.

### Hyperlinks

```tex
\usepackage{hyperref}
\hypersetup{
  colorlinks=true,
  linkcolor=hydroniaPrimary,
  urlcolor=hydroniaPrimary,
  citecolor=hydroniaPrimary,
  pdftitle={$title$},
  pdfauthor={$author$},
  pdfsubject={$subject$},
  pdfkeywords={$keywords$}
}
```

Expose `$hidelinks$` flag to switch to `hidelinks` instead (default off — we want colored links).

### Fancy headers / footers

Match the existing layout:

- `\fancyhead[LE]{\sffamily \rightmark}` (section on even pages)
- `\fancyhead[RE]{\sffamily \thepage}`
- `\fancyhead[RO]{\sffamily \leftmark}` (chapter on odd pages)
- `\fancyhead[LO]{\sffamily \thepage}`
- `\chaptermark` strips the "Chapter" word.
- `plain` pagestyle (chapter first pages) redefined: no rules, centered sans page number in footer.

### Graphics paths

```tex
\graphicspath{{./}{./img/}{./images/}{./converted_graphics/}}
```

The per-product `docs/<product>/img/` resolves via the pipeline's `--resource-path`.

### Product-name macros

Preserve these (they appear in body fragments of the original; harmless if the Pandoc sources never use them):

```tex
\newcommand{\rflo}{\mbox{\sffamily RiverFlow2D}}
\newcommand{\rf2d}{\mbox{\sffamily RiverFlow2D}}
\newcommand{\of2d}{\mbox{\sffamily OilFlow2D}}
\newcommand{\hbflood}{\mbox{\sffamily HydroBID Flood}}
\newcommand{\qgis}{\mbox{\sffamily QGIS}}
\newcommand{\rfqgis}{\rf2d{} QGIS plugin}
\newcommand{\hbfqgis}{\hbflood{} QGIS plugin}
\newcommand{\ofqgis}{\of2d{} QGIS plugin}
\newcommand{\dip}{\mbox{\sffamily DIP}}
```

### What to drop vs keep

**Keep only what's used:** `geometry`, `fontspec` (XeLaTeX) / `helvet` fallback, `xcolor`, `caption`, `float`, `graphicx`, `booktabs`, `longtable`, `tabularx`, `array`, `multirow`, `colortbl`, `fancyhdr`, `titlesec`, `quotchap`, `tocloft`, `tocbibind`, `setspace`, `etoolbox`, `hyperref`, `listings` (for Pandoc `--listings` flag).

**Drop:** `harvard`, `agsm`, `multind`, `subeqnarray`, `amsthm`, `framed` (dup), `fancybox`, `floatpag`, `placeins`, `epstopdf`, `soul`, `gensymb`, `wrapfig`, `sidecap`, `rotating`, `selectcolormodel{cmyk}`, duplicate `\usepackage` lines, the empty `notation.tex` include.

---

## §2 — Build pipeline

### Source assembly

**Concatenate** per-product chapters into `build/pandoc/<manual-id>.md`. Single-file input is cleanest for Pandoc's TOC + internal cross-refs + `--top-level-division=chapter`. Rewrite cross-chapter link anchors (`new-project.md#slug` → `#slug`; detect slug collisions and warn).

### Image paths

**Don't copy images.** Pass `--resource-path="build/pandoc/<manual-id>:docs/<product>"` so Pandoc finds `img/foo.png` inside `docs/<product>/img/`.

### Manual registry — `pandoc/manuals.yaml`

```yaml
manuals:
  - id: riverflow2d-plugin-reference-en
    product: riverflow2d
    manual: qgis-plugin-reference
    flavor: qgis
    language: en
    title: "RiverFlow2D QGIS Plugin Reference Manual"
    subtitle: "Two-Dimensional Flood and River Dynamics Model"
    author: "Hydronia LLC"
    date: "April 2026"
    source_dir: docs/riverflow2d
    chapters: [index, new-project, export, maps, animation, cross-sections, tools, context-menus, appendix]
    output: site/pdf/RiverFlow2D-Plugin-Reference.pdf
    useQuotchap: true

  - id: oilflow2d-plugin-reference-en
    product: oilflow2d
    manual: qgis-plugin-reference
    flavor: qgis
    language: en
    title: "OilFlow2D QGIS Plugin Reference Manual"
    subtitle: "Oil Spill Modeling for Land and Water"
    author: "Hydronia LLC"
    date: "April 2026"
    source_dir: docs/oilflow2d
    chapters: [index, new-project, export, maps, animation, cross-sections, tools, context-menus, appendix]
    output: site/pdf/OilFlow2D-Plugin-Reference.pdf
    useQuotchap: true

  - id: hydrobid-flood-plugin-reference-en
    product: hydrobid-flood
    manual: qgis-plugin-reference
    flavor: qgis
    language: en
    title: "HydroBID Flood QGIS Plugin Reference Manual"
    subtitle: "IDB Flood Mitigation and Urban Drainage Edition"
    author: "Hydronia LLC"
    date: "April 2026"
    source_dir: docs/hydrobid-flood
    chapters: [index, new-project, export, maps, animation, cross-sections, tools, context-menus, appendix]
    output: site/pdf/HydroBIDFlood-Plugin-Reference.pdf
    useQuotchap: false
```

Schema notes:
- `id` must match `[a-z0-9-]+`.
- `chapters` is an ordered list of `.md` filenames (no extension) under `source_dir`.
- Only `id`, `source_dir`, `chapters`, `output`, `title`, `language` are mandatory; others have defaults in `pandoc/manuals.defaults.yaml` (to be created).
- Later rows for ES / additional manuals are **additive** — same schema.

### Scripts

**`scripts/pandoc_preprocess.py`** — pure-function string transforms, no I/O:

- `rewrite_cross_chapter_links(text: str, chapters: list[str]) -> str` — `<chapter>.md#slug` → `#slug`; collisions get `#<chapter>-<slug>` with a warning.
- `neutralize_raw_figure_blocks(text: str) -> str` — replace raw `<figure>...<figcaption>...</figure>` blocks (no image child) with a bold caption paragraph.
- `unescape_pandoc_quotes(text: str) -> str` — `\"` → `"`, `\.` → `.` in body text (leave code blocks alone).
- `strip_cross_doc_links(text: str) -> str` — `../getting-started/...` etc. become plain link text (drop the link).
- `strip_frontmatter(text: str) -> str` — remove any YAML frontmatter at the top of a chapter (our chapters don't have it but defensive).

Each function gets a unit test in `tests/test_pandoc_preprocess.py` (new directory).

**`scripts/build_pdfs.py`** — orchestrator with argparse CLI:

```
python scripts/build_pdfs.py                          # build all manuals
python scripts/build_pdfs.py --manual <id>            # single manual
python scripts/build_pdfs.py --product riverflow2d    # all manuals for a product
python scripts/build_pdfs.py --dry-run                # concat + preprocess, skip pandoc
python scripts/build_pdfs.py --keep-build             # preserve build/pandoc/ for debugging
python scripts/build_pdfs.py --verify-only <id>       # run verification on a pre-built PDF
```

Flow per manual:
1. Load registry + defaults; merge.
2. Concatenate chapters → `build/pandoc/<id>.md` (demote all H1 in individual files if the chapter already starts with H1 and `--top-level-division=chapter` would double-chapter).
3. Run preprocess module over the concatenated text.
4. Emit `build/pandoc/<id>.meta.yaml` with Pandoc metadata (title, subtitle, author, date, lang, subject, keywords, useQuotchap, coverLogo path).
5. Invoke Pandoc with flags in §2/Pandoc invocation.
6. Run verifier (page count within ±10% of `pandoc/baselines.json` if present; every chapter title appears in extracted PDF text).
7. Copy output to `output` path.

Concurrency: sequential by default; optional `--parallel` to build manuals in parallel using `concurrent.futures.ProcessPoolExecutor`.

### Pandoc invocation

```
pandoc build/pandoc/<id>.md \
  --from=markdown+pipe_tables+grid_tables+yaml_metadata_block+tex_math_dollars+raw_tex+fenced_divs+bracketed_spans+link_attributes \
  --to=pdf \
  --pdf-engine=xelatex \
  --template=pandoc/hydronia.tex \
  --metadata-file=pandoc/metadata.yaml \
  --metadata-file=build/pandoc/<id>.meta.yaml \
  --resource-path="build/pandoc/<id>:docs/<product>" \
  --toc --toc-depth=3 \
  --number-sections \
  --top-level-division=chapter \
  --listings \
  --highlight-style=tango \
  --output <build-output>
```

### Files to create

- `pandoc/hydronia.tex` — the template (Pandoc-dialect `.tex`, uses `$title$`, `$author$`, `$body$`, `$toc$`, etc.).
- `pandoc/metadata.yaml` — shared defaults (author: Hydronia LLC, colorlinks: true, numbersections: true, fontsize: 10pt).
- `pandoc/manuals.yaml` — the registry (full contents above).
- `pandoc/manuals.defaults.yaml` — optional cross-manual defaults.
- `pandoc/texlive-packages.txt` — one package per line, used by CI cache key + install.
- `scripts/build_pdfs.py`
- `scripts/pandoc_preprocess.py`
- `tests/test_pandoc_preprocess.py`

### Files to modify

- `.github/workflows/deploy.yml` — insert PDF build steps between `Build site` and `Upload artifact`. See §3 below.
- `README.md` — add "Building PDFs locally" section: prereqs (Pandoc, TeXLive or MiKTeX), one-command build, where to find output, note about HTML vs PDF figure numbering being independent.
- `docs/riverflow2d/index.md`, `docs/oilflow2d/index.md`, `docs/hydrobid-flood/index.md` — add a prominent "Download the PDF" link near the top.

### CI workflow additions

Inspect the existing `.github/workflows/deploy.yml` (already has `actions/checkout@v4`, `actions/setup-python@v5`, pip install from `requirements.txt`, `mkdocs build --strict`, `actions/upload-pages-artifact@v3`, `actions/deploy-pages@v4`).

Insert after the `mkdocs build` step:

```yaml
- name: Install Pandoc
  run: |
    PANDOC_VERSION=3.5
    wget -q https://github.com/jgm/pandoc/releases/download/${PANDOC_VERSION}/pandoc-${PANDOC_VERSION}-1-amd64.deb
    sudo dpkg -i pandoc-${PANDOC_VERSION}-1-amd64.deb

- name: Cache + install TeX Live packages
  uses: awalsh128/cache-apt-pkgs-action@v1
  with:
    packages: texlive-xetex texlive-fonts-recommended texlive-latex-recommended texlive-latex-extra texlive-lang-spanish lmodern
    version: 1.0
    execute_install_scripts: true

- name: Build PDFs
  run: python scripts/build_pdfs.py --all

- name: Stage PDFs into site
  run: |
    mkdir -p site/pdf
    cp build/pdf/*.pdf site/pdf/
```

### `pandoc/texlive-packages.txt`

One package per line. Used only as input to the apt cache key in CI (the actual `packages:` list is inline in the workflow).

```
texlive-xetex
texlive-fonts-recommended
texlive-latex-recommended
texlive-latex-extra
texlive-lang-spanish
lmodern
```

### Failure modes

- CI: any Pandoc non-zero exit fails the workflow.
- Local: per-manual errors are logged but don't block subsequent manuals.
- Verifier warnings (missing anchor targets, stripped constructs) always log, never fatal.

### Testing

In `build_pdfs.py`'s verifier, per manual:
1. Output file exists and > 100 KB.
2. `pypdf` page count within ±10% of `pandoc/baselines.json[<id>].pages` (if present; first green build commits the baseline).
3. `pypdf` text extraction — every chapter title from the registry appears in the extracted text.

### Local dev

```
python scripts/build_pdfs.py --manual riverflow2d-plugin-reference-en --keep-build
```

Produces:
- `build/pandoc/riverflow2d-plugin-reference-en.md` (preserved)
- `build/pandoc/riverflow2d-plugin-reference-en.meta.yaml` (preserved)
- `site/pdf/RiverFlow2D-Plugin-Reference.pdf`

Developer prereqs documented in `README.md`:
- Windows: `scoop install pandoc miktex` (or install each manually).
- macOS: `brew install pandoc && brew install --cask mactex-no-gui`.
- Linux: system package manager + `texlive-xetex` + `texlive-latex-extra`.

---

## §3 — Implementation tasks (ordered)

Each task must be self-contained — pass all tests / produce a usable artifact — before moving on.

1. **`pandoc/hydronia.tex`** — the Pandoc template. Inspect the existing LaTeX manual's `\titleGM` and copyright-page source to replicate the front matter. Confirm it compiles with a minimal `\documentclass{book}\begin{document}Hello\end{document}` body passed through Pandoc.

2. **`pandoc/metadata.yaml`** + **`pandoc/manuals.yaml`** + **`pandoc/manuals.defaults.yaml`** + **`pandoc/texlive-packages.txt`**.

3. **`scripts/pandoc_preprocess.py`** with the five pure functions + docstrings. Each docstring includes a minimal before/after example.

4. **`tests/test_pandoc_preprocess.py`** with one test per function. Use realistic fixtures extracted from `docs/riverflow2d/animation.md`. Run via `pytest tests/`.

5. **`scripts/build_pdfs.py`** — orchestrator. Full CLI surface. Must handle the case where Pandoc or XeLaTeX is missing (friendly error + install hint).

6. **Local smoke test** — run `python scripts/build_pdfs.py --manual riverflow2d-plugin-reference-en --keep-build` and report: Pandoc exit code, output PDF size, page count, preserved `.md` / `.meta.yaml` paths. Do **not** commit the PDFs.

7. **`.github/workflows/deploy.yml`** modifications per §2.

8. **`docs/<product>/index.md`** — Download PDF links on all three product landing pages.

9. **`README.md`** — Building PDFs locally section.

10. **`requirements.txt`** — add `pypdf` (used for verification). Keep `mkdocs-exporter` removed.

## Summary for implementer

Read this spec end-to-end. Read the existing LaTeX manual preamble + one or two toggle files + the chapters `.tex` if needed for the title page / copyright wording — but **stay inside `QGIS_Plugin_Reference_Manual_Latex/`**. Implement tasks 1–10 in order. After task 6 (local smoke test), **pause and report** — don't modify the CI workflow or landing pages until the local build produces an acceptable PDF.

Report at the end:
- Files created / modified (paths).
- Local smoke-test results (page count, file size per manual).
- Any deviations from this spec (and why).
- Anything you saw that this spec didn't cover and that should be decided by a human.
