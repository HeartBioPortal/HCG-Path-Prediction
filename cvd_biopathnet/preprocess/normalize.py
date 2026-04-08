from __future__ import annotations

import hashlib
import re
from collections import Counter
from typing import Iterable

from cvd_biopathnet.models import EdgeRecord, NodeRecord, NormalizedGraph, RawGraph

TYPE_ALIASES = {
    "gene": "Gene",
    "condition": "Condition",
    "guideline": "Guideline",
    "section": "Section",
    "snippet": "Snippet",
    "recommendation": "Recommendation",
    "drug": "Drug",
    "evidenceclass": "EvidenceClass",
    "evidence_class": "EvidenceClass",
    "evidencelevel": "EvidenceLevel",
    "evidence_level": "EvidenceLevel",
    "biomarker": "Biomarker",
}


def normalize_graph(
    raw_graph: RawGraph,
    *,
    excluded_relations: Iterable[str] | None = None,
    remove_self_loops: bool = False,
) -> NormalizedGraph:
    excluded = {normalize_relation(relation) for relation in (excluded_relations or [])}
    nodes: dict[str, NodeRecord] = {}
    raw_to_entity: dict[str, str] = {}
    entity_to_raw: dict[str, str] = {}

    for raw_node in raw_graph.nodes:
        raw_id = clean_text(raw_node["id"])
        label = normalize_node_label(str(raw_node.get("label", "Entity")))
        name = clean_text(str(raw_node.get("name", raw_id)))
        entity_id = build_entity_id(raw_id, label, entity_to_raw)
        raw_to_entity[raw_id] = entity_id
        entity_to_raw[entity_id] = raw_id
        nodes[entity_id] = NodeRecord(
            raw_id=raw_id,
            entity_id=entity_id,
            label=label,
            name=name,
            attributes=_drop_keys(raw_node, {"id", "label", "name"}),
        )

    deduped_edges: dict[tuple[str, str, str], EdgeRecord] = {}
    duplicates_removed = 0
    skipped_edges = 0

    for raw_edge in raw_graph.edges:
        raw_source = clean_text(raw_edge["source"])
        raw_target = clean_text(raw_edge["target"])
        if raw_source not in raw_to_entity or raw_target not in raw_to_entity:
            raise ValueError(
                f"Edge references unknown node(s): source={raw_source!r}, target={raw_target!r}"
            )

        relation = normalize_relation(str(raw_edge["relation"]))
        if relation in excluded:
            skipped_edges += 1
            continue

        source = raw_to_entity[raw_source]
        target = raw_to_entity[raw_target]
        if remove_self_loops and source == target:
            skipped_edges += 1
            continue

        key = (source, relation, target)
        if key in deduped_edges:
            deduped_edges[key].duplicate_count += 1
            duplicates_removed += 1
            continue

        deduped_edges[key] = EdgeRecord(
            raw_source=raw_source,
            raw_target=raw_target,
            source=source,
            relation=relation,
            target=target,
            attributes=_drop_keys(raw_edge, {"source", "target", "relation"}),
        )

    return NormalizedGraph(
        nodes=nodes,
        edges=sorted(deduped_edges.values(), key=lambda edge: edge.triplet()),
        source_files=raw_graph.source_files,
        detected_format=raw_graph.detected_format,
        graph_metadata=raw_graph.graph_metadata,
        duplicates_removed=duplicates_removed,
        skipped_edges=skipped_edges,
    )


def extract_task_edges(
    graph: NormalizedGraph,
    *,
    target_relation: str,
    head_type: str = "Gene",
    tail_type: str = "Condition",
) -> tuple[list[EdgeRecord], list[EdgeRecord], dict[str, int]]:
    normalized_target_relation = normalize_relation(target_relation)
    target_edges: list[EdgeRecord] = []
    background_edges: list[EdgeRecord] = []
    mismatched_target_edges = 0

    for edge in graph.edges:
        source_type = graph.nodes[edge.source].label
        target_type = graph.nodes[edge.target].label
        if edge.relation == normalized_target_relation:
            if source_type == head_type and target_type == tail_type:
                target_edges.append(edge)
            else:
                mismatched_target_edges += 1
            continue
        background_edges.append(edge)

    return target_edges, background_edges, {
        "target_edge_count": len(target_edges),
        "background_edge_count": len(background_edges),
        "mismatched_target_edges": mismatched_target_edges,
    }


def summarize_normalized_graph(graph: NormalizedGraph) -> dict[str, dict[str, int] | int]:
    node_type_counts = Counter(node.label for node in graph.nodes.values())
    relation_counts = Counter(edge.relation for edge in graph.edges)
    return {
        "node_count": len(graph.nodes),
        "edge_count": len(graph.edges),
        "duplicates_removed": graph.duplicates_removed,
        "skipped_edges": graph.skipped_edges,
        "counts_by_type": dict(node_type_counts.most_common()),
        "counts_by_relation": dict(relation_counts.most_common()),
    }


def normalize_node_label(label: str) -> str:
    compact = re.sub(r"[^0-9A-Za-z]+", "", label).lower()
    if compact in TYPE_ALIASES:
        return TYPE_ALIASES[compact]
    cleaned = clean_text(label).replace(" ", "")
    return cleaned or "Entity"


def normalize_relation(relation: str) -> str:
    cleaned = clean_text(relation)
    cleaned = re.sub(r"[\s/\\-]+", "_", cleaned)
    cleaned = re.sub(r"[^0-9A-Za-z_]", "_", cleaned)
    cleaned = re.sub(r"_+", "_", cleaned)
    return cleaned.strip("_").upper()


def build_entity_id(raw_id: str, label: str, existing: dict[str, str]) -> str:
    suffix = raw_id.split(":", 1)[1] if ":" in raw_id else raw_id
    token = sanitize_identifier(suffix) or sanitize_identifier(label)
    candidate = f"{label.upper()}:{token}"
    if candidate not in existing or existing[candidate] == raw_id:
        return candidate
    digest = hashlib.sha1(raw_id.encode("utf-8")).hexdigest()[:8]
    return f"{candidate}_{digest}"


def sanitize_identifier(value: str) -> str:
    cleaned = clean_text(value)
    cleaned = re.sub(r"[\s/\\|]+", "_", cleaned)
    cleaned = re.sub(r"[^0-9A-Za-z_.-]", "_", cleaned)
    cleaned = re.sub(r"_+", "_", cleaned)
    return cleaned.strip("_")


def clean_text(value: str) -> str:
    return " ".join(str(value).replace("\t", " ").replace("\n", " ").split())


def _drop_keys(record: dict[str, object], keys: set[str]) -> dict[str, object]:
    return {key: value for key, value in record.items() if key not in keys}
