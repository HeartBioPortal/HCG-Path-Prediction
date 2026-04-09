#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_MANAGER="${ENV_MANAGER:-auto}"
CONDA_ENV_NAME="${CONDA_ENV_NAME:-biopathnet}"
VENV_PATH="${VENV_PATH:-${PROJECT_ROOT}/.venv}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
PYTHON_VERSION="${PYTHON_VERSION:-3.10}"
BIOPATHNET_INSTALL_MODE="${BIOPATHNET_INSTALL_MODE:-gpu}"
TORCH_WHL_URL_GPU="${TORCH_WHL_URL_GPU:-https://download.pytorch.org/whl/torch_stable.html}"
TORCH_WHL_URL_CPU="${TORCH_WHL_URL_CPU:-https://download.pytorch.org/whl/cpu}"
PYG_WHL_URL_GPU="${PYG_WHL_URL_GPU:-https://data.pyg.org/whl/torch-2.0.1+cu118.html}"
PYG_WHL_URL_CPU="${PYG_WHL_URL_CPU:-https://data.pyg.org/whl/torch-2.0.1+cpu.html}"
TORCHDRUG_DIR="${TORCHDRUG_DIR:-${PROJECT_ROOT}/third_party/torchdrug}"

if [ -f "${PROJECT_ROOT}/configs/paths.env" ]; then
  set -a
  . "${PROJECT_ROOT}/configs/paths.env"
  set +a
fi

if [ -n "${HPC_MODULES:-}" ]; then
  for module_name in ${HPC_MODULES}; do
    module load "${module_name}"
  done
fi

activate_conda_env() {
  source "$(conda info --base)/etc/profile.d/conda.sh"
  conda create -y -n "${CONDA_ENV_NAME}" "python=${PYTHON_VERSION}" || true
  conda activate "${CONDA_ENV_NAME}"
}

activate_venv() {
  if [ ! -d "${VENV_PATH}" ]; then
    "${PYTHON_BIN}" -m venv "${VENV_PATH}"
  fi
  # shellcheck disable=SC1091
  . "${VENV_PATH}/bin/activate"
}

activate_env() {
  case "${ENV_MANAGER}" in
    auto)
      if [ -n "${VIRTUAL_ENV:-}" ]; then
        echo "Using active virtual environment: ${VIRTUAL_ENV}"
      elif command -v conda >/dev/null 2>&1; then
        activate_conda_env
      else
        activate_venv
      fi
      ;;
    conda)
      activate_conda_env
      ;;
    venv)
      activate_venv
      ;;
    *)
      echo "Unsupported ENV_MANAGER=${ENV_MANAGER}. Use auto, conda, or venv."
      exit 1
      ;;
  esac
}

activate_env

python -m pip install --upgrade pip setuptools wheel

if [ "${BIOPATHNET_INSTALL_MODE}" = "gpu" ]; then
  pip install --no-cache-dir \
    torch==2.0.1+cu118 \
    torchvision==0.15.2+cu118 \
    torchaudio==2.0.2+cu118 \
    -f "${TORCH_WHL_URL_GPU}"
  pip install --no-cache-dir \
    pyg_lib torch_scatter torch_sparse torch_cluster torch_spline_conv \
    -f "${PYG_WHL_URL_GPU}"
else
  pip install --no-cache-dir \
    --index-url "${TORCH_WHL_URL_CPU}" \
    torch==2.0.1 \
    torchvision==0.15.2 \
    torchaudio==2.0.2
  pip install --no-cache-dir \
    pyg_lib torch_scatter torch_sparse torch_cluster torch_spline_conv \
    -f "${PYG_WHL_URL_CPU}"
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

pip install ogb easydict pyyaml jinja2 pandas
pip install numpy==1.26.4 --force-reinstall
pip install -e "${PROJECT_ROOT}"

python - <<'PY'
import torch
print("python", __import__("sys").version)
print("torch", torch.__version__)
print("cuda_available", torch.cuda.is_available())
print("cuda_device_count", torch.cuda.device_count())
PY
