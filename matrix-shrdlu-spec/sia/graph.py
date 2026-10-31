"""Thresholded implicative graphs and boolean closures."""

from __future__ import annotations

import numpy as np

DEFAULT_THRESHOLDS = (0.99, 0.95, 0.90, 0.85)


def implicative_graph(
    phi: np.ndarray, thresholds: tuple[float, ...] = DEFAULT_THRESHOLDS
) -> dict[float, np.ndarray]:
    """Returns one boolean arc matrix per threshold, diagonal excluded."""

    graph: dict[float, np.ndarray] = {}
    for threshold in thresholds:
        arcs = np.asarray(phi) >= threshold
        np.fill_diagonal(arcs, False)
        graph[float(threshold)] = arcs
    return graph


def transitive_closure(adj: np.ndarray) -> np.ndarray:
    """Returns the transitive closure by boolean squaring to a fixed point."""

    closure = np.asarray(adj, dtype=bool).copy()
    while True:
        squared = closure @ closure
        updated = closure | squared
        if np.array_equal(updated, closure):
            return closure
        closure = updated


def transitive_reduction(adj: np.ndarray) -> np.ndarray:
    """Removes arcs implied by a two-step path through an intermediate node."""

    matrix = np.asarray(adj, dtype=bool)
    two_step = matrix @ matrix
    return matrix & ~two_step
