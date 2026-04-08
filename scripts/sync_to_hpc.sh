#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ -f "${PROJECT_ROOT}/configs/paths.env" ]; then
  set -a
  . "${PROJECT_ROOT}/configs/paths.env"
  set +a
fi

: "${HPC_REMOTE:?Set HPC_REMOTE in the environment or configs/paths.env}"
: "${PROJECT_ROOT_HPC:?Set PROJECT_ROOT_HPC in the environment or configs/paths.env}"

EXCLUDES=(
  --exclude ".git"
  --exclude "__pycache__"
  --exclude ".pytest_cache"
  --exclude ".ruff_cache"
  --exclude ".ipynb_checkpoints"
  --exclude ".venv"
  --exclude "venv"
  --exclude "data/raw/papers"
)

if [ "${SYNC_OUTPUTS:-0}" != "1" ]; then
  EXCLUDES+=(--exclude "outputs" --exclude "logs")
fi

ssh "${HPC_REMOTE}" "mkdir -p '${PROJECT_ROOT_HPC}'"
rsync -av "${EXCLUDES[@]}" "${PROJECT_ROOT}/" "${HPC_REMOTE}:${PROJECT_ROOT_HPC}/"
