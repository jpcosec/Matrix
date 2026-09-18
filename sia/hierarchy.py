"""Agglomerative implicative hierarchy and Lerman significant levels."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .cohesion import cohesion_class


@dataclass(frozen=True)
class Level:
    """One amalgamation step of the hierarchy."""

    k: int
    cls: tuple[int, ...]
    cohesion: float
    height: float


def build_hierarchy(cpair: np.ndarray, max_size: int | None = None) -> list[Level]:
    """Builds the agglomerative hierarchy by maximum class cohesion."""

    size = int(cpair.shape[0])
    live: list[tuple[int, ...]] = [(index,) for index in range(size)]
    levels: list[Level] = []
    while len(live) > 1:
        best: tuple[int, ...] | None = None
        best_positions: tuple[int, int] | None = None
        best_cohesion = -1.0
        for first in range(len(live)):
            for second in range(len(live)):
                if first == second:
                    continue
                candidate = live[first] + live[second]
                if max_size is not None and len(candidate) > max_size:
                    continue
                value = cohesion_class(candidate, cpair)
                if value > best_cohesion or (value == best_cohesion and best is not None and candidate < best):
                    best = candidate
                    best_positions = (first, second)
                    best_cohesion = value
        if best is None or best_cohesion <= 0.0:
            break
        assert best_positions is not None
        insertion = min(best_positions)
        live = [cls for position, cls in enumerate(live) if position not in best_positions]
        live.insert(insertion, best)
        levels.append(Level(len(levels), best, best_cohesion, 1.0 - best_cohesion))
    return levels


def significant_levels(levels: list[Level], cpair: np.ndarray) -> list[int]:
    """Returns the indices of significant levels (strict local maxima of ``s``)."""

    scores = concordance_scores(levels, cpair)
    significant: list[int] = []
    for k, score in enumerate(scores):
        left = k == 0 or scores[k - 1] < score
        right = k == len(scores) - 1 or score > scores[k + 1]
        if left and right:
            significant.append(k)
    return significant


def concordance_scores(levels: list[Level], cpair: np.ndarray) -> np.ndarray:
    """Vectorized Lerman concordance scores, one per level.

    For each level the concordance counts ordered pairs ``(p in A_k, q in S_k)``
    with ``c(p) >= c(q)``; ``S_k`` is sorted once per level and every ``A_k``
    value is located with ``np.searchsorted``.
    """

    size = int(cpair.shape[0])
    if size == 0 or not levels:
        return np.zeros(len(levels))
    row, column = np.meshgrid(np.arange(size), np.arange(size), indexing="ij")
    off_diagonal = row != column
    row, column = row[off_diagonal], column[off_diagonal]
    values = np.asarray(cpair, dtype=np.float64)[row, column]
    order = np.argsort(values, kind="stable")
    sorted_values = values[order]
    rank = np.empty(order.shape[0], dtype=np.int64)
    rank[order] = np.arange(order.shape[0])
    pair_position = np.full((size, size), -1, dtype=np.int64)
    pair_position[row, column] = np.arange(values.shape[0])
    merged_sorted = np.zeros(values.shape[0], dtype=bool)
    scores = np.zeros(len(levels))
    for k, level in enumerate(levels):
        positions = pair_position[np.ix_(level.cls, level.cls)].ravel()
        positions = positions[positions >= 0]
        if positions.size:
            merged_sorted[rank[positions]] = True
        merged_values = sorted_values[merged_sorted]
        separated_values = sorted_values[~merged_sorted]
        if merged_values.size == 0 or separated_values.size == 0:
            scores[k] = 0.0
            continue
        concordances = int(np.searchsorted(separated_values, merged_values, side="right").sum())
        m = merged_values.size * separated_values.size
        sigma = float(np.sqrt(m * (values.shape[0] + 1) / 12.0))
        scores[k] = 0.0 if sigma == 0.0 else (concordances - m / 2.0) / sigma
    return scores


def _significant_levels_naive(levels: list[Level], cpair: np.ndarray) -> list[int]:
    """Reference O(|A|*|S|) implementation used by the tests."""

    size = int(cpair.shape[0])
    pairs = [(x, y) for x in range(size) for y in range(size) if x != y]
    scores: list[float] = []
    for k in range(len(levels)):
        merged = {pair for level in levels[: k + 1] for pair in _inner_pairs(level.cls)}
        separated = [pair for pair in pairs if pair not in merged]
        concordances = sum(
            1
            for inside in merged
            for outside in separated
            if cpair[inside[0], inside[1]] >= cpair[outside[0], outside[1]]
        )
        m = len(merged) * len(separated)
        sigma = float(np.sqrt(m * (len(pairs) + 1) / 12.0))
        scores.append(0.0 if sigma == 0.0 else (concordances - m / 2.0) / sigma)
    significant: list[int] = []
    for k, score in enumerate(scores):
        left = k == 0 or scores[k - 1] < score
        right = k == len(scores) - 1 or score > scores[k + 1]
        if left and right:
            significant.append(k)
    return significant


def _inner_pairs(cls: tuple[int, ...]) -> set[tuple[int, int]]:
    return {(x, y) for x in cls for y in cls if x != y}


def classes(levels: list[Level]) -> list[tuple[int, ...]]:
    """Returns the class of every amalgamation level, in construction order."""

    return [level.cls for level in levels]
