#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck disable=SC1091
. "${PROJECT_ROOT}/scripts/load_project_env.sh"
load_project_env "${PROJECT_ROOT}"

if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="${PYTHON_BIN:-python3}"
else
  PYTHON_BIN="${PYTHON_BIN:-python}"
fi

if [ -n "${PROJECT_ROOT_HPC:-}" ] && [ -d "${PROJECT_ROOT_HPC:-}" ] && [ "${PWD#${PROJECT_ROOT_HPC}}" != "${PWD}" ]; then
  CURRENT_SCOPE="HPC"
else
  CURRENT_SCOPE="LOCAL"
fi

RAW_GRAPH_DIR_DEFAULT="${PROJECT_ROOT}/data/raw/guidelines_graph"
EXTERNAL_BRG_SIF_DEFAULT="${PROJECT_ROOT}/data/raw/brg/pathway_commons_pc2_v14/pc-hgnc.sif.gz"
DATASET_DIR_DEFAULT="${PROJECT_ROOT}/data/processed/cvd_guidelines_assoc_pc14"
REPORTS_DIR_DEFAULT="${PROJECT_ROOT}/data/reports/pathway_commons_pc14"

if [ "${CURRENT_SCOPE}" = "HPC" ]; then
  RAW_GRAPH_DIR="${RAW_GRAPH_DIR_HPC:-${RAW_GRAPH_DIR:-${RAW_GRAPH_DIR_DEFAULT}}}"
  EXTERNAL_BRG_SIF="${EXTERNAL_BRG_SIF_HPC:-${EXTERNAL_BRG_SIF:-${EXTERNAL_BRG_SIF_DEFAULT}}}"
  OUTPUT_DATASET_DIR="${DATASET_DIR_WITH_EXTERNAL_BRG_HPC:-${DATASET_DIR_WITH_EXTERNAL_BRG:-${DATASET_DIR_DEFAULT}}}"
  REPORTS_DIR="${REPORTS_DIR_WITH_EXTERNAL_BRG_HPC:-${REPORTS_DIR_WITH_EXTERNAL_BRG:-${REPORTS_DIR_DEFAULT}}}"
else
  RAW_GRAPH_DIR="${RAW_GRAPH_DIR_LOCAL:-${RAW_GRAPH_DIR:-${RAW_GRAPH_DIR_DEFAULT}}}"
  EXTERNAL_BRG_SIF="${EXTERNAL_BRG_SIF_LOCAL:-${EXTERNAL_BRG_SIF:-${EXTERNAL_BRG_SIF_DEFAULT}}}"
  OUTPUT_DATASET_DIR="${DATASET_DIR_WITH_EXTERNAL_BRG_LOCAL:-${DATASET_DIR_WITH_EXTERNAL_BRG:-${DATASET_DIR_DEFAULT}}}"
  REPORTS_DIR="${REPORTS_DIR_WITH_EXTERNAL_BRG_LOCAL:-${REPORTS_DIR_WITH_EXTERNAL_BRG:-${REPORTS_DIR_DEFAULT}}}"
fi

TARGET_RELATION="${TARGET_RELATION:-ASSOCIATED_WITH_CONDITION}"
DATASET_MODE="${DATASET_MODE:-full}"
SPLIT_SEED="${SPLIT_SEED:-42}"
PILOT_TARGET_LIMIT="${PILOT_TARGET_LIMIT:-256}"
PILOT_BACKGROUND_LIMIT="${PILOT_BACKGROUND_LIMIT:-2000}"
BACKGROUND_NODE_TYPES="${BACKGROUND_NODE_TYPES:-Gene,Drug,Condition,Biomarker}"

background_type_args=()
if [ -n "${BACKGROUND_NODE_TYPES}" ]; then
  IFS=',' read -r -a background_type_array <<< "${BACKGROUND_NODE_TYPES}"
  for node_type in "${background_type_array[@]}"; do
    node_type="$(echo "${node_type}" | xargs)"
    if [ -n "${node_type}" ]; then
      background_type_args+=(--background-node-type "${node_type}")
    fi
  done
fi

echo "Rebuilding dataset with Pathway Commons BRG"
echo "  scope: ${CURRENT_SCOPE}"
echo "  raw graph: ${RAW_GRAPH_DIR}"
echo "  external BRG: ${EXTERNAL_BRG_SIF}"
echo "  output dataset: ${OUTPUT_DATASET_DIR}"
echo "  reports: ${REPORTS_DIR}"
echo "  mode: ${DATASET_MODE}"
echo "  internal background node types: ${BACKGROUND_NODE_TYPES}"

"${PYTHON_BIN}" -m cvd_biopathnet.cli convert \
  --input "${RAW_GRAPH_DIR}" \
  --output "${OUTPUT_DATASET_DIR}" \
  --reports-dir "${REPORTS_DIR}" \
  --target-relation "${TARGET_RELATION}" \
  --seed "${SPLIT_SEED}" \
  --mode "${DATASET_MODE}" \
  --pilot-target-limit "${PILOT_TARGET_LIMIT}" \
  --pilot-background-limit "${PILOT_BACKGROUND_LIMIT}" \
  --external-brg-sif "${EXTERNAL_BRG_SIF}" \
  "${background_type_args[@]}"

"${PYTHON_BIN}" -m cvd_biopathnet.cli validate-dataset --dataset-dir "${OUTPUT_DATASET_DIR}"

echo "Dataset with external BRG written to: ${OUTPUT_DATASET_DIR}"
