from __future__ import annotations

import gzip
from pathlib import Path

from cvd_biopathnet.models import EdgeRecord, NormalizedGraph
from cvd_biopathnet.preprocess.normalize import normalize_relation, sanitize_identifier


def merge_pathway_commons_brg(
    *,
    graph: NormalizedGraph,
    background_edges: list[EdgeRecord],
    sif_path: Path,
) -> tuple[list[EdgeRecord], dict[str, int | str]]:
    sif_path = sif_path.expanduser().resolve()
    if not sif_path.exists():
        raise FileNotFoundError(f"External BRG file not found: {sif_path}")

    gene_symbol_to_entity = _build_gene_symbol_index(graph)
    deduped: dict[tuple[str, str, str], EdgeRecord] = {
        edge.triplet(): edge for edge in background_edges
    }

    stats = {
        "path": str(sif_path),
        "added_edge_count": 0,
        "duplicate_edge_count": 0,
        "skipped_unmapped_count": 0,
        "skipped_non_gene_count": 0,
        "total_line_count": 0,
        "retained_line_count": 0,
    }

    with _open_text(sif_path) as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            stats["total_line_count"] += 1
            tokens = line.split("\t")
            if len(tokens) != 3:
                continue

            source_symbol, relation, target_symbol = tokens
            if not (_looks_like_gene_symbol(source_symbol) and _looks_like_gene_symbol(target_symbol)):
                stats["skipped_non_gene_count"] += 1
                continue

            source_entity = gene_symbol_to_entity.get(source_symbol.upper())
            target_entity = gene_symbol_to_entity.get(target_symbol.upper())
            if source_entity is None or target_entity is None:
                stats["skipped_unmapped_count"] += 1
                continue

            normalized = normalize_relation(relation)
            key = (source_entity, normalized, target_entity)
            if key in deduped:
                stats["duplicate_edge_count"] += 1
                continue

            deduped[key] = EdgeRecord(
                raw_source=source_symbol,
                raw_target=target_symbol,
                source=source_entity,
                relation=normalized,
                target=target_entity,
                attributes={"source_dataset": "PathwayCommons_PC2_v14"},
            )
            stats["added_edge_count"] += 1
            stats["retained_line_count"] += 1

    merged_edges = sorted(deduped.values(), key=lambda edge: edge.triplet())
    return merged_edges, stats


def _build_gene_symbol_index(graph: NormalizedGraph) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for entity_id, node in graph.nodes.items():
        if node.label != "Gene":
            continue
        candidates = {
            node.name.upper(),
            node.raw_id.upper(),
            entity_id.split(":", 1)[1].upper() if ":" in entity_id else entity_id.upper(),
            sanitize_identifier(node.name).upper(),
            sanitize_identifier(node.raw_id).upper(),
        }
        for candidate in candidates:
            if candidate:
                mapping.setdefault(candidate, entity_id)
    return mapping


def _looks_like_gene_symbol(value: str) -> bool:
    value = value.strip()
    if not value or ":" in value:
        return False
    return sanitize_identifier(value).upper() == value.upper()


def _open_text(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt")
    return path.open("r")
