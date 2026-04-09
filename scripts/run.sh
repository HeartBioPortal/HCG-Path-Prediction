#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="${RUN_MODE:-auto}"
JOB="${1:-train}"
shift || true

if [ -f "${PROJECT_ROOT}/configs/paths.env" ]; then
  set -a
  . "${PROJECT_ROOT}/configs/paths.env"
  set +a
fi

build_sbatch_args() {
  local args=()
  local account="${SBATCH_ACCOUNT:-${SLURM_ACCOUNT:-}}"
  local partition="${SBATCH_PARTITION:-${SLURM_PARTITION:-}}"

  if [ -n "${account}" ]; then
    args+=(--account "${account}")
  fi

  if [ -n "${partition}" ]; then
    args+=(--partition "${partition}")
  fi

  printf '%s\n' "${args[@]}"
}

choose_mode() {
  case "${MODE}" in
    sbatch|local)
      printf '%s\n' "${MODE}"
      ;;
    auto)
      if command -v sbatch >/dev/null 2>&1; then
        printf '%s\n' "sbatch"
      else
        printf '%s\n' "local"
      fi
      ;;
    *)
      echo "Unsupported RUN_MODE=${MODE}. Use auto, sbatch, or local." >&2
      exit 1
      ;;
  esac
}

run_local() {
  case "${JOB}" in
    train)
      exec bash "${PROJECT_ROOT}/scripts/run_local_train.sh" "$@"
      ;;
    predict)
      exec bash "${PROJECT_ROOT}/scripts/run_local_predict.sh" "$@"
      ;;
    visualize)
      exec bash "${PROJECT_ROOT}/scripts/run_local_visualize.sh" "$@"
      ;;
    pipeline)
      echo "Local pipeline mode is not the default. Use RUN_MODE=sbatch for HPC submission." >&2
      exit 1
      ;;
    *)
      echo "Unknown job '${JOB}'. Use train, predict, visualize, or pipeline." >&2
      exit 1
      ;;
  esac
}

run_sbatch() {
  local sbatch_args=()
  while IFS= read -r line; do
    if [ -n "${line}" ]; then
      sbatch_args+=("${line}")
    fi
  done < <(build_sbatch_args)

  case "${JOB}" in
    train)
      exec sbatch "${sbatch_args[@]}" "${PROJECT_ROOT}/scripts/submit_train.sbatch" "$@"
      ;;
    predict)
      exec sbatch "${sbatch_args[@]}" "${PROJECT_ROOT}/scripts/submit_predict.sbatch" "$@"
      ;;
    visualize)
      exec sbatch "${sbatch_args[@]}" "${PROJECT_ROOT}/scripts/submit_visualize.sbatch" "$@"
      ;;
    pipeline)
      exec bash "${PROJECT_ROOT}/scripts/submit_pipeline.sh" "$@"
      ;;
    *)
      echo "Unknown job '${JOB}'. Use train, predict, visualize, or pipeline." >&2
      exit 1
      ;;
  esac
}

SELECTED_MODE="$(choose_mode)"
echo "Run mode: ${SELECTED_MODE}"
echo "Job: ${JOB}"

if [ "${SELECTED_MODE}" = "sbatch" ]; then
  run_sbatch "$@"
else
  run_local "$@"
fi
