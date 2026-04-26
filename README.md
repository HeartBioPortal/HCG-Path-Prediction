# cvd-biopathnet

`cvd-biopathnet` is a local-plus-HPC workflow for converting a cardiovascular guideline knowledge graph into BioPathNet datasets, then running training, prediction, and path visualization either directly on a laptop or through Slurm on HPC.

The project is designed around the first prediction task:

- head type: `Gene`
- relation: `ASSOCIATED_WITH_CONDITION`
- tail type: `Condition`

All other relations are exported into `train1.txt` as the BioPathNet background regulatory graph (BRG). Training positives for the target task are exported into `train2.txt`, with deterministic `valid.txt` and `test.txt` splits.

## What is included

- A format detector and raw graph loader that supports node-link JSON, GraphML, paired JSON / JSONL files, and paired CSV / TSV node+edge tables.
- A normalization pipeline for entity IDs, relation names, deduplication, and task extraction.
- BioPathNet dataset export with `train1`, `train2`, `valid`, `test`, `test_vis`, `entity_types`, `entity_names`, `node_colors_dict`, and `metadata`.
- Validation tooling for duplicate checks, split overlap checks, exported entity map checks, and target-schema checks.
- A downloaded external BRG candidate from Pathway Commons at [data/raw/brg/pathway_commons_pc2_v14](/Users/kvand/Documents/B528-class/project/data/raw/brg/pathway_commons_pc2_v14).
- Rendered BioPathNet config templates in [configs/cvd_assoc_run.yaml](/Users/kvand/Documents/B528-class/project/configs/cvd_assoc_run.yaml) and [configs/cvd_assoc_vis.yaml](/Users/kvand/Documents/B528-class/project/configs/cvd_assoc_vis.yaml).
- Local run scripts, Slurm batch scripts, laptop-to-HPC sync scripts, and a small prediction-inspection notebook.
- Vendored upstream BioPathNet code in [third_party/BioPathNet](/Users/kvand/Documents/B528-class/project/third_party/BioPathNet).

## Local development workflow

Install the project package first so the CLI and helper modules are available:

```bash
python3 -m pip install -e .
```

Inspect the raw graph:

```bash
python3 -m cvd_biopathnet.cli inspect-raw --input data/raw/guidelines_graph
```

Convert the graph into a pilot BioPathNet dataset:

```bash
python3 -m cvd_biopathnet.cli convert \
  --input data/raw/guidelines_graph \
  --output data/processed/cvd_guidelines_assoc \
  --reports-dir data/reports \
  --target-relation ASSOCIATED_WITH_CONDITION \
  --seed 42 \
  --mode pilot \
  --pilot-target-limit 256 \
  --pilot-background-limit 2000
```

Validate the exported dataset:

```bash
python3 -m cvd_biopathnet.cli validate-dataset --dataset-dir data/processed/cvd_guidelines_assoc
```

Render the BioPathNet config templates:

```bash
python3 -m cvd_biopathnet.cli render-configs \
  --dataset-dir data/processed/cvd_guidelines_assoc \
  --output-dir configs
```

Run local training, prediction, and visualization:

```bash
bash scripts/run_local_train.sh
bash scripts/run_local_predict.sh
bash scripts/run_local_visualize.sh
```

The local run scripts default to CPU mode with `--gpus null`. Set `BIOPATHNET_GPUS="[0]"` in your environment if you want to target a local GPU.

## HPC workflow

Copy the committed environment template first:

```bash
cp .env.example .env
```

The project scripts load `.env` first and then `configs/paths.env` if it exists, so you can either keep everything in `.env` or use `configs/paths.env` for local machine-specific overrides. A second template also exists at [configs/paths.example.env](/Users/kvand/Documents/B528-class/project/configs/paths.example.env).

Recommended IU HPC variables:

```bash
PROJECT_ROOT_HPC=/N/u/kvand/BigRed200/HCG-Path-Prediction
RAW_GRAPH_DIR_HPC=/N/u/kvand/BigRed200/HCG-Path-Prediction/data/raw/guidelines_graph
DATASET_DIR_HPC=/N/u/kvand/BigRed200/HCG-Path-Prediction/data/processed/cvd_guidelines_assoc
OUTPUT_DIR_HPC=/N/u/kvand/BigRed200/HCG-Path-Prediction/outputs/cvd_assoc/checkpoints
PREDICTION_OUTPUT_DIR_HPC=/N/u/kvand/BigRed200/HCG-Path-Prediction/outputs/cvd_assoc/predictions
VIS_OUTPUT_DIR_HPC=/N/u/kvand/BigRed200/HCG-Path-Prediction/outputs/cvd_assoc/visualizations
LOG_DIR_HPC=/N/scratch/kvand/hbp/logs/datahub
ENV_MANAGER=venv
VENV_PATH=/N/u/kvand/BigRed200/HCG-Path-Prediction/.venv
BIOPATHNET_INSTALL_MODE=cpu
BIOPATHNET_GPUS=null
BIOPATHNET_BATCH_SIZE=4
BIOPATHNET_NUM_EPOCHS=5
BIOPATHNET_SEED=1024
BIOPATHNET_VIS_BATCH_SIZE=1
BIOPATHNET_VIS_TEST_LIMIT=3
BIOPATHNET_VISUALIZE_TEXT=0
BIOPATHNET_VISUALIZE_GRAPH=1
OMP_NUM_THREADS=1
MKL_NUM_THREADS=1
TORCH_EXTENSIONS_DIR=/N/scratch/kvand/hbp/torch_extensions
BIOPATHNET_CLEAR_TORCH_EXTENSIONS=0
SBATCH_ACCOUNT=r01806
SBATCH_CPUS_PER_TASK=4
SBATCH_MEM=48G
SBATCH_TIME=12:00:00
SBATCH_OUTPUT=/N/scratch/kvand/hbp/logs/datahub/cvd_train_%j.out
SBATCH_ERROR=/N/scratch/kvand/hbp/logs/datahub/cvd_train_%j.err
```

For GPU submission, opt in explicitly:

```bash
SBATCH_GRES=gpu:1
BIOPATHNET_GPUS='[0]'
```

Sync the repo to HPC:

```bash
bash scripts/sync_to_hpc.sh
```

On the cluster:

```bash
cd <PROJECT_ROOT_HPC>
bash scripts/setup_runtime_env.sh
bash scripts/run_train.sh
```

Submit the full dependent pipeline:

```bash
bash scripts/run_pipeline.sh
```

The canonical `run_*` wrappers default to `sbatch` on HPC and can pass through account, CPU, memory, time, output, error, partition, QOS, and GPU flags from `.env` or `configs/paths.env`. The Slurm job scripts now also honor `ENV_MANAGER=venv` with `VENV_PATH`, so they no longer assume Conda is installed on the compute nodes. The pipeline wrapper can optionally preprocess first, then submit train, predict, and visualization jobs using Slurm dependencies.

For CPU smoke runs, the runtime activation layer now also honors:

- `OMP_NUM_THREADS`
- `MKL_NUM_THREADS`
- `TORCH_EXTENSIONS_DIR`
- `BIOPATHNET_CLEAR_TORCH_EXTENSIONS`

Visualization is intentionally limited by default because BioPathNet path explanation uses beam search over the graph and can be much slower than prediction. The wrapper skips the text-only explanation pass unless `BIOPATHNET_VISUALIZE_TEXT=1`, runs the HTML/JSON graph pass by default with `BIOPATHNET_VISUALIZE_GRAPH=1`, uses `BIOPATHNET_VIS_BATCH_SIZE=1`, and limits `test_vis.txt` to the first `BIOPATHNET_VIS_TEST_LIMIT=3` rows. Set `BIOPATHNET_VIS_TEST_LIMIT=0` or `all` only if you really want every visualization query.

## Data files and BioPathNet semantics

- `train1.txt`: all non-target relations, used as the BRG / fact graph.
- `train2.txt`: training positives only for `Gene --ASSOCIATED_WITH_CONDITION--> Condition`.
- `valid.txt`: validation positives for the same target relation.
- `test.txt`: test positives for the same target relation.
- `test_vis.txt`: a small subset of test triplets used by the default predict / visualize workflow.
- `entity_types.txt`: entity ID to integer type ID.
- `entity_names.txt`: entity ID to readable display name.
- `node_colors_dict.txt`: integer type ID to visualization color, plus the query highlight color.
- `metadata.json`: source files, format, counts, split seed, target relation, and export metadata.

The exported entity IDs are namespaced and type-aware, for example `GENE:SCN5A` and `CONDITION:c4a2be2e451c52d3`.

## External BRG candidate

The current best-fit external BRG candidate for this project is Pathway Commons PC2 v14, downloaded in HGNC SIF form at [data/raw/brg/pathway_commons_pc2_v14](/Users/kvand/Documents/B528-class/project/data/raw/brg/pathway_commons_pc2_v14). This is the graph I would start with because it closely matches the BRG role described in BioPathNet and integrates pathway / interaction sources such as Reactome, PhosphoSite, BioGRID, IntAct, DrugBank, and others.

The raw file is:

- [data/raw/brg/pathway_commons_pc2_v14/pc-hgnc.sif.gz](/Users/kvand/Documents/B528-class/project/data/raw/brg/pathway_commons_pc2_v14/pc-hgnc.sif.gz)

Before using it in `train1.txt`, we should map identifiers into the project namespace and filter any edges that could leak direct target supervision.

## Pilot and full mode

- `--mode pilot` keeps the workflow lightweight by sampling a deterministic subset of target edges and a focused background graph.
- `--mode full` exports all target positives and all non-target BRG edges.

Pilot mode is useful for laptop testing and for smoke-checking the HPC pipeline before a full run.

## Successful pilot path

The provided `networkx_graph.json` was converted successfully with the pilot command above. The resulting validated pilot dataset contains:

- `train1.txt`: 2,000 BRG triplets
- `train2.txt`: 204 training target triplets
- `valid.txt`: 26 validation triplets
- `test.txt`: 26 test triplets
- `test_vis.txt`: 25 visualization triplets

Validation output is written to [data/processed/cvd_guidelines_assoc/validation_summary.json](/Users/kvand/Documents/B528-class/project/data/processed/cvd_guidelines_assoc/validation_summary.json), and graph / split summaries are written under [data/reports](/Users/kvand/Documents/B528-class/project/data/reports).

## Slurm usage

Committed templates are provided in:

- [scripts/submit_train.sbatch](/Users/kvand/Documents/B528-class/project/scripts/submit_train.sbatch)
- [scripts/submit_predict.sbatch](/Users/kvand/Documents/B528-class/project/scripts/submit_predict.sbatch)
- [scripts/submit_visualize.sbatch](/Users/kvand/Documents/B528-class/project/scripts/submit_visualize.sbatch)

You can also render fresh templates programmatically:

```bash
python3 -m cvd_biopathnet.cli build-slurm --job train --output scripts/submit_train.sbatch
python3 -m cvd_biopathnet.cli build-slurm --job predict --output scripts/submit_predict.sbatch
python3 -m cvd_biopathnet.cli build-slurm --job visualize --output scripts/submit_visualize.sbatch
```

## Common failure modes

- `ModuleNotFoundError: cvd_biopathnet`: install the project with `python3 -m pip install -e .`, or run from the repo root after installation.
- `No checkpoint found`: run training first, or set `CHECKPOINT_PATH` before prediction / visualization.
- `torchdrug` / PyG install failures on HPC: use [scripts/setup_runtime_env.sh](/Users/kvand/Documents/B528-class/project/scripts/setup_runtime_env.sh) and adjust `HPC_MODULES`, CUDA wheel URLs, or `BIOPATHNET_INSTALL_MODE=cpu`.
- Slurm account or partition errors: uncomment and edit the optional `#SBATCH` lines in the batch templates for your cluster.
- Training loads the dataset but stays at `Epoch 0 begin`: this is a known NBFNet symptom of a broken Torch JIT cache. Set `BIOPATHNET_CLEAR_TORCH_EXTENSIONS=1`, keep `TORCH_EXTENSIONS_DIR` on scratch if possible, and rerun a 1-epoch smoke test.
- Visualization runs for hours with only `log.txt`: cancel it, pull the latest repo, and rerun with the default graph-only limited settings. The text-only path pass can be much slower than the HTML/JSON graph output and is now opt-in via `BIOPATHNET_VISUALIZE_TEXT=1`.
- Raw-format detection errors: ensure the input directory contains a supported schema with node IDs, node types, edge sources, edge targets, and edge relations.


## HPC Runtime Notes

For HPC `.venv` setup, use:

```bash
ENV_MANAGER=venv BIOPATHNET_INSTALL_MODE=cpu bash scripts/setup_runtime_env.sh
```

Use `BIOPATHNET_INSTALL_MODE=gpu` for CUDA installs. This workflow also pins `setuptools<82` because `torch==2.0.1` still imports `pkg_resources`.

If a job appears stuck immediately after `Epoch 0 begin`, clear the Torch JIT cache before retrying:

```bash
rm -rf "${TORCH_EXTENSIONS_DIR:-$HOME/.cache/torch_extensions}"
```

Then submit a tiny smoke job with:

```bash
export BIOPATHNET_CLEAR_TORCH_EXTENSIONS=1
export BIOPATHNET_NUM_EPOCHS=1
export BIOPATHNET_BATCH_SIZE=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
bash scripts/run_train.sh
```

## Default Run Mode On HPC

The canonical run wrappers are now:

```bash
bash scripts/run_train.sh
bash scripts/run_predict.sh
bash scripts/run_visualize.sh
bash scripts/run_pipeline.sh
```

When `sbatch` is available, these wrappers default to Slurm submission instead of running directly on the login node. To force the older direct-run path for smoke tests, use:

```bash
RUN_MODE=local bash scripts/run_train.sh
```

On IU HPC, set your RT project account before using the sbatch-first wrappers:

```bash
export SBATCH_ACCOUNT=r01806
```

You can also store that value in `configs/paths.env`.

The submitted Slurm templates now default to CPU-compatible runs. To match a CPU-style submission similar to your previous jobs, you can also set:

```bash
export SBATCH_CPUS_PER_TASK=4
export SBATCH_MEM=48G
export SBATCH_TIME=12:00:00
export BIOPATHNET_GPUS=null
```

If you want a GPU job instead, opt in explicitly with:

```bash
export SBATCH_GRES=gpu:1
export BIOPATHNET_GPUS='[0]'
```
