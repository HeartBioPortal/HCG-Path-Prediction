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

mkdir -p "${PROJECT_ROOT}/outputs" "${PROJECT_ROOT}/logs" "${PROJECT_ROOT}/data/reports"
rsync -av "${HPC_REMOTE}:${PROJECT_ROOT_HPC}/outputs/" "${PROJECT_ROOT}/outputs/"
rsync -av "${HPC_REMOTE}:${PROJECT_ROOT_HPC}/logs/" "${PROJECT_ROOT}/logs/"
rsync -av "${HPC_REMOTE}:${PROJECT_ROOT_HPC}/data/reports/" "${PROJECT_ROOT}/data/reports/"

if [ "${SYNC_PROCESSED_DATA:-1}" = "1" ]; then
  mkdir -p "${PROJECT_ROOT}/data/processed"
  rsync -av "${HPC_REMOTE}:${PROJECT_ROOT_HPC}/data/processed/" "${PROJECT_ROOT}/data/processed/"
fi
