#!/bin/bash
#SBATCH --job-name=cvd_biopathnet_train
#SBATCH --output=logs/slurm/%x-%j.out
#SBATCH --error=logs/slurm/%x-%j.err
#SBATCH --time=12:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
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
OUTPUT_DIR="${OUTPUT_DIR_HPC:-$PROJECT_ROOT/outputs/cvd_assoc/checkpoints}"
CONDA_ENV_NAME="${CONDA_ENV_NAME:-biopathnet}"
BIOPATHNET_GPUS="${BIOPATHNET_GPUS:-null}"
BIOPATHNET_BATCH_SIZE="${BIOPATHNET_BATCH_SIZE:-4}"
BIOPATHNET_NUM_EPOCHS="${BIOPATHNET_NUM_EPOCHS:-5}"
BIOPATHNET_SEED="${BIOPATHNET_SEED:-1024}"
VENV_PATH="${VENV_PATH:-${PROJECT_ROOT}/.venv}"

mkdir -p "$PROJECT_ROOT/logs/slurm" "$OUTPUT_DIR"
activate_runtime_env "${PROJECT_ROOT}"
cd "$PROJECT_ROOT"

COMMAND=(
  python third_party/BioPathNet/script/run.py
  -s "$BIOPATHNET_SEED"
  -c configs/cvd_assoc_run.yaml
  --dataset_path "$DATASET_DIR"
  --output_dir "$OUTPUT_DIR"
  --gpus "$BIOPATHNET_GPUS"
  --batch_size "$BIOPATHNET_BATCH_SIZE"
  --num_epoch "$BIOPATHNET_NUM_EPOCHS"
)

printf 'Running:'
printf ' %q' "${COMMAND[@]}"
printf '\n'
"${COMMAND[@]}"
