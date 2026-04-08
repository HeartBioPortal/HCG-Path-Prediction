from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from cvd_biopathnet.io.detect import DetectionResult, detect_input_format
from cvd_biopathnet.models import RawGraph

NODE_ID_FIELDS = ("id", "node_id", "identifier")
NODE_TYPE_FIELDS = ("node_type", "type", "category", "kind", "label")
NODE_NAME_FIELDS = ("name", "display_name", "title", "canonical_name", "preferred_name", "label")
EDGE_SOURCE_FIELDS = ("source", "src", "from", "head")
EDGE_TARGET_FIELDS = ("target", "dst", "to", "tail")
EDGE_RELATION_FIELDS = ("relation", "predicate", "edge_type", "type", "label")


def load_graph(input_path: Path) -> RawGraph:
    detection = detect_input_format(input_path)
    if detection.format_name == "networkx_node_link_json":
        return _load_node_link_json(detection)
    if detection.format_name == "json_pair":
        return _load_json_pair(detection)
    if detection.format_name == "jsonl_pair":
        return _load_jsonl_pair(detection)
    if detection.format_name == "tabular_pair":
        return _load_tabular_pair(detection)
    if detection.format_name == "graphml":
        return _load_graphml(detection)
    raise ValueError(f"Unsupported detected format: {detection.format_name}")


def summarize_raw_graph(raw_graph: RawGraph, sample_limit: int = 5) -> dict[str, Any]:
    node_type_counts = Counter(node.get("label", "UNKNOWN") for node in raw_graph.nodes)
    relation_counts = Counter(edge.get("relation", "UNKNOWN") for edge in raw_graph.edges)
    return {
        "detected_format": raw_graph.detected_format,
        "source_files": raw_graph.source_files,
        "node_count": len(raw_graph.nodes),
        "edge_count": len(raw_graph.edges),
        "node_type_counts": dict(node_type_counts.most_common()),
        "relation_counts": dict(relation_counts.most_common()),
        "sample_nodes": raw_graph.nodes[:sample_limit],
        "sample_edges": raw_graph.edges[:sample_limit],
        "graph_metadata": raw_graph.graph_metadata,
    }


def _load_node_link_json(detection: DetectionResult) -> RawGraph:
    assert detection.node_file is not None
    payload = json.loads(detection.node_file.read_text())
    nodes = [_canonicalize_node(record, detection.node_file) for record in payload["nodes"]]
    edge_records = payload.get("edges", payload.get("links", []))
    edges = [_canonicalize_edge(record, detection.node_file) for record in edge_records]
    return RawGraph(
        nodes=nodes,
        edges=edges,
        source_files=[str(path) for path in detection.source_files],
        detected_format=detection.format_name,
        graph_metadata=payload.get("graph", {}),
    )


def _load_json_pair(detection: DetectionResult) -> RawGraph:
    assert detection.node_file is not None and detection.edge_file is not None
    node_payload = json.loads(detection.node_file.read_text())
    edge_payload = json.loads(detection.edge_file.read_text())
    nodes = [_canonicalize_node(record, detection.node_file) for record in _extract_records(node_payload, "nodes")]
    edges = [_canonicalize_edge(record, detection.edge_file) for record in _extract_records(edge_payload, "edges")]
    return RawGraph(
        nodes=nodes,
        edges=edges,
        source_files=[str(path) for path in detection.source_files],
        detected_format=detection.format_name,
    )


def _load_jsonl_pair(detection: DetectionResult) -> RawGraph:
    assert detection.node_file is not None and detection.edge_file is not None
    nodes = [
        _canonicalize_node(json.loads(line), detection.node_file)
        for line in detection.node_file.read_text().splitlines()
        if line.strip()
    ]
    edges = [
        _canonicalize_edge(json.loads(line), detection.edge_file)
        for line in detection.edge_file.read_text().splitlines()
        if line.strip()
    ]
    return RawGraph(
        nodes=nodes,
        edges=edges,
        source_files=[str(path) for path in detection.source_files],
        detected_format=detection.format_name,
    )


def _load_tabular_pair(detection: DetectionResult) -> RawGraph:
    assert detection.node_file is not None and detection.edge_file is not None
    nodes = [
        _canonicalize_node(record, detection.node_file)
        for record in _read_tabular_records(detection.node_file)
    ]
    edges = [
        _canonicalize_edge(record, detection.edge_file)
        for record in _read_tabular_records(detection.edge_file)
    ]
    return RawGraph(
        nodes=nodes,
        edges=edges,
        source_files=[str(path) for path in detection.source_files],
        detected_format=detection.format_name,
    )


def _load_graphml(detection: DetectionResult) -> RawGraph:
    assert detection.node_file is not None
    try:
        import networkx as nx
    except ImportError as exc:
        raise RuntimeError("GraphML support requires the `networkx` package.") from exc

    graph = nx.read_graphml(detection.node_file)
    nodes = [
        _canonicalize_node({"id": node_id, **attributes}, detection.node_file)
        for node_id, attributes in graph.nodes(data=True)
    ]

    edges: list[dict[str, Any]] = []
    if graph.is_multigraph():
        for source, target, key, attributes in graph.edges(keys=True, data=True):
            edges.append(
                _canonicalize_edge(
                    {"source": source, "target": target, "key": key, **attributes},
                    detection.node_file,
                )
            )
    else:
        for source, target, attributes in graph.edges(data=True):
            edges.append(
                _canonicalize_edge({"source": source, "target": target, **attributes}, detection.node_file)
            )

    return RawGraph(
        nodes=nodes,
        edges=edges,
        source_files=[str(path) for path in detection.source_files],
        detected_format=detection.format_name,
        graph_metadata=dict(graph.graph),
    )


def _canonicalize_node(record: dict[str, Any], source_file: Path) -> dict[str, Any]:
    node_id = _pick_required(record, NODE_ID_FIELDS, "node id", source_file)
    type_value, type_field = _pick_required_with_field(record, NODE_TYPE_FIELDS, "node type", source_file)
    name_value = _pick_optional(record, NODE_NAME_FIELDS)
    if name_value is None or (type_field == "label" and name_value == type_value):
        name_value = node_id
    canonical = dict(record)
    canonical["id"] = str(node_id)
    canonical["label"] = str(type_value)
    canonical["name"] = str(name_value)
    return canonical


def _canonicalize_edge(record: dict[str, Any], source_file: Path) -> dict[str, Any]:
    source = _pick_required(record, EDGE_SOURCE_FIELDS, "edge source", source_file)
    target = _pick_required(record, EDGE_TARGET_FIELDS, "edge target", source_file)
    relation = _pick_required(record, EDGE_RELATION_FIELDS, "edge relation", source_file)
    canonical = dict(record)
    canonical["source"] = str(source)
    canonical["target"] = str(target)
    canonical["relation"] = str(relation)
    return canonical


def _pick_required(
    record: dict[str, Any],
    fields: Iterable[str],
    label: str,
    source_file: Path,
) -> Any:
    value, _ = _pick_required_with_field(record, fields, label, source_file)
    return value


def _pick_required_with_field(
    record: dict[str, Any],
    fields: Iterable[str],
    label: str,
    source_file: Path,
) -> tuple[Any, str]:
    for field in fields:
        value = record.get(field)
        if value not in (None, ""):
            return value, field
    expected = ", ".join(fields)
    raise ValueError(f"Missing {label} in {source_file}. Expected one of: {expected}. Record: {record}")


def _pick_optional(record: dict[str, Any], fields: Iterable[str]) -> Any | None:
    for field in fields:
        value = record.get(field)
        if value not in (None, ""):
            return value
    return None


def _extract_records(payload: Any, key: str) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        records = payload.get(key)
        if isinstance(records, list):
            return records
    raise ValueError(f"Expected a JSON list or an object containing `{key}` records.")


def _read_tabular_records(path: Path) -> list[dict[str, str]]:
    delimiter = "\t" if path.suffix.lower() == ".tsv" else ","
    with path.open("r", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        return list(reader)
