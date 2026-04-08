#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ -f "${PROJECT_ROOT}/configs/paths.env" ]; then
  set -a
  . "${PROJECT_ROOT}/configs/paths.env"
  set +a
fi

PROJECT_ROOT_HPC="${PROJECT_ROOT_HPC:-${PROJECT_ROOT}}"
RAW_GRAPH_DIR="${RAW_GRAPH_DIR_HPC:-${RAW_GRAPH_DIR_LOCAL:-${PROJECT_ROOT_HPC}/data/raw/guidelines_graph}}"
DATASET_DIR_HPC="${DATASET_DIR_HPC:-${PROJECT_ROOT_HPC}/data/processed/cvd_guidelines_assoc}"
OUTPUT_DIR_HPC="${OUTPUT_DIR_HPC:-${PROJECT_ROOT_HPC}/outputs/cvd_assoc/checkpoints}"
LOG_DIR_HPC="${LOG_DIR_HPC:-${PROJECT_ROOT_HPC}/logs/slurm}"

export PROJECT_ROOT_HPC DATASET_DIR_HPC OUTPUT_DIR_HPC LOG_DIR_HPC

if [ "${RUN_PREPROCESS:-0}" = "1" ]; then
  PREPROCESS_CMD=(
    python3 -m cvd_biopathnet.cli convert
    --input "${RAW_GRAPH_DIR}"
    --output "${DATASET_DIR_HPC}"
    --reports-dir "${PROJECT_ROOT_HPC}/data/reports"
    --target-relation ASSOCIATED_WITH_CONDITION
    --seed "${PREPROCESS_SEED:-42}"
    --mode "${PREPROCESS_MODE:-pilot}"
    --pilot-target-limit "${PILOT_TARGET_LIMIT:-256}"
  )
  if [ -n "${PILOT_BACKGROUND_LIMIT:-}" ]; then
    PREPROCESS_CMD+=(--pilot-background-limit "${PILOT_BACKGROUND_LIMIT}")
  fi

  printf 'Running:'
  printf ' %q' "${PREPROCESS_CMD[@]}"
  printf '\n'
  "${PREPROCESS_CMD[@]}"

  python3 -m cvd_biopathnet.cli validate-dataset --dataset-dir "${DATASET_DIR_HPC}"
fi

train_job="$(sbatch "${PROJECT_ROOT}/scripts/submit_train.sbatch" | awk '{print $4}')"
echo "Submitted train job ${train_job}"

if [ "${SUBMIT_PREDICT:-1}" = "1" ]; then
  predict_job="$(sbatch --dependency=afterok:${train_job} "${PROJECT_ROOT}/scripts/submit_predict.sbatch" | awk '{print $4}')"
  echo "Submitted predict job ${predict_job}"
else
  predict_job=""
fi

if [ "${SUBMIT_VISUALIZE:-1}" = "1" ]; then
  if [ -n "${predict_job}" ]; then
    visualize_job="$(sbatch --dependency=afterok:${predict_job} "${PROJECT_ROOT}/scripts/submit_visualize.sbatch" | awk '{print $4}')"
  else
    visualize_job="$(sbatch --dependency=afterok:${train_job} "${PROJECT_ROOT}/scripts/submit_visualize.sbatch" | awk '{print $4}')"
  fi
  echo "Submitted visualize job ${visualize_job}"
fi
