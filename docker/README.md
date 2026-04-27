# Local Docker CI-repro system

Status: implemented for the CI PDF build path.

This Docker setup reproduces the expensive and Linux-specific part of the GitHub Actions build: `scripts/build_pdfs.py -> pandoc -> xelatex -> xdvipdfmx`, plus the optional Poppler image-sizing check. It exists because CI-only PDF failures are otherwise slow to debug: each experiment needs a commit, push, Actions startup, TeX install, PDF build, and log inspection.

The 2026-04 engine-reference EPS failure took about 75 minutes across CI bisect commits. With this container, the same class of investigation can happen locally after one image build.

## What This Mirrors

The PDF-relevant pieces of `.github/workflows/deploy.yml` are mirrored intentionally:

- Ubuntu 24.04 userland, matching the current `ubuntu-latest` runner generation.
- Python plus `requirements.txt`.
- Pandoc 3.5 from the upstream `.deb`, matching the workflow's `PANDOC_VERSION`.
- TeX Live from Ubuntu apt packages, not `tlmgr` or an upstream TeX Live ISO.
- Poppler utilities for `scripts/check_pdf_images.py`.

This is deliberately narrower than a full deploy reproduction. `mkdocs build --strict` already runs quickly on the host, and GitHub Pages deployment behavior is outside this tool's scope.

## Files

- `docker/Dockerfile.ci` builds the local CI-like image.
- `docker/run-build.sh` is the Git Bash/Linux/macOS wrapper.
- `docker/run-build.ps1` is the PowerShell wrapper for Windows.

The repo is mounted into the container at runtime. The image bakes in apt packages and Python dependencies, so normal runs do not reinstall TeX or pip packages.

## Quick Start

Build one manual through the CI-like Linux stack:

```bash
bash docker/run-build.sh --manual engine-reference-riverflow2d-en --keep-build
```

PowerShell equivalent:

```powershell
.\docker\run-build.ps1 --% --manual engine-reference-riverflow2d-en --keep-build
```

Run the full PDF build plus the same image-sizing gate CI currently applies:

```bash
bash docker/run-build.sh --ci-full
```

PowerShell equivalent:

```powershell
.\docker\run-build.ps1 -CiFull
```

Force an image rebuild after changing dependencies or the Dockerfile:

```bash
bash docker/run-build.sh --rebuild --manual tutorials-riverflow2d-en --keep-build
```

PowerShell equivalent:

```powershell
.\docker\run-build.ps1 -Rebuild --% --manual tutorials-riverflow2d-en --keep-build
```

## Wrapper Options

The wrapper options are consumed before forwarding the remaining arguments to `scripts/build_pdfs.py`.

- `--rebuild` / `-Rebuild`: rebuild the Docker image before running.
- `--check-images` / `-CheckImages`: after the PDF build, scan all PDFs in `site/pdf/*.pdf` with `scripts/check_pdf_images.py`.
- `--ci-full` / `-CiFull`: run `python scripts/build_pdfs.py --all`, then scan the six PDF manuals currently gated in CI.
- `HYDRONIA_DOCS_CI_IMAGE`: override the Docker image tag.

PowerShell users should usually put `--%` before `build_pdfs.py` options so flags such as `--manual` and `--keep-build` pass through unchanged.

## Why Apt TeX Live Matters

The bugs this tool is designed to catch are often in the exact Pandoc, XeLaTeX, and `xdvipdfmx` combination used by CI. Installing TeX Live through `tlmgr`, MiKTeX, or a newer upstream ISO can move the failure away from the version CI actually runs.

For this repo, a local Windows/MiKTeX success does not prove the GitHub Actions PDF build will succeed. The container gives us a local Linux result that is much closer to CI.

## How This Makes Debugging Faster

Without this tool, a CI-only PDF issue usually looks like this:

1. Make a speculative change.
2. Commit and push.
3. Wait for Actions to provision Python, install TeX, build PDFs, and fail.
4. Read partial logs.
5. Repeat.

With this tool, the loop becomes:

1. Edit locally.
2. Run one manual in the container.
3. Inspect `build/pandoc/`, `build/pdf/`, `site/pdf/`, and stderr immediately.
4. Repeat without pushing.

That makes chapter bisection practical. It also makes CI a confirmation step instead of the only machine that can tell us whether a PDF change worked.

## Known Limits

- Docker Desktop is required locally. If `docker` is not on PATH, the wrappers will stop before doing any work.
- Windows bind mounts can be slower than Linux filesystem mounts, especially for many small files. Single-manual bisection is still usually worth it. If `--all` is too slow, clone the repo inside WSL or another Linux filesystem.
- The base image is pinned to `ubuntu:24.04`, while GitHub's `ubuntu-latest` can roll forward. If repro diverges from CI, compare the TeX Live package versions in the container and in the Actions log.
- This does not reproduce GitHub Pages deployment, runner hardware quirks, or race conditions outside the PDF build path.

## Future Improvement

The next high-value addition is a `--split-build` mode in `scripts/build_pdfs.py`. Instead of asking Pandoc to do Markdown-to-PDF in one step, it would run:

```bash
pandoc ... -o input.tex
xelatex input.tex
xdvipdfmx -vv input.xdv
```

That would preserve `.tex`, `.aux`, `.log`, and `.xdv` artifacts without relying on Pandoc's `/tmp/tex2pdf.*` cleanup behavior. Keep it behind a flag so CI can stay on the current one-step path.

## History

This was added after the 2026-04 engine-reference EPS crash, where repeated CI bisection isolated the failure to EPS handling in chapter 05. The lesson was simple: when the failure lives in Linux Pandoc/TeX tooling, we need a local Linux Pandoc/TeX loop.
