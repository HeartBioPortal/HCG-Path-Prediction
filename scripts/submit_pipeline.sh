#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ -f "${PROJECT_ROOT}/configs/paths.env" ]; then
  set -a
  . "${PROJECT_ROOT}/configs/paths.env"
  set +a
fi

build_sbatch_args() {
  local args=()
  local account="${SBATCH_ACCOUNT:-${SLURM_ACCOUNT:-}}"
  local partition="${SBATCH_PARTITION:-${SLURM_PARTITION:-}}"
  local gres="${SBATCH_GRES:-}"
  local cpus="${SBATCH_CPUS_PER_TASK:-}"
  local memory="${SBATCH_MEM:-}"
  local time_limit="${SBATCH_TIME:-}"
  local output_path="${SBATCH_OUTPUT:-}"
  local error_path="${SBATCH_ERROR:-}"
  local qos="${SBATCH_QOS:-}"

  if [ -n "${account}" ]; then
    args+=(--account "${account}")
  fi

  if [ -n "${partition}" ]; then
    args+=(--partition "${partition}")
  fi

  if [ -n "${gres}" ]; then
    args+=(--gres "${gres}")
  fi

  if [ -n "${cpus}" ]; then
    args+=(--cpus-per-task "${cpus}")
  fi

  if [ -n "${memory}" ]; then
    args+=(--mem "${memory}")
  fi

  if [ -n "${time_limit}" ]; then
    args+=(--time "${time_limit}")
  fi

  if [ -n "${output_path}" ]; then
    args+=(--output "${output_path}")
  fi

  if [ -n "${error_path}" ]; then
    args+=(--error "${error_path}")
  fi

  if [ -n "${qos}" ]; then
    args+=(--qos "${qos}")
  fi

  printf '%s\n' "${args[@]}"
}

PROJECT_ROOT_HPC="${PROJECT_ROOT_HPC:-${PROJECT_ROOT}}"
RAW_GRAPH_DIR="${RAW_GRAPH_DIR_HPC:-${RAW_GRAPH_DIR_LOCAL:-${PROJECT_ROOT_HPC}/data/raw/guidelines_graph}}"
DATASET_DIR_HPC="${DATASET_DIR_HPC:-${PROJECT_ROOT_HPC}/data/processed/cvd_guidelines_assoc}"
OUTPUT_DIR_HPC="${OUTPUT_DIR_HPC:-${PROJECT_ROOT_HPC}/outputs/cvd_assoc/checkpoints}"
LOG_DIR_HPC="${LOG_DIR_HPC:-${PROJECT_ROOT_HPC}/logs/slurm}"

export PROJECT_ROOT_HPC DATASET_DIR_HPC OUTPUT_DIR_HPC LOG_DIR_HPC

SBATCH_ARGS=()
while IFS= read -r line; do
  if [ -n "${line}" ]; then
    SBATCH_ARGS+=("${line}")
  fi
done < <(build_sbatch_args)

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

train_job="$(sbatch "${SBATCH_ARGS[@]}" "${PROJECT_ROOT}/scripts/submit_train.sbatch" | awk '{print $4}')"
echo "Submitted train job ${train_job}"

if [ "${SUBMIT_PREDICT:-1}" = "1" ]; then
  predict_job="$(sbatch "${SBATCH_ARGS[@]}" --dependency=afterok:${train_job} "${PROJECT_ROOT}/scripts/submit_predict.sbatch" | awk '{print $4}')"
  echo "Submitted predict job ${predict_job}"
else
  predict_job=""
fi

if [ "${SUBMIT_VISUALIZE:-1}" = "1" ]; then
  if [ -n "${predict_job}" ]; then
    visualize_job="$(sbatch "${SBATCH_ARGS[@]}" --dependency=afterok:${predict_job} "${PROJECT_ROOT}/scripts/submit_visualize.sbatch" | awk '{print $4}')"
  else
    visualize_job="$(sbatch "${SBATCH_ARGS[@]}" --dependency=afterok:${train_job} "${PROJECT_ROOT}/scripts/submit_visualize.sbatch" | awk '{print $4}')"
  fi
  echo "Submitted visualize job ${visualize_job}"
fi
