from __future__ import annotations

import random

from cvd_biopathnet.models import EdgeRecord


def make_splits(
    edges: list[EdgeRecord],
    *,
    seed: int,
    valid_ratio: float = 0.1,
    test_ratio: float = 0.1,
) -> tuple[list[EdgeRecord], list[EdgeRecord], list[EdgeRecord]]:
    if not edges:
        raise ValueError("No target edges were found for splitting.")

    shuffled = list(edges)
    rng = random.Random(seed)
    rng.shuffle(shuffled)

    total = len(shuffled)
    valid_count, test_count = _split_counts(total, valid_ratio, test_ratio)
    train_count = total - valid_count - test_count

    train = sorted(shuffled[:train_count], key=lambda edge: edge.triplet())
    valid = sorted(shuffled[train_count : train_count + valid_count], key=lambda edge: edge.triplet())
    test = sorted(shuffled[train_count + valid_count :], key=lambda edge: edge.triplet())
    return train, valid, test


def build_test_vis(test_edges: list[EdgeRecord], limit: int = 25) -> list[EdgeRecord]:
    return sorted(test_edges, key=lambda edge: edge.triplet())[:limit]


def _split_counts(total: int, valid_ratio: float, test_ratio: float) -> tuple[int, int]:
    if total < 3:
        return 0, 0

    valid_count = max(1, round(total * valid_ratio))
    test_count = max(1, round(total * test_ratio))
    while valid_count + test_count >= total:
        if valid_count >= test_count and valid_count > 1:
            valid_count -= 1
        elif test_count > 1:
            test_count -= 1
        else:
            break
    return valid_count, test_count
