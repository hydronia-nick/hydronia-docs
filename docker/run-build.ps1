[CmdletBinding()]
param(
    [switch]$Rebuild,
    [switch]$CheckImages,
    [switch]$CiFull,
    [switch]$Help,
    [string]$Image = $env:HYDRONIA_DOCS_CI_IMAGE,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$BuildArgs
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $Image) {
    $Image = "hydronia-docs-ci:24.04-pandoc3.5"
}

function Show-Usage {
    @"
Usage:
  .\docker\run-build.ps1 [wrapper options] [build_pdfs.py options]

Wrapper options:
  -Rebuild       Rebuild the Docker image before running.
  -CheckImages   After the PDF build, scan site/pdf/*.pdf with check_pdf_images.py.
  -CiFull        Run the CI PDF section: build all PDFs, then scan CI-gated PDFs.
  -Image <tag>   Override the Docker image tag.
  -Help          Show this help.

Examples:
  .\docker\run-build.ps1 --% --manual engine-reference-riverflow2d-en --keep-build
  .\docker\run-build.ps1 -CheckImages --% --manual tutorials-riverflow2d-en --keep-build
  .\docker\run-build.ps1 -CiFull

PowerShell tip:
  Use --% before build_pdfs.py options so flags such as --manual pass through unchanged.
"@
}

if ($Help) {
    Show-Usage
    exit 0
}

if ($env:CI -and $env:HYDRONIA_DOCKER_ALLOW_CI -ne "1") {
    throw "This wrapper is intended for local CI reproduction. Set HYDRONIA_DOCKER_ALLOW_CI=1 to run it inside CI."
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker CLI was not found. Install Docker Desktop or add docker to PATH, then try again."
}

$Repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Dockerfile = Join-Path $Repo "docker/Dockerfile.ci"

function Invoke-DockerChecked {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)

    & docker @Arguments
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

function Test-ImageExists {
    & docker image inspect $Image *> $null
    return $LASTEXITCODE -eq 0
}

function Build-Image {
    Invoke-DockerChecked build -t $Image -f $Dockerfile $Repo
}

if ($Rebuild -or -not (Test-ImageExists)) {
    Build-Image
}

$DockerRunArgs = @(
    "run",
    "--rm",
    "-v",
    "${Repo}:/repo",
    "-e",
    "KEEP_TEX2PDF=1",
    $Image
)

if ($CiFull) {
    if ($BuildArgs.Count -gt 0 -or $CheckImages) {
        throw "-CiFull runs its own fixed command set; do not combine it with build args or -CheckImages."
    }

    $Command = @'
set -euo pipefail
python scripts/build_pdfs.py --all
for id in \
  qgis-reference-riverflow2d-en \
  qgis-reference-oilflow2d-en \
  qgis-reference-hydrobid-flood-en \
  tutorials-riverflow2d-en \
  tutorials-oilflow2d-en \
  tutorials-hydrobid-flood-en; do
    echo "check: ${id}"
    python scripts/check_pdf_images.py "site/pdf/${id}.pdf" --top 20
done
'@
    Invoke-DockerChecked @DockerRunArgs bash -lc $Command
    exit 0
}

Invoke-DockerChecked @DockerRunArgs python scripts/build_pdfs.py @BuildArgs

if ($CheckImages) {
    $Command = @'
set -euo pipefail
shopt -s nullglob
pdfs=(site/pdf/*.pdf)
if [[ ${#pdfs[@]} -eq 0 ]]; then
  echo "No PDFs found under site/pdf/." >&2
  exit 1
fi
for pdf in "${pdfs[@]}"; do
  echo "check: ${pdf}"
  python scripts/check_pdf_images.py "$pdf" --top 20
done
'@
    Invoke-DockerChecked @DockerRunArgs bash -lc $Command
}
