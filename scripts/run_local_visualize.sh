#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ -f "${PROJECT_ROOT}/configs/paths.env" ]; then
  set -a
  . "${PROJECT_ROOT}/configs/paths.env"
  set +a
fi

PROJECT_ROOT_LOCAL="${PROJECT_ROOT_LOCAL:-${PROJECT_ROOT}}"
DATASET_DIR="${DATASET_DIR_LOCAL:-${DATASET_DIR:-${PROJECT_ROOT_LOCAL}/data/processed/cvd_guidelines_assoc}}"
OUTPUT_DIR="${VIS_OUTPUT_DIR_LOCAL:-${PROJECT_ROOT_LOCAL}/outputs/cvd_assoc/visualizations}"
BIOPATHNET_GPUS="${BIOPATHNET_GPUS:-null}"
BIOPATHNET_BATCH_SIZE="${BIOPATHNET_BATCH_SIZE:-4}"
BIOPATHNET_NUM_EPOCHS="${BIOPATHNET_NUM_EPOCHS:-5}"
BIOPATHNET_SEED="${BIOPATHNET_SEED:-1024}"
CHECKPOINT_PATH="${CHECKPOINT_PATH:-$(find "${PROJECT_ROOT_LOCAL}/outputs/cvd_assoc/checkpoints" -name 'model_epoch_*.pth' | sort | tail -n 1)}"

mkdir -p "${PROJECT_ROOT_LOCAL}/logs/local" "${OUTPUT_DIR}"
LOG_FILE="${PROJECT_ROOT_LOCAL}/logs/local/visualize-$(date +%Y%m%d-%H%M%S).log"
exec > >(tee -a "${LOG_FILE}") 2>&1

cd "${PROJECT_ROOT_LOCAL}"

if [ -z "${CHECKPOINT_PATH}" ]; then
  echo "No checkpoint found. Set CHECKPOINT_PATH or run training first."
  exit 1
fi

VISUALIZE_COMMAND=(
  python third_party/BioPathNet/script/visualize.py
  -s "${BIOPATHNET_SEED}"
  -c configs/cvd_assoc_vis.yaml
  --dataset_path "${DATASET_DIR}"
  --output_dir "${OUTPUT_DIR}"
  --gpus "${BIOPATHNET_GPUS}"
  --batch_size "${BIOPATHNET_BATCH_SIZE}"
  --num_epoch "${BIOPATHNET_NUM_EPOCHS}"
  --checkpoint "${CHECKPOINT_PATH}"
)

GRAPH_COMMAND=(
  python third_party/BioPathNet/script/visualize_graph.py
  -s "${BIOPATHNET_SEED}"
  -c configs/cvd_assoc_vis.yaml
  --dataset_path "${DATASET_DIR}"
  --output_dir "${OUTPUT_DIR}"
  --gpus "${BIOPATHNET_GPUS}"
  --batch_size "${BIOPATHNET_BATCH_SIZE}"
  --num_epoch "${BIOPATHNET_NUM_EPOCHS}"
  --checkpoint "${CHECKPOINT_PATH}"
)

printf 'Running:'
printf ' %q' "${VISUALIZE_COMMAND[@]}"
printf '\n'
"${VISUALIZE_COMMAND[@]}"

printf 'Running:'
printf ' %q' "${GRAPH_COMMAND[@]}"
printf '\n'
"${GRAPH_COMMAND[@]}"
