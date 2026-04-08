from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable


def validate_dataset(dataset_dir: Path, *, write_report: bool = True) -> dict[str, object]:
    dataset_dir = dataset_dir.expanduser().resolve()
    required_triplet_files = {
        "train1": dataset_dir / "train1.txt",
        "train2": dataset_dir / "train2.txt",
        "valid": dataset_dir / "valid.txt",
        "test": dataset_dir / "test.txt",
        "test_vis": dataset_dir / "test_vis.txt",
    }
    required_map_files = {
        "entity_types": dataset_dir / "entity_types.txt",
        "entity_names": dataset_dir / "entity_names.txt",
        "metadata": dataset_dir / "metadata.json",
    }

    for name, path in {**required_triplet_files, **required_map_files}.items():
        if not path.exists():
            raise FileNotFoundError(f"Missing required dataset artifact `{name}` at {path}")

    triplets = {name: _read_triplets(path) for name, path in required_triplet_files.items()}
    entity_types = _read_simple_map(required_map_files["entity_types"], integer_values=True)
    entity_names = _read_simple_map(required_map_files["entity_names"], integer_values=False)
    metadata = json.loads(required_map_files["metadata"].read_text())

    duplicate_counts = {
        name: len(rows) - len(set(rows))
        for name, rows in triplets.items()
    }
    duplicates = {name: count for name, count in duplicate_counts.items() if count}
    if duplicates:
        raise ValueError(f"Duplicate triplets detected: {duplicates}")

    overlaps = {
        "train2_valid": len(set(triplets["train2"]) & set(triplets["valid"])),
        "train2_test": len(set(triplets["train2"]) & set(triplets["test"])),
        "valid_test": len(set(triplets["valid"]) & set(triplets["test"])),
    }
    bad_overlaps = {name: count for name, count in overlaps.items() if count}
    if bad_overlaps:
        raise ValueError(f"Split overlap detected: {bad_overlaps}")

    all_entities = {
        entity
        for rows in triplets.values()
        for head, _, tail in rows
        for entity in (head, tail)
    }
    missing_types = sorted(all_entities - set(entity_types))
    missing_names = sorted(all_entities - set(entity_names))
    if missing_types:
        raise ValueError(f"Entities missing from entity_types.txt: {missing_types[:10]}")
    if missing_names:
        raise ValueError(f"Entities missing from entity_names.txt: {missing_names[:10]}")

    expected_relation = metadata.get("target_relation", "ASSOCIATED_WITH_CONDITION")
    for split_name in ("valid", "test", "test_vis"):
        for head, relation, tail in triplets[split_name]:
            if relation != expected_relation:
                raise ValueError(
                    f"{split_name} contains relation {relation!r}, expected {expected_relation!r}"
                )
            if not head.startswith("GENE:") or not tail.startswith("CONDITION:"):
                raise ValueError(
                    f"{split_name} contains malformed target schema: {(head, relation, tail)}"
                )

    report = {
        "dataset_dir": str(dataset_dir),
        "triplet_counts": {name: len(rows) for name, rows in triplets.items()},
        "entity_count": len(all_entities),
        "duplicate_counts": duplicate_counts,
        "overlaps": overlaps,
        "target_relation": expected_relation,
        "checks": {
            "duplicates": True,
            "overlap": True,
            "entity_types_present": True,
            "entity_names_present": True,
            "target_schema_valid": True,
        },
    }

    if write_report:
        (dataset_dir / "validation_summary.json").write_text(json.dumps(report, indent=2, sort_keys=True))
    return report


def _read_triplets(path: Path) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for line_number, raw_line in enumerate(path.read_text().splitlines(), start=1):
        if not raw_line.strip():
            continue
        tokens = raw_line.split("\t")
        if len(tokens) != 3:
            raise ValueError(f"Malformed triplet row in {path}:{line_number}: {raw_line!r}")
        rows.append((tokens[0], tokens[1], tokens[2]))
    return rows


def _read_simple_map(path: Path, *, integer_values: bool) -> dict[str, int | str]:
    mapping: dict[str, int | str] = {}
    for line_number, raw_line in enumerate(path.read_text().splitlines(), start=1):
        if not raw_line.strip():
            continue
        tokens = raw_line.split("\t")
        if len(tokens) != 2:
            raise ValueError(f"Malformed map row in {path}:{line_number}: {raw_line!r}")
        key, value = tokens
        mapping[key] = int(value) if integer_values else value
    return mapping


def read_triplets(path: Path) -> list[tuple[str, str, str]]:
    return _read_triplets(path)
