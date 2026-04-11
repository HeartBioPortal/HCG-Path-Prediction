#!/bin/bash
#SBATCH --job-name=cvd_biopathnet_visualize
#SBATCH --output=logs/slurm/%x-%j.out
#SBATCH --error=logs/slurm/%x-%j.err
#SBATCH --time=04:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
##SBATCH --partition=gpu
##SBATCH --account=my_account
##SBATCH --gres=gpu:1

set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT_HPC:-$PWD}"
# shellcheck disable=SC1091
. "${PROJECT_ROOT}/scripts/load_project_env.sh"
load_project_env "${PROJECT_ROOT}"
# shellcheck disable=SC1091
. "${PROJECT_ROOT}/scripts/activate_runtime_env.sh"
DATASET_DIR="${DATASET_DIR_HPC:-$PROJECT_ROOT/data/processed/cvd_guidelines_assoc}"
OUTPUT_DIR="${VIS_OUTPUT_DIR_HPC:-$PROJECT_ROOT/outputs/cvd_assoc/visualizations}"
CONDA_ENV_NAME="${CONDA_ENV_NAME:-biopathnet}"
BIOPATHNET_GPUS="${BIOPATHNET_GPUS:-null}"
BIOPATHNET_BATCH_SIZE="${BIOPATHNET_BATCH_SIZE:-4}"
BIOPATHNET_VIS_BATCH_SIZE="${BIOPATHNET_VIS_BATCH_SIZE:-1}"
BIOPATHNET_NUM_EPOCHS="${BIOPATHNET_NUM_EPOCHS:-5}"
BIOPATHNET_SEED="${BIOPATHNET_SEED:-1024}"
BIOPATHNET_VIS_TEST_LIMIT="${BIOPATHNET_VIS_TEST_LIMIT:-3}"
BIOPATHNET_VISUALIZE_TEXT="${BIOPATHNET_VISUALIZE_TEXT:-0}"
BIOPATHNET_VISUALIZE_GRAPH="${BIOPATHNET_VISUALIZE_GRAPH:-1}"
VENV_PATH="${VENV_PATH:-${PROJECT_ROOT}/.venv}"
CHECKPOINT_PATH="${CHECKPOINT_PATH:-$(find "$PROJECT_ROOT/outputs/cvd_assoc/checkpoints" -name 'model_epoch_*.pth' | sort | tail -n 1)}"

if [ -z "$CHECKPOINT_PATH" ]; then
  echo "No checkpoint found. Set CHECKPOINT_PATH explicitly."
  exit 1
fi

mkdir -p "$PROJECT_ROOT/logs/slurm" "$OUTPUT_DIR"
activate_runtime_env "${PROJECT_ROOT}"
cd "$PROJECT_ROOT"

VIS_DATASET_DIR="$DATASET_DIR"
VIS_DATASET_TMP=""
case "$BIOPATHNET_VIS_TEST_LIMIT" in
  ""|0|all|ALL)
    ;;
  *)
    if ! [[ "$BIOPATHNET_VIS_TEST_LIMIT" =~ ^[0-9]+$ ]]; then
      echo "BIOPATHNET_VIS_TEST_LIMIT must be a positive integer, 0, or all." >&2
      exit 1
    fi
    mkdir -p "$OUTPUT_DIR/tmp"
    VIS_DATASET_TMP="$(mktemp -d "$OUTPUT_DIR/tmp/test_vis.XXXXXX")"
    cp -a "$DATASET_DIR/." "$VIS_DATASET_TMP/"
    head -n "$BIOPATHNET_VIS_TEST_LIMIT" "$DATASET_DIR/test_vis.txt" > "$VIS_DATASET_TMP/test_vis.txt"
    VIS_DATASET_DIR="$VIS_DATASET_TMP"
    echo "Using first $BIOPATHNET_VIS_TEST_LIMIT rows of test_vis.txt for visualization."
    echo "Temporary visualization dataset: $VIS_DATASET_DIR"
    trap 'if [ -n "${VIS_DATASET_TMP:-}" ] && [ "${BIOPATHNET_KEEP_VIS_DATASET:-0}" != "1" ]; then rm -rf "$VIS_DATASET_TMP"; fi' EXIT
    ;;
esac

VISUALIZE_COMMAND=(
  python third_party/BioPathNet/script/visualize.py
  -s "$BIOPATHNET_SEED"
  -c configs/cvd_assoc_vis.yaml
  --dataset_path "$VIS_DATASET_DIR"
  --output_dir "$OUTPUT_DIR"
  --gpus "$BIOPATHNET_GPUS"
  --batch_size "$BIOPATHNET_VIS_BATCH_SIZE"
  --num_epoch "$BIOPATHNET_NUM_EPOCHS"
  --checkpoint "$CHECKPOINT_PATH"
)

GRAPH_COMMAND=(
  python third_party/BioPathNet/script/visualize_graph.py
  -s "$BIOPATHNET_SEED"
  -c configs/cvd_assoc_vis.yaml
  --dataset_path "$VIS_DATASET_DIR"
  --output_dir "$OUTPUT_DIR"
  --gpus "$BIOPATHNET_GPUS"
  --batch_size "$BIOPATHNET_VIS_BATCH_SIZE"
  --num_epoch "$BIOPATHNET_NUM_EPOCHS"
  --checkpoint "$CHECKPOINT_PATH"
)

if [ "$BIOPATHNET_VISUALIZE_TEXT" = "1" ]; then
  printf 'Running text path explanations:'
  printf ' %q' "${VISUALIZE_COMMAND[@]}"
  printf '\n'
  "${VISUALIZE_COMMAND[@]}"
else
  echo "Skipping text-only path explanations. Set BIOPATHNET_VISUALIZE_TEXT=1 to enable them."
fi

if [ "$BIOPATHNET_VISUALIZE_GRAPH" = "1" ]; then
  printf 'Running graph visualizations:'
  printf ' %q' "${GRAPH_COMMAND[@]}"
  printf '\n'
  "${GRAPH_COMMAND[@]}"
else
  echo "Skipping graph visualizations because BIOPATHNET_VISUALIZE_GRAPH=$BIOPATHNET_VISUALIZE_GRAPH."
fi
