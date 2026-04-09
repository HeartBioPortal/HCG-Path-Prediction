# Default Run Mode

The canonical entrypoint for this project is now:

```bash
bash scripts/run.sh <job>
```

## Default behavior

When `RUN_MODE` is not set, the wrapper uses `auto` mode:

- if `sbatch` is available, it defaults to Slurm submission
- otherwise, it falls back to the local direct-run scripts

That means on HPC the default behavior is now batch submission instead of running training directly on the login node.

## Examples

Submit train on HPC:

```bash
bash scripts/run.sh train
```

Submit the dependent pipeline on HPC:

```bash
bash scripts/run.sh pipeline
```

Force a local smoke test:

```bash
RUN_MODE=local bash scripts/run.sh train
```

Force Slurm mode explicitly:

```bash
RUN_MODE=sbatch bash scripts/run.sh train
```
