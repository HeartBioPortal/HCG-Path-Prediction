#!/usr/bin/env bash

activate_runtime_env() {
  local project_root="$1"
  local env_manager="${ENV_MANAGER:-auto}"
  local conda_env_name="${CONDA_ENV_NAME:-biopathnet}"
  local venv_path="${VENV_PATH:-${project_root}/.venv}"

  case "${env_manager}" in
    auto)
      if [ -n "${VIRTUAL_ENV:-}" ]; then
        return 0
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
}
