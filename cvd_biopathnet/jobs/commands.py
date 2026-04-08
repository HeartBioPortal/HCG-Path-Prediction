from __future__ import annotations


def train_command(config_path: str = "configs/cvd_assoc_run.yaml") -> str:
    return (
        "python third_party/BioPathNet/script/run.py "
        "-s ${BIOPATHNET_SEED:-1024} "
        f"-c {config_path} "
        "--dataset_path \"${DATASET_DIR}\" "
        "--output_dir \"${OUTPUT_DIR}\" "
        "--gpus \"${BIOPATHNET_GPUS}\" "
        "--batch_size \"${BIOPATHNET_BATCH_SIZE}\" "
        "--num_epoch \"${BIOPATHNET_NUM_EPOCHS}\""
    )


def predict_command(config_path: str = "configs/cvd_assoc_vis.yaml") -> str:
    return (
        "python third_party/BioPathNet/script/predict.py "
        "-s ${BIOPATHNET_SEED:-1024} "
        f"-c {config_path} "
        "--dataset_path \"${DATASET_DIR}\" "
        "--output_dir \"${OUTPUT_DIR}\" "
        "--gpus \"${BIOPATHNET_GPUS}\" "
        "--batch_size \"${BIOPATHNET_BATCH_SIZE}\" "
        "--num_epoch \"${BIOPATHNET_NUM_EPOCHS}\" "
        "--checkpoint \"${CHECKPOINT_PATH}\""
    )


def visualize_command(config_path: str = "configs/cvd_assoc_vis.yaml") -> str:
    return (
        "python third_party/BioPathNet/script/visualize.py "
        "-s ${BIOPATHNET_SEED:-1024} "
        f"-c {config_path} "
        "--dataset_path \"${DATASET_DIR}\" "
        "--output_dir \"${OUTPUT_DIR}\" "
        "--gpus \"${BIOPATHNET_GPUS}\" "
        "--batch_size \"${BIOPATHNET_BATCH_SIZE}\" "
        "--num_epoch \"${BIOPATHNET_NUM_EPOCHS}\" "
        "--checkpoint \"${CHECKPOINT_PATH}\""
    )


def visualize_graph_command(config_path: str = "configs/cvd_assoc_vis.yaml") -> str:
    return (
        "python third_party/BioPathNet/script/visualize_graph.py "
        "-s ${BIOPATHNET_SEED:-1024} "
        f"-c {config_path} "
        "--dataset_path \"${DATASET_DIR}\" "
        "--output_dir \"${OUTPUT_DIR}\" "
        "--gpus \"${BIOPATHNET_GPUS}\" "
        "--batch_size \"${BIOPATHNET_BATCH_SIZE}\" "
        "--num_epoch \"${BIOPATHNET_NUM_EPOCHS}\" "
        "--checkpoint \"${CHECKPOINT_PATH}\""
    )
