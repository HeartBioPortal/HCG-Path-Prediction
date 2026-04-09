#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONDA_ENV_NAME="${CONDA_ENV_NAME:-biopathnet}"
PYTHON_VERSION="${PYTHON_VERSION:-3.10}"
BIOPATHNET_INSTALL_MODE="${BIOPATHNET_INSTALL_MODE:-gpu}"
TORCH_WHL_URL="${TORCH_WHL_URL:-https://download.pytorch.org/whl/torch_stable.html}"
PYG_WHL_URL="${PYG_WHL_URL:-https://data.pyg.org/whl/torch-2.0.1+cu118.html}"
TORCHDRUG_DIR="${TORCHDRUG_DIR:-${PROJECT_ROOT}/third_party/torchdrug}"

# shellcheck disable=SC1091
. "${PROJECT_ROOT}/scripts/load_project_env.sh"
load_project_env "${PROJECT_ROOT}"

if [ -n "${HPC_MODULES:-}" ]; then
  for module_name in ${HPC_MODULES}; do
    module load "${module_name}"
  done
fi

source "$(conda info --base)/etc/profile.d/conda.sh"
conda create -y -n "${CONDA_ENV_NAME}" "python=${PYTHON_VERSION}" || true
conda activate "${CONDA_ENV_NAME}"

python -m pip install --upgrade pip setuptools wheel

if [ "${BIOPATHNET_INSTALL_MODE}" = "gpu" ]; then
  pip install --no-cache-dir \
    torch==2.0.1+cu118 \
    torchvision==0.15.2+cu118 \
    torchaudio==2.0.2+cu118 \
    -f "${TORCH_WHL_URL}"
  pip install --no-cache-dir \
    pyg_lib torch_scatter torch_sparse torch_cluster torch_spline_conv \
    -f "${PYG_WHL_URL}"
else
  pip install --no-cache-dir torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2
fi

if [ ! -d "${TORCHDRUG_DIR}" ]; then
  git clone https://github.com/DeepGraphLearning/torchdrug "${TORCHDRUG_DIR}"
fi

pushd "${TORCHDRUG_DIR}" >/dev/null
pip install -r requirements.txt
python setup.py install
popd >/dev/null

pushd "${PROJECT_ROOT}/third_party/BioPathNet" >/dev/null
pip install -r requirements.txt
popd >/dev/null

pip install ogb easydict pyyaml jinja2
pip install numpy==1.26.4 --force-reinstall
pip install -e "${PROJECT_ROOT}"

python - <<'PY'
import torch
print("python", __import__("sys").version)
print("torch", torch.__version__)
print("cuda_available", torch.cuda.is_available())
print("cuda_device_count", torch.cuda.device_count())
PY
