from __future__ import annotations

from pathlib import Path
import random

from cvd_biopathnet.io.load_graph import load_graph, summarize_raw_graph
from cvd_biopathnet.models import ConversionArtifacts, EdgeRecord, NormalizedGraph
from cvd_biopathnet.preprocess.external_brg import merge_pathway_commons_brg
from cvd_biopathnet.preprocess.export_biopathnet import export_dataset
from cvd_biopathnet.preprocess.normalize import (
    extract_task_edges,
    normalize_graph,
    normalize_relation,
    summarize_normalized_graph,
)
from cvd_biopathnet.preprocess.splits import build_test_vis, make_splits
from cvd_biopathnet.preprocess.validate import validate_dataset


def convert_to_biopathnet(
    *,
    input_path: Path,
    output_dir: Path,
    reports_dir: Path,
    target_relation: str,
    seed: int,
    mode: str,
    pilot_target_limit: int,
    pilot_background_limit: int | None,
    excluded_relations: list[str] | None = None,
    remove_self_loops: bool = False,
    external_brg_sif: Path | None = None,
    background_node_types: list[str] | None = None,
) -> ConversionArtifacts:
    raw_graph = load_graph(input_path)
    normalized_graph = normalize_graph(
        raw_graph,
        excluded_relations=excluded_relations,
        remove_self_loops=remove_self_loops,
    )
    normalized_summary = summarize_normalized_graph(normalized_graph)

    target_edges, background_edges, extraction_summary = extract_task_edges(
        normalized_graph,
        target_relation=target_relation,
    )
    background_filter_summary: dict[str, object] | None = None
    if background_node_types:
        background_edges, background_filter_summary = _filter_background_edges_by_node_types(
            graph=normalized_graph,
            background_edges=background_edges,
            allowed_node_types=background_node_types,
        )
    external_brg_summary: dict[str, int | str] | None = None
    if external_brg_sif is not None:
        background_edges, external_brg_summary = merge_pathway_commons_brg(
            graph=normalized_graph,
            background_edges=background_edges,
            sif_path=external_brg_sif,
        )
    if not target_edges:
        raise ValueError(
            f"No target edges found for relation {normalize_relation(target_relation)} with schema "
            "(Gene, relation, Condition)."
        )

    if mode == "pilot":
        target_edges, background_edges = _apply_pilot_mode(
            normalized_graph=normalized_graph,
            target_edges=target_edges,
            background_edges=background_edges,
            seed=seed,
            target_limit=pilot_target_limit,
            background_limit=pilot_background_limit,
        )

    train_edges, valid_edges, test_edges = make_splits(target_edges, seed=seed)
    test_vis_edges = build_test_vis(test_edges)

    graph_summary = {
        "raw": summarize_raw_graph(raw_graph, sample_limit=3),
        "normalized": normalized_summary,
        "task_extraction": extraction_summary,
        "mode": mode,
        "pilot_target_limit": pilot_target_limit if mode == "pilot" else None,
        "pilot_background_limit": pilot_background_limit if mode == "pilot" else None,
        "background_filter": background_filter_summary,
        "external_brg": external_brg_summary,
    }

    metadata = export_dataset(
        dataset_dir=output_dir,
        reports_dir=reports_dir,
        nodes=normalized_graph.nodes,
        background_edges=background_edges,
        train_edges=train_edges,
        valid_edges=valid_edges,
        test_edges=test_edges,
        test_vis_edges=test_vis_edges,
        source_files=normalized_graph.source_files,
        detected_format=normalized_graph.detected_format,
        target_relation=normalize_relation(target_relation),
        split_seed=seed,
        mode=mode,
        excluded_relations=[normalize_relation(relation) for relation in (excluded_relations or [])],
        graph_summary=graph_summary,
        extra_metadata={
            "duplicates_removed": normalized_graph.duplicates_removed,
            "skipped_edges": normalized_graph.skipped_edges,
            "background_filter": background_filter_summary,
            "external_brg": external_brg_summary,
        },
    )
    validation_report = validate_dataset(output_dir, write_report=True)
    return ConversionArtifacts(
        dataset_dir=str(output_dir),
        reports_dir=str(reports_dir),
        train1_count=len(background_edges),
        train2_count=len(train_edges),
        valid_count=len(valid_edges),
        test_count=len(test_edges),
        test_vis_count=len(test_vis_edges),
        validation_report=validation_report,
        metadata=metadata,
    )


def _apply_pilot_mode(
    *,
    normalized_graph: NormalizedGraph,
    target_edges: list[EdgeRecord],
    background_edges: list[EdgeRecord],
    seed: int,
    target_limit: int,
    background_limit: int | None,
) -> tuple[list[EdgeRecord], list[EdgeRecord]]:
    ranked_targets = list(sorted(target_edges, key=lambda edge: edge.triplet()))
    random.Random(seed).shuffle(ranked_targets)
    selected_targets = sorted(ranked_targets[:target_limit], key=lambda edge: edge.triplet())

    focus_entities = {entity for edge in selected_targets for entity in (edge.source, edge.target)}
    candidate_background = [
        edge
        for edge in background_edges
        if edge.source in focus_entities or edge.target in focus_entities
    ]
    if not candidate_background:
        candidate_background = list(background_edges)

    if background_limit is not None and len(candidate_background) > background_limit:
        shuffled_background = list(candidate_background)
        random.Random(seed + 1).shuffle(shuffled_background)
        candidate_background = sorted(
            shuffled_background[:background_limit],
            key=lambda edge: edge.triplet(),
        )
    else:
        candidate_background = sorted(candidate_background, key=lambda edge: edge.triplet())

    return selected_targets, candidate_background


def _filter_background_edges_by_node_types(
    *,
    graph: NormalizedGraph,
    background_edges: list[EdgeRecord],
    allowed_node_types: list[str],
) -> tuple[list[EdgeRecord], dict[str, object]]:
    allowed = {node_type.strip() for node_type in allowed_node_types if node_type.strip()}
    filtered_edges: list[EdgeRecord] = []
    removed_count = 0

    for edge in background_edges:
        source_type = graph.nodes[edge.source].label
        target_type = graph.nodes[edge.target].label
        if source_type in allowed and target_type in allowed:
            filtered_edges.append(edge)
        else:
            removed_count += 1

    summary: dict[str, object] = {
        "allowed_node_types": sorted(allowed),
        "kept_edge_count": len(filtered_edges),
        "removed_edge_count": removed_count,
    }
    return filtered_edges, summary
