"""Tests for sia.hierarchy against Fig. 1 (book p. 26)."""

from __future__ import annotations

import numpy as np

from sia.cohesion import cohesion_pair
from sia.contingency import contingency
from sia.hierarchy import build_hierarchy, classes, significant_levels
from sia.intensity import phi_entropic

# Variables in book order: a=0, b=1, c=2, d=3, e=4.
A, B, C, D, E = 0, 1, 2, 3, 4


def build_figure_1_matrix() -> np.ndarray:
    """Builds a deterministic 300x5 matrix with the Fig. 1 block structure."""

    x = np.zeros((300, 5), dtype=int)
    x[0:60, B] = 1
    x[0:100, C] = 1
    x[200:249, E] = 1
    x[200:289, D] = 1
    x[195:220, A] = 1
    return x


def test_hierarchy_reproduces_figure_1_classes():
    cpair = cohesion_pair(phi_entropic(contingency(build_figure_1_matrix())))
    levels = build_hierarchy(cpair)
    result = {frozenset(cls) for cls in classes(levels)}

    assert result == {
        frozenset({B, C}),
        frozenset({D, E}),
        frozenset({A, D, E}),
    }


def test_hierarchy_never_merges_the_two_independent_blocks():
    cpair = cohesion_pair(phi_entropic(contingency(build_figure_1_matrix())))
    levels = build_hierarchy(cpair)

    assert not any({B, E} <= set(cls) for cls in classes(levels))


def test_height_grows_when_a_joins_the_de_class():
    cpair = cohesion_pair(phi_entropic(contingency(build_figure_1_matrix())))
    levels = build_hierarchy(cpair)
    heights = {frozenset(level.cls): level.height for level in levels}

    assert heights[frozenset({A, D, E})] > heights[frozenset({D, E})]


def test_significant_levels_returns_valid_indices():
    cpair = cohesion_pair(phi_entropic(contingency(build_figure_1_matrix())))
    levels = build_hierarchy(cpair)
    significant = significant_levels(levels, cpair)

    assert significant
    assert all(0 <= index < len(levels) for index in significant)


def _synthetic_levels(size: int, count: int):
    from sia.hierarchy import Level

    live = [(index,) for index in range(size)]
    levels = []
    while len(live) > 1 and len(levels) < count:
        first = live.pop(0)
        second = live.pop(0)
        merged = first + second
        live.insert(0, merged)
        levels.append(Level(len(levels), merged, 0.9, 0.1))
    return levels


def test_significant_levels_matches_the_naive_implementation():
    from sia.hierarchy import _significant_levels_naive

    rng = np.random.default_rng(3)
    cpair = cohesion_pair(rng.random((12, 12)))
    levels = build_hierarchy(cpair)

    assert significant_levels(levels, cpair) == _significant_levels_naive(levels, cpair)


def test_significant_levels_is_fast_on_large_hierarchies():
    from time import perf_counter

    cpair = np.random.default_rng(4).random((300, 300))
    levels = _synthetic_levels(300, 150)

    start = perf_counter()
    significant_levels(levels, cpair)
    elapsed = perf_counter() - start

    assert elapsed < 2.0


def test_significant_levels_handles_eight_hundred_variables():
    from time import perf_counter

    cpair = np.random.default_rng(5).random((800, 800))
    levels = _synthetic_levels(800, 200)

    start = perf_counter()
    significant_levels(levels, cpair)
    elapsed = perf_counter() - start

    assert elapsed < 5.0
