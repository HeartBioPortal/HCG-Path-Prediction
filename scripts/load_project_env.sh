#!/usr/bin/env bash

load_project_env() {
  local project_root="$1"
  local env_file

  for env_file in "${project_root}/.env" "${project_root}/configs/paths.env"; do
    if [ -f "${env_file}" ]; then
      set -a
      # shellcheck disable=SC1090
      . "${env_file}"
      set +a
    fi
  done
}
