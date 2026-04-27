#!/usr/bin/env bash
set -euo pipefail

DEFAULT_IMAGE="hydronia-docs-ci:24.04-pandoc3.5"
IMAGE="${HYDRONIA_DOCS_CI_IMAGE:-$DEFAULT_IMAGE}"
REBUILD=0
CHECK_IMAGES=0
CI_FULL=0
BUILD_ARGS=()

usage() {
  cat <<'EOF'
Usage:
  docker/run-build.sh [wrapper options] [build_pdfs.py options]

Wrapper options:
  --rebuild        Rebuild the Docker image before running.
  --check-images   After the PDF build, scan site/pdf/*.pdf with check_pdf_images.py.
  --ci-full        Run the CI PDF section: build all PDFs, then scan CI-gated PDFs.
  -h, --help       Show this help.

Examples:
  docker/run-build.sh --manual engine-reference-riverflow2d-en --keep-build
  docker/run-build.sh --check-images --manual tutorials-riverflow2d-en --keep-build
  docker/run-build.sh --ci-full
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --rebuild)
      REBUILD=1
      ;;
    --check-images)
      CHECK_IMAGES=1
      ;;
    --ci-full)
      CI_FULL=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      BUILD_ARGS+=("$1")
      ;;
  esac
  shift
done

if [[ -n "${CI:-}" && "${HYDRONIA_DOCKER_ALLOW_CI:-}" != "1" ]]; then
  echo "This wrapper is intended for local CI reproduction. Set HYDRONIA_DOCKER_ALLOW_CI=1 to run it inside CI." >&2
  exit 2
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_POSIX="$(cd "$SCRIPT_DIR/.." && pwd)"
if REPO_MOUNT="$(cd "$SCRIPT_DIR/.." && pwd -W 2>/dev/null)"; then
  :
else
  REPO_MOUNT="$REPO_POSIX"
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker CLI was not found. Install Docker Desktop or add docker to PATH, then try again." >&2
  exit 127
fi

build_image() {
  docker build -t "$IMAGE" -f "$REPO_MOUNT/docker/Dockerfile.ci" "$REPO_MOUNT"
}

if [[ "$REBUILD" == "1" ]] || ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  build_image
fi

DOCKER_TTY=()
if [[ -t 0 && -t 1 ]]; then
  DOCKER_TTY=(-it)
fi

docker_run() {
  docker run --rm "${DOCKER_TTY[@]}" \
    -v "$REPO_MOUNT:/repo" \
    -e KEEP_TEX2PDF=1 \
    "$IMAGE" "$@"
}

if [[ "$CI_FULL" == "1" ]]; then
  if [[ ${#BUILD_ARGS[@]} -ne 0 || "$CHECK_IMAGES" == "1" ]]; then
    echo "--ci-full runs its own fixed command set; do not combine it with build args or --check-images." >&2
    exit 2
  fi

  docker_run bash -lc '
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
  '
  exit $?
fi

docker_run python scripts/build_pdfs.py "${BUILD_ARGS[@]}"

if [[ "$CHECK_IMAGES" == "1" ]]; then
  docker_run bash -lc '
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
  '
fi
