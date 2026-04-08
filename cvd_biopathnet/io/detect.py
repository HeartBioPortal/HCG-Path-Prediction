from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


class DetectionError(RuntimeError):
    """Raised when the raw graph format cannot be determined safely."""


@dataclass(slots=True)
class DetectionResult:
    format_name: str
    source_files: list[Path]
    node_file: Path | None = None
    edge_file: Path | None = None


def detect_input_format(input_path: Path) -> DetectionResult:
    path = input_path.expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"Input path does not exist: {path}")

    if path.is_file():
        return _detect_file(path)
    return _detect_directory(path)


def _detect_file(path: Path) -> DetectionResult:
    suffix = path.suffix.lower()
    if suffix == ".graphml":
        return DetectionResult("graphml", [path], node_file=path)
    if suffix == ".json":
        if _looks_like_node_link_json(path):
            return DetectionResult("networkx_node_link_json", [path], node_file=path)
        raise DetectionError(
            f"Unsupported JSON schema in {path}. Expected a node-link JSON object with "
            f"`nodes` and `edges` (or `links`)."
        )
    if suffix == ".jsonl":
        raise DetectionError(
            f"Single JSONL file {path} is ambiguous. Provide a directory with paired "
            f"`nodes.jsonl` and `edges.jsonl` files."
        )
    if suffix in {".csv", ".tsv"}:
        raise DetectionError(
            f"Single tabular file {path} is ambiguous. Provide a directory with paired "
            f"node and edge tables."
        )
    raise DetectionError(f"Unsupported input file type: {path.suffix or '<no extension>'}")


def _detect_directory(path: Path) -> DetectionResult:
    files = [candidate for candidate in sorted(path.iterdir()) if candidate.is_file()]

    graphml_files = [candidate for candidate in files if candidate.suffix.lower() == ".graphml"]
    if len(graphml_files) == 1:
        return DetectionResult("graphml", graphml_files, node_file=graphml_files[0])

    json_node_link_files = [candidate for candidate in files if candidate.suffix.lower() == ".json"]
    for candidate in json_node_link_files:
        if _looks_like_node_link_json(candidate):
            return DetectionResult("networkx_node_link_json", [candidate], node_file=candidate)

    json_nodes = _find_named_file(files, ("nodes.json", "node.json"))
    json_edges = _find_named_file(files, ("edges.json", "edge.json", "links.json"))
    if json_nodes and json_edges:
        return DetectionResult("json_pair", [json_nodes, json_edges], node_file=json_nodes, edge_file=json_edges)

    jsonl_nodes = _find_named_file(files, ("nodes.jsonl", "node.jsonl"))
    jsonl_edges = _find_named_file(files, ("edges.jsonl", "edge.jsonl", "links.jsonl"))
    if jsonl_nodes and jsonl_edges:
        return DetectionResult(
            "jsonl_pair",
            [jsonl_nodes, jsonl_edges],
            node_file=jsonl_nodes,
            edge_file=jsonl_edges,
        )

    tabular_nodes = _find_named_file(files, ("nodes.csv", "nodes.tsv", "node.csv", "node.tsv"))
    tabular_edges = _find_named_file(files, ("edges.csv", "edges.tsv", "edge.csv", "edge.tsv"))
    if tabular_nodes and tabular_edges:
        return DetectionResult(
            "tabular_pair",
            [tabular_nodes, tabular_edges],
            node_file=tabular_nodes,
            edge_file=tabular_edges,
        )

    available = ", ".join(candidate.name for candidate in files) or "<empty directory>"
    raise DetectionError(
        f"Could not detect a supported graph format in {path}. Expected one of: "
        "node-link JSON, GraphML, paired JSON/JSONL node+edge files, or paired CSV/TSV "
        f"node+edge tables. Files found: {available}"
    )


def _find_named_file(files: list[Path], names: tuple[str, ...]) -> Path | None:
    for candidate in files:
        if candidate.name.lower() in names:
            return candidate
    return None


def _looks_like_node_link_json(path: Path) -> bool:
    try:
        payload = json.loads(path.read_text())
    except json.JSONDecodeError:
        return False
    if not isinstance(payload, dict):
        return False
    keys = set(payload)
    return "nodes" in keys and ("edges" in keys or "links" in keys)
