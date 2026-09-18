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
