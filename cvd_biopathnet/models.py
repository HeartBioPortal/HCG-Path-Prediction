from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


JsonDict = dict[str, Any]


@dataclass(slots=True)
class NodeRecord:
    raw_id: str
    entity_id: str
    label: str
    name: str
    attributes: JsonDict = field(default_factory=dict)


@dataclass(slots=True)
class EdgeRecord:
    raw_source: str
    raw_target: str
    source: str
    relation: str
    target: str
    attributes: JsonDict = field(default_factory=dict)
    duplicate_count: int = 1

    def triplet(self) -> tuple[str, str, str]:
        return (self.source, self.relation, self.target)


@dataclass(slots=True)
class RawGraph:
    nodes: list[JsonDict]
    edges: list[JsonDict]
    source_files: list[str]
    detected_format: str
    graph_metadata: JsonDict = field(default_factory=dict)


@dataclass(slots=True)
class NormalizedGraph:
    nodes: dict[str, NodeRecord]
    edges: list[EdgeRecord]
    source_files: list[str]
    detected_format: str
    graph_metadata: JsonDict = field(default_factory=dict)
    duplicates_removed: int = 0
    skipped_edges: int = 0


@dataclass(slots=True)
class ConversionArtifacts:
    dataset_dir: str
    reports_dir: str
    train1_count: int
    train2_count: int
    valid_count: int
    test_count: int
    test_vis_count: int
    validation_report: JsonDict
    metadata: JsonDict
