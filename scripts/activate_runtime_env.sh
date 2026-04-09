#!/usr/bin/env bash

activate_runtime_env() {
  local project_root="$1"
  local env_manager="${ENV_MANAGER:-auto}"
  local conda_env_name="${CONDA_ENV_NAME:-biopathnet}"
  local venv_path="${VENV_PATH:-${project_root}/.venv}"
  local biopathnet_gpus="${BIOPATHNET_GPUS:-null}"
  local clear_torch_extensions="${BIOPATHNET_CLEAR_TORCH_EXTENSIONS:-0}"
  local torch_extensions_dir="${TORCH_EXTENSIONS_DIR:-}"
  local cache_dir=""

  case "${env_manager}" in
    auto)
      if [ -n "${VIRTUAL_ENV:-}" ]; then
        :
      elif [ -f "${venv_path}/bin/activate" ]; then
        # shellcheck disable=SC1090
        . "${venv_path}/bin/activate"
      elif command -v conda >/dev/null 2>&1; then
        # shellcheck disable=SC1091
        . "$(conda info --base)/etc/profile.d/conda.sh"
        conda activate "${conda_env_name}"
      else
        echo "No supported runtime environment found. Expected ${venv_path} or a conda install." >&2
        exit 1
      fi
      ;;
    venv)
      if [ ! -f "${venv_path}/bin/activate" ]; then
        echo "Virtualenv not found at ${venv_path}" >&2
        exit 1
      fi
      # shellcheck disable=SC1090
      . "${venv_path}/bin/activate"
      ;;
    conda)
      if ! command -v conda >/dev/null 2>&1; then
        echo "conda is not available but ENV_MANAGER=conda was requested." >&2
        exit 1
      fi
      # shellcheck disable=SC1091
      . "$(conda info --base)/etc/profile.d/conda.sh"
      conda activate "${conda_env_name}"
      ;;
    *)
      echo "Unsupported ENV_MANAGER=${env_manager}. Use auto, venv, or conda." >&2
      exit 1
      ;;
  esac

  if [ "${biopathnet_gpus}" = "null" ] || [ -z "${biopathnet_gpus}" ]; then
    export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
    export MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}"
  fi

  if [ -n "${torch_extensions_dir}" ]; then
    mkdir -p "${torch_extensions_dir}"
    export TORCH_EXTENSIONS_DIR="${torch_extensions_dir}"
  fi

  if [ "${clear_torch_extensions}" = "1" ]; then
    cache_dir="${TORCH_EXTENSIONS_DIR:-${HOME}/.cache/torch_extensions}"
    if [ -d "${cache_dir}" ]; then
      echo "Clearing torch extensions cache at ${cache_dir}"
      rm -rf "${cache_dir}"
    fi
    mkdir -p "${cache_dir}"
    export TORCH_EXTENSIONS_DIR="${cache_dir}"
  fi

  echo "Runtime environment ready:"
  echo "  ENV_MANAGER=${env_manager}"
  if [ -n "${VIRTUAL_ENV:-}" ]; then
    echo "  VIRTUAL_ENV=${VIRTUAL_ENV}"
  fi
  if [ -n "${TORCH_EXTENSIONS_DIR:-}" ]; then
    echo "  TORCH_EXTENSIONS_DIR=${TORCH_EXTENSIONS_DIR}"
  fi
  if [ "${biopathnet_gpus}" = "null" ] || [ -z "${biopathnet_gpus}" ]; then
    echo "  OMP_NUM_THREADS=${OMP_NUM_THREADS}"
    echo "  MKL_NUM_THREADS=${MKL_NUM_THREADS}"
  fi
}
