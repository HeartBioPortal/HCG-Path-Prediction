from __future__ import annotations

import argparse
import json
from pathlib import Path

from cvd_biopathnet.config import render_configs
from cvd_biopathnet.io.load_graph import load_graph, summarize_raw_graph
from cvd_biopathnet.jobs.slurm import render_slurm_script
from cvd_biopathnet.preprocess.convert import convert_to_biopathnet
from cvd_biopathnet.preprocess.validate import validate_dataset


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CVD BioPathNet project CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect-raw", help="Inspect a raw graph input")
    inspect_parser.add_argument("--input", required=True, type=Path)
    inspect_parser.add_argument("--sample-limit", type=int, default=5)

    convert_parser = subparsers.add_parser("convert", help="Convert a raw graph to BioPathNet files")
    convert_parser.add_argument("--input", required=True, type=Path)
    convert_parser.add_argument("--output", required=True, type=Path)
    convert_parser.add_argument("--reports-dir", type=Path, default=Path("data/reports"))
    convert_parser.add_argument("--target-relation", default="ASSOCIATED_WITH_CONDITION")
    convert_parser.add_argument("--seed", type=int, default=42)
    convert_parser.add_argument("--mode", choices=("pilot", "full"), default="full")
    convert_parser.add_argument("--pilot-target-limit", type=int, default=256)
    convert_parser.add_argument("--pilot-background-limit", type=int, default=None)
    convert_parser.add_argument("--exclude-relation", action="append", default=[])
    convert_parser.add_argument("--remove-self-loops", action="store_true")
    convert_parser.add_argument(
        "--external-brg-sif",
        type=Path,
        default=None,
        help="Optional Pathway Commons-style SIF file to merge into train1 / BRG.",
    )

    validate_parser = subparsers.add_parser("validate-dataset", help="Validate exported dataset files")
    validate_parser.add_argument("--dataset-dir", required=True, type=Path)

    render_parser = subparsers.add_parser("render-configs", help="Render BioPathNet config templates")
    render_parser.add_argument("--dataset-dir", required=True, type=Path)
    render_parser.add_argument("--output-dir", required=True, type=Path)

    slurm_parser = subparsers.add_parser("build-slurm", help="Render a Slurm script template")
    slurm_parser.add_argument("--job", required=True, choices=("train", "predict", "visualize"))
    slurm_parser.add_argument("--output", required=True, type=Path)
    slurm_parser.add_argument("--job-name")
    slurm_parser.add_argument("--time", default="12:00:00")
    slurm_parser.add_argument("--cpus", type=int, default=8)
    slurm_parser.add_argument("--mem", default="48G")
    slurm_parser.add_argument("--gpus", type=int, default=1)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "inspect-raw":
        graph = load_graph(args.input)
        summary = summarize_raw_graph(graph, sample_limit=args.sample_limit)
        print(json.dumps(summary, indent=2, sort_keys=True))
        return

    if args.command == "convert":
        result = convert_to_biopathnet(
            input_path=args.input,
            output_dir=args.output,
            reports_dir=args.reports_dir,
            target_relation=args.target_relation,
            seed=args.seed,
            mode=args.mode,
            pilot_target_limit=args.pilot_target_limit,
            pilot_background_limit=args.pilot_background_limit,
            excluded_relations=args.exclude_relation,
            remove_self_loops=args.remove_self_loops,
            external_brg_sif=args.external_brg_sif,
        )
        print(json.dumps(result.validation_report, indent=2, sort_keys=True))
        return

    if args.command == "validate-dataset":
        report = validate_dataset(args.dataset_dir)
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    if args.command == "render-configs":
        written = render_configs(args.output_dir)
        summary = {
            "dataset_dir": str(args.dataset_dir),
            "written_files": [str(path) for path in written],
        }
        print(json.dumps(summary, indent=2, sort_keys=True))
        return

    if args.command == "build-slurm":
        script = render_slurm_script(
            job=args.job,
            job_name=args.job_name,
            time_limit=args.time,
            cpus=args.cpus,
            memory=args.mem,
            gpus=args.gpus,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(script)
        print(json.dumps({"written": str(args.output)}, indent=2, sort_keys=True))
        return

    parser.error(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
