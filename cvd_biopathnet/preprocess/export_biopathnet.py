from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cvd_biopathnet.models import EdgeRecord, NodeRecord

DEFAULT_COLORS = [
    "#8f5682",
    "#f9844a",
    "#577590",
    "#277da1",
    "#f3722c",
    "#f94144",
    "#43aa8b",
    "#f9c74f",
    "#f8961e",
    "#90be6d",
]


def export_dataset(
    *,
    dataset_dir: Path,
    reports_dir: Path,
    nodes: dict[str, NodeRecord],
    background_edges: list[EdgeRecord],
    train_edges: list[EdgeRecord],
    valid_edges: list[EdgeRecord],
    test_edges: list[EdgeRecord],
    test_vis_edges: list[EdgeRecord],
    source_files: list[str],
    detected_format: str,
    target_relation: str,
    split_seed: int,
    mode: str,
    excluded_relations: list[str],
    graph_summary: dict[str, Any],
    extra_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    dataset_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "examples").mkdir(parents=True, exist_ok=True)

    all_edges = background_edges + train_edges + valid_edges + test_edges + test_vis_edges
    entity_ids = sorted({entity for edge in all_edges for entity in (edge.source, edge.target)})
    exported_nodes = {entity_id: nodes[entity_id] for entity_id in entity_ids}

    type_names = sorted({node.label for node in exported_nodes.values()})
    type_to_id = {label: index for index, label in enumerate(type_names)}

    _write_triplets(dataset_dir / "train1.txt", background_edges)
    _write_triplets(dataset_dir / "train2.txt", train_edges)
    _write_triplets(dataset_dir / "valid.txt", valid_edges)
    _write_triplets(dataset_dir / "test.txt", test_edges)
    _write_triplets(dataset_dir / "test_vis.txt", test_vis_edges)
    _write_entity_types(dataset_dir / "entity_types.txt", exported_nodes, type_to_id)
    _write_entity_names(dataset_dir / "entity_names.txt", exported_nodes)
    _write_node_colors(dataset_dir / "node_colors_dict.txt", type_to_id)
    _write_entity_metadata(dataset_dir / "entity_metadata.jsonl", exported_nodes)

    relation_counts = Counter(edge.relation for edge in all_edges)
    type_counts = Counter(node.label for node in exported_nodes.values())

    metadata = {
        "source_files": source_files,
        "detected_format": detected_format,
        "conversion_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "target_relation": target_relation,
        "target_schema": {
            "head_type": "Gene",
            "tail_type": "Condition",
        },
        "split_seed": split_seed,
        "counts_by_type": dict(type_counts.most_common()),
        "counts_by_relation": dict(relation_counts.most_common()),
        "mode": mode,
        "excluded_relations": excluded_relations,
        "type_to_id": type_to_id,
        "exported_files": {
            "train1": "train1.txt",
            "train2": "train2.txt",
            "valid": "valid.txt",
            "test": "test.txt",
            "test_vis": "test_vis.txt",
            "entity_types": "entity_types.txt",
            "entity_names": "entity_names.txt",
            "node_colors_dict": "node_colors_dict.txt",
            "entity_metadata": "entity_metadata.jsonl",
        },
    }
    if extra_metadata:
        metadata.update(extra_metadata)

    (dataset_dir / "metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True))

    split_stats = {
        "train1_count": len(background_edges),
        "train2_count": len(train_edges),
        "valid_count": len(valid_edges),
        "test_count": len(test_edges),
        "test_vis_count": len(test_vis_edges),
        "supervision_total": len(train_edges) + len(valid_edges) + len(test_edges),
    }
    (reports_dir / "split_stats.json").write_text(json.dumps(split_stats, indent=2, sort_keys=True))
    (reports_dir / "graph_summary.json").write_text(json.dumps(graph_summary, indent=2, sort_keys=True))

    example_payload = [
        {
            "head_id": edge.source,
            "head_name": exported_nodes[edge.source].name,
            "relation": edge.relation,
            "tail_id": edge.target,
            "tail_name": exported_nodes[edge.target].name,
        }
        for edge in test_vis_edges
    ]
    (reports_dir / "examples" / "test_vis_preview.json").write_text(
        json.dumps(example_payload, indent=2, sort_keys=True)
    )

    return metadata


def _write_triplets(path: Path, edges: list[EdgeRecord]) -> None:
    lines = ["\t".join(edge.triplet()) for edge in edges]
    path.write_text("\n".join(lines) + ("\n" if lines else ""))


def _write_entity_types(path: Path, nodes: dict[str, NodeRecord], type_to_id: dict[str, int]) -> None:
    lines = [f"{entity_id}\t{type_to_id[node.label]}" for entity_id, node in sorted(nodes.items())]
    path.write_text("\n".join(lines) + ("\n" if lines else ""))


def _write_entity_names(path: Path, nodes: dict[str, NodeRecord]) -> None:
    lines = [f"{entity_id}\t{node.name}" for entity_id, node in sorted(nodes.items())]
    path.write_text("\n".join(lines) + ("\n" if lines else ""))


def _write_node_colors(path: Path, type_to_id: dict[str, int]) -> None:
    lines = ["type\tcolor"]
    for index, type_name in sorted((index, type_name) for type_name, index in type_to_id.items()):
        color = DEFAULT_COLORS[index % len(DEFAULT_COLORS)]
        lines.append(f"{index}\t{color}")
    lines.append("99\t#DB2E34")
    path.write_text("\n".join(lines) + "\n")


def _write_entity_metadata(path: Path, nodes: dict[str, NodeRecord]) -> None:
    with path.open("w") as handle:
        for entity_id, node in sorted(nodes.items()):
            payload = {
                "entity_id": entity_id,
                "raw_id": node.raw_id,
                "label": node.label,
                "name": node.name,
                "attributes": node.attributes,
            }
            handle.write(json.dumps(payload, sort_keys=True) + "\n")
