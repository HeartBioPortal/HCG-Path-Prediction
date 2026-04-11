from __future__ import annotations

from pathlib import Path


RUN_CONFIG_TEMPLATE = """output_dir: {{ output_dir }}

dataset:
  class: biomedical
  path: {{ dataset_path }}
  include_factgraph: yes
  files: ['train1.txt', 'train2.txt', 'valid.txt', 'test.txt']

task:
  class: KnowledgeGraphCompletionBiomed
  model:
    class: NBFNet
    input_dim: 32
    hidden_dims: [32, 32, 32, 32, 32, 32]
    message_func: distmult
    aggregate_func: pna
    short_cut: yes
    layer_norm: yes
    dependent: yes
    symmetric: no
    num_beam: 3
    path_topk: 3
  criterion: bce
  num_negative: 32
  strict_negative: yes
  adversarial_temperature: 0.5
  sample_weight: no
  heterogeneous_negative: yes
  heterogeneous_evaluation: yes
  full_batch_eval: yes
  train2_in_factgraph: no

optimizer:
  class: Adam
  lr: 1.0e-3

engine:
  gpus: {{ gpus }}
  batch_size: {{ batch_size }}

train:
  num_epoch: {{ num_epoch }}

metric: mrr
"""


VIS_CONFIG_TEMPLATE = """output_dir: {{ output_dir }}

dataset:
  class: biomedical
  path: {{ dataset_path }}
  include_factgraph: yes
  files: ['train1.txt', 'train2.txt', 'valid.txt', 'test_vis.txt']

task:
  class: KnowledgeGraphCompletionBiomed
  model:
    class: NBFNet
    input_dim: 32
    hidden_dims: [32, 32, 32, 32, 32, 32]
    message_func: distmult
    aggregate_func: pna
    short_cut: yes
    layer_norm: yes
    dependent: yes
    symmetric: no
  criterion: bce
  num_negative: 32
  strict_negative: yes
  adversarial_temperature: 0.5
  sample_weight: no
  heterogeneous_negative: yes
  heterogeneous_evaluation: yes
  full_batch_eval: yes
  remove_pos: no
  train2_in_factgraph: no

optimizer:
  class: Adam
  lr: 1.0e-3

engine:
  gpus: {{ gpus }}
  batch_size: {{ batch_size }}

train:
  num_epoch: {{ num_epoch }}

metric: mrr

checkpoint: {{ checkpoint }}
"""


PATHS_EXAMPLE_TEMPLATE = """PROJECT_ROOT_LOCAL=/path/to/cvd-biopathnet
PROJECT_ROOT_HPC=/path/to/hpc/cvd-biopathnet
RAW_GRAPH_DIR_LOCAL=/path/to/cvd-biopathnet/data/raw/guidelines_graph
DATASET_DIR_HPC=/path/to/hpc/cvd-biopathnet/data/processed/cvd_guidelines_assoc
OUTPUT_DIR_HPC=/path/to/hpc/cvd-biopathnet/outputs/cvd_assoc
LOG_DIR_HPC=/path/to/hpc/cvd-biopathnet/logs
CONDA_ENV_NAME=biopathnet
HPC_REMOTE=user@login.cluster.example.edu
ENV_MANAGER=venv
VENV_PATH=/path/to/hpc/cvd-biopathnet/.venv
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
TORCH_EXTENSIONS_DIR=/path/to/hpc/scratch/torch_extensions
BIOPATHNET_CLEAR_TORCH_EXTENSIONS=0
SBATCH_ACCOUNT=my_account
SBATCH_CPUS_PER_TASK=4
SBATCH_MEM=48G
SBATCH_TIME=12:00:00
"""


def render_configs(output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written_files = []
    run_path = output_dir / "cvd_assoc_run.yaml"
    vis_path = output_dir / "cvd_assoc_vis.yaml"
    paths_example = output_dir / "paths.example.env"

    run_path.write_text(RUN_CONFIG_TEMPLATE)
    vis_path.write_text(VIS_CONFIG_TEMPLATE)
    if not paths_example.exists():
        paths_example.write_text(PATHS_EXAMPLE_TEMPLATE)

    written_files.extend([run_path, vis_path, paths_example])
    return written_files
