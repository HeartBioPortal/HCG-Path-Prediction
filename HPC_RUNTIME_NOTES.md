# HPC Runtime Notes

This repo's BioPathNet stack was debugged against a local `.venv` on HPC.

## Known good direction

- Prefer Python `3.10` when creating a fresh environment.
- CPU smoke tests can run with `torch==2.0.1+cpu`.
- `setuptools` must stay below `82` because `torch 2.0.1` still imports `pkg_resources`.
- NBFNet itself is officially documented around Python `3.7/3.8` and PyTorch `>= 1.8.0`, so the current Python `3.11` / Torch `2.0.1` stack should be treated as a pragmatic compatibility setup rather than the upstream-tested matrix.

## Symptom we hit

If verification or training fails with:

```text
ModuleNotFoundError: No module named 'pkg_resources'
```

pin setuptools back below `82`:

```bash
python -m pip install --force-reinstall "setuptools<82"
```

## Symptom we hit again

If a Slurm training run loads the dataset and then sits at:

```text
Epoch 0 begin
```

for hours without advancing, the official NBFNet FAQ says this is usually a broken Torch JIT extensions cache. Clear the cache and rerun:

```bash
scancel <jobid>
rm -rf "${TORCH_EXTENSIONS_DIR:-$HOME/.cache/torch_extensions}"
```

Then set:

```bash
BIOPATHNET_CLEAR_TORCH_EXTENSIONS=1
OMP_NUM_THREADS=1
MKL_NUM_THREADS=1
```

for the next smoke run. The repo's runtime scripts now honor those variables automatically.

## Reproducible setup

Copy the committed environment template first:

```bash
cp .env.example .env
```

The scripts load `.env` first and then `configs/paths.env` if it exists, so either file works. Use `.env` as the main committed-friendly template and `configs/paths.env` for local overrides if you want them.

Use the runtime bootstrapper:

```bash
ENV_MANAGER=venv BIOPATHNET_INSTALL_MODE=cpu bash scripts/setup_runtime_env.sh
```

The Slurm job scripts use the same environment selection logic. For a repo-local venv on HPC, keep:

```bash
ENV_MANAGER=venv
VENV_PATH=/N/u/kvand/BigRed200/HCG-Path-Prediction/.venv
OMP_NUM_THREADS=1
MKL_NUM_THREADS=1
TORCH_EXTENSIONS_DIR=/N/scratch/kvand/hbp/torch_extensions
BIOPATHNET_CLEAR_TORCH_EXTENSIONS=0
```

For GPU installs:

```bash
ENV_MANAGER=venv BIOPATHNET_INSTALL_MODE=gpu bash scripts/setup_runtime_env.sh
```

For IU HPC submission, set your RT project account before using the sbatch-first wrappers:

```bash
export SBATCH_ACCOUNT=r01806
```

or place it in `configs/paths.env`.

The Slurm templates now default to CPU-compatible submission. If you want GPU scheduling, opt in explicitly:

```bash
export SBATCH_GRES=gpu:1
export BIOPATHNET_GPUS='[0]'
```

## Visualization runtime

BioPathNet visualization is path explanation, not a normal static plot. It runs beam search over the graph for each query in `test_vis.txt`, and the original text-only explanation pass can run for hours on CPU before producing HTML/JSON files.

The project wrapper now defaults to a practical graph-only run:

```bash
BIOPATHNET_VISUALIZE_TEXT=0
BIOPATHNET_VISUALIZE_GRAPH=1
BIOPATHNET_VIS_BATCH_SIZE=1
BIOPATHNET_VIS_TEST_LIMIT=3
```

This should produce a few `.html` and `.json` artifacts quickly enough to verify the workflow. Set `BIOPATHNET_VIS_TEST_LIMIT=0` or `all` only for an exhaustive run. Set `BIOPATHNET_VISUALIZE_TEXT=1` only if you also want text path explanations in `log.txt`.

## Verification

```bash
python - <<'PY'
import setuptools
import pkg_resources
import torch
print("setuptools", setuptools.__version__)
print("torch", torch.__version__)
PY
```

The `pkg_resources` deprecation warning is expected with the pinned setuptools version and is acceptable for now.
