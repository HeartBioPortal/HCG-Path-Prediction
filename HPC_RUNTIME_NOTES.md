# HPC Runtime Notes

This repo's BioPathNet stack was debugged against a local `.venv` on HPC.

## Known good direction

- Prefer Python `3.10` when creating a fresh environment.
- CPU smoke tests can run with `torch==2.0.1+cpu`.
- `setuptools` must stay below `82` because `torch 2.0.1` still imports `pkg_resources`.

## Symptom we hit

If verification or training fails with:

```text
ModuleNotFoundError: No module named 'pkg_resources'
```

pin setuptools back below `82`:

```bash
python -m pip install --force-reinstall "setuptools<82"
```

## Reproducible setup

Use the runtime bootstrapper:

```bash
ENV_MANAGER=venv BIOPATHNET_INSTALL_MODE=cpu bash scripts/setup_runtime_env.sh
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
