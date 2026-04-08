from __future__ import annotations

from cvd_biopathnet.jobs.commands import (
    predict_command,
    train_command,
    visualize_command,
    visualize_graph_command,
)


def render_slurm_script(
    *,
    job: str,
    job_name: str | None = None,
    time_limit: str = "12:00:00",
    cpus: int = 8,
    memory: str = "48G",
    gpus: int = 1,
    conda_env_name: str = "biopathnet",
) -> str:
    effective_name = job_name or f"cvd_biopathnet_{job}"
    primary_command = _command_for_job(job)
    secondary_command = ""
    extra_body = ""
    if job == "predict":
        extra_body = _checkpoint_block()
    if job == "visualize":
        extra_body = _checkpoint_block()
        secondary_command = visualize_graph_command()

    gpu_directive = f"#SBATCH --gres=gpu:{gpus}" if gpus > 0 else ""
    output_subdir = {
        "train": "checkpoints",
        "predict": "predictions",
        "visualize": "visualizations",
    }[job]
    gpu_default = "[0]" if gpus > 0 else "null"

    return f"""#!/bin/bash
#SBATCH --job-name={effective_name}
#SBATCH --output=logs/slurm/%x-%j.out
#SBATCH --error=logs/slurm/%x-%j.err
#SBATCH --time={time_limit}
#SBATCH --cpus-per-task={cpus}
#SBATCH --mem={memory}
{gpu_directive}
# Optional cluster-specific lines:
##SBATCH --partition=gpu
##SBATCH --account=my_account

set -euo pipefail

PROJECT_ROOT="${{PROJECT_ROOT_HPC:-$PWD}}"
DATASET_DIR="${{DATASET_DIR_HPC:-$PROJECT_ROOT/data/processed/cvd_guidelines_assoc}}"
OUTPUT_DIR="${{OUTPUT_DIR_HPC:-$PROJECT_ROOT/outputs/cvd_assoc/{output_subdir}}}"
LOG_DIR="${{LOG_DIR_HPC:-$PROJECT_ROOT/logs/slurm}}"
BIOPATHNET_GPUS="${{BIOPATHNET_GPUS:-{gpu_default}}}"
BIOPATHNET_BATCH_SIZE="${{BIOPATHNET_BATCH_SIZE:-4}}"
BIOPATHNET_NUM_EPOCHS="${{BIOPATHNET_NUM_EPOCHS:-5}}"
CONDA_ENV_NAME="${{CONDA_ENV_NAME:-{conda_env_name}}}"

mkdir -p "$LOG_DIR"
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$CONDA_ENV_NAME"
cd "$PROJECT_ROOT"
{extra_body}
PRIMARY_COMMAND='{primary_command}'
echo "Running: $PRIMARY_COMMAND"
eval "$PRIMARY_COMMAND"
{_secondary_command_block(secondary_command)}
"""


def _command_for_job(job: str) -> str:
    if job == "train":
        return train_command()
    if job == "predict":
        return predict_command()
    if job == "visualize":
        return visualize_command()
    raise ValueError(f"Unsupported Slurm job type: {job}")


def _checkpoint_block() -> str:
    return """CHECKPOINT_PATH="${CHECKPOINT_PATH:-$(find "$PROJECT_ROOT/outputs/cvd_assoc/checkpoints" -name 'model_epoch_*.pth' | sort | tail -n 1)}"
if [ -z "${CHECKPOINT_PATH}" ]; then
  echo "No checkpoint found. Set CHECKPOINT_PATH explicitly."
  exit 1
fi"""

def _secondary_command_block(command: str) -> str:
    if not command:
        return ""
    return f"""SECONDARY_COMMAND='{command}'
echo "Running: $SECONDARY_COMMAND"
eval "$SECONDARY_COMMAND"
"""
