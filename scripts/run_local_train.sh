#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck disable=SC1091
. "${PROJECT_ROOT}/scripts/load_project_env.sh"
load_project_env "${PROJECT_ROOT}"

PROJECT_ROOT_LOCAL="${PROJECT_ROOT_LOCAL:-${PROJECT_ROOT}}"
DATASET_DIR="${DATASET_DIR_LOCAL:-${DATASET_DIR:-${PROJECT_ROOT_LOCAL}/data/processed/cvd_guidelines_assoc}}"
OUTPUT_DIR="${OUTPUT_DIR_LOCAL:-${OUTPUT_DIR:-${PROJECT_ROOT_LOCAL}/outputs/cvd_assoc/checkpoints}}"
BIOPATHNET_GPUS="${BIOPATHNET_GPUS:-null}"
BIOPATHNET_BATCH_SIZE="${BIOPATHNET_BATCH_SIZE:-4}"
BIOPATHNET_NUM_EPOCHS="${BIOPATHNET_NUM_EPOCHS:-5}"
BIOPATHNET_SEED="${BIOPATHNET_SEED:-1024}"

mkdir -p "${PROJECT_ROOT_LOCAL}/logs/local" "${OUTPUT_DIR}"
LOG_FILE="${PROJECT_ROOT_LOCAL}/logs/local/train-$(date +%Y%m%d-%H%M%S).log"
exec > >(tee -a "${LOG_FILE}") 2>&1

cd "${PROJECT_ROOT_LOCAL}"

if [ ! -d "${DATASET_DIR}" ]; then
  echo "Dataset directory not found: ${DATASET_DIR}"
  exit 1
fi

COMMAND=(
  python third_party/BioPathNet/script/run.py
  -s "${BIOPATHNET_SEED}"
  -c configs/cvd_assoc_run.yaml
  --dataset_path "${DATASET_DIR}"
  --output_dir "${OUTPUT_DIR}"
  --gpus "${BIOPATHNET_GPUS}"
  --batch_size "${BIOPATHNET_BATCH_SIZE}"
  --num_epoch "${BIOPATHNET_NUM_EPOCHS}"
)

printf 'Running:'
printf ' %q' "${COMMAND[@]}"
printf '\n'
"${COMMAND[@]}"
