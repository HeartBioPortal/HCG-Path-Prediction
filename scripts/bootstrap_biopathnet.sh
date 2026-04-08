#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_DIR="${PROJECT_ROOT}/third_party/BioPathNet"
UPSTREAM_URL="${BIOPATHNET_UPSTREAM_URL:-https://github.com/emyyue/BioPathNet.git}"

if [ -d "${TARGET_DIR}/script" ]; then
  echo "BioPathNet is already present at ${TARGET_DIR}"
  exit 0
fi

mkdir -p "${PROJECT_ROOT}/third_party"
GIT_LFS_SKIP_SMUDGE=1 git clone "${UPSTREAM_URL}" "${TARGET_DIR}"
git -C "${TARGET_DIR}" -c filter.lfs.smudge= -c filter.lfs.process= -c filter.lfs.required=false checkout -f HEAD
echo "Vendored BioPathNet at ${TARGET_DIR}"
