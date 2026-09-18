"""Lerman similarity index and undirected agglomerative similarity tree."""

from __future__ import annotations

import numpy as np
from scipy import stats

from .contingency import Contingency
from .hierarchy import Level


def similarity_index(c: Contingency, exact_below: float = 4.0) -> np.ndarray:
    """Returns the symmetric similarity index of every pair."""

    lam = c.n_a[:, None] * c.n_a[None, :] / c.n
    with np.errstate(divide="ignore", invalid="ignore"):
        normal = stats.norm.cdf((c.n_ab - lam) / np.sqrt(lam))
    exact = stats.poisson.cdf(c.n_ab - 1, lam)
    similarity = np.where(lam > exact_below, normal, exact)
    similarity = np.where((c.n_a[:, None] == 0.0) | (c.n_a[None, :] == 0.0), 0.0, similarity)
    similarity = np.maximum(similarity, similarity.T)
    np.fill_diagonal(similarity, 0.0)
    return similarity


def similarity_class(cls: tuple[int, ...], spair: np.ndarray) -> float:
    """Returns the geometric mean similarity of all unordered pairs in a class."""

    r = len(cls)
    if r == 1:
        return 1.0
    product = 1.0
    for i in range(r):
        for j in range(i + 1, r):
            product *= float(spair[cls[i], cls[j]])
    if product <= 0.0:
        return 0.0
    return float(product ** (2.0 / (r * (r - 1))))


def build_similarity_tree(spair: np.ndarray, max_size: int | None = None) -> list[Level]:
    """Builds the undirected agglomerative tree by maximum class similarity."""

    size = int(spair.shape[0])
    live: list[tuple[int, ...]] = [(index,) for index in range(size)]
    levels: list[Level] = []
    while len(live) > 1:
        best: tuple[int, ...] | None = None
        best_positions: tuple[int, int] | None = None
        best_similarity = -1.0
        for first in range(len(live)):
            for second in range(first + 1, len(live)):
                candidate = tuple(sorted(live[first] + live[second]))
                if max_size is not None and len(candidate) > max_size:
                    continue
                value = similarity_class(candidate, spair)
                if value > best_similarity or (value == best_similarity and best is not None and candidate < best):
                    best = candidate
                    best_positions = (first, second)
                    best_similarity = value
        if best is None or best_similarity <= 0.0:
            break
        assert best_positions is not None
        insertion = min(best_positions)
        live = [cls for position, cls in enumerate(live) if position not in best_positions]
        live.insert(insertion, best)
        levels.append(Level(len(levels), best, best_similarity, 1.0 - best_similarity))
    return levels
