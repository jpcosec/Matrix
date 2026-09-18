"""Tests for sia.similarity: Lerman index and undirected similarity tree."""

from __future__ import annotations

import numpy as np
import pytest

from sia.contingency import Contingency, contingency
from sia.hierarchy import significant_levels
from sia.similarity import build_similarity_tree, similarity_class, similarity_index
from tests.test_sia_hierarchy import B, C, D, E, build_figure_1_matrix


def from_counts(n: int, n_a: int, n_b: int, n_ab: int) -> Contingency:
    """Builds a two-variable Contingency from counted values."""

    n_a_vector = np.array([n_a, n_b], dtype=np.float64)
    n_ab_matrix = np.array([[n_a, n_ab], [n_ab, n_b]], dtype=np.float64)
    return Contingency(
        n=n,
        n_a=n_a_vector,
        n_ab=n_ab_matrix,
        n_anb=n_a_vector[:, None] - n_ab_matrix,
        n_nb=np.broadcast_to(n - n_a_vector, n_ab_matrix.shape).copy(),
    )


def test_similarity_index_is_symmetric_with_zero_diagonal():
    matrix = similarity_index(contingency(_small_matrix()))

    assert np.allclose(matrix, matrix.T)
    assert np.all(np.diag(matrix) == 0.0)


def test_similarity_index_is_one_for_always_together():
    matrix = similarity_index(from_counts(1000, 400, 400, 400))

    assert matrix[0, 1] == pytest.approx(1.0, abs=1e-6)


def test_similarity_index_is_one_half_for_independence():
    matrix = similarity_index(from_counts(1000, 500, 500, 250))

    assert matrix[0, 1] == pytest.approx(0.5, abs=1e-6)


def test_similarity_index_is_zero_for_never_together():
    matrix = similarity_index(from_counts(100, 50, 50, 0))

    assert matrix[0, 1] < 1e-4


def test_similarity_class_of_a_pair_is_its_similarity():
    spair = np.zeros((3, 3))
    spair[0, 2] = 0.7

    assert similarity_class((0, 2), spair) == pytest.approx(0.7)


def test_similarity_tree_recovers_the_two_figure_1_blocks():
    spair = similarity_index(contingency(build_figure_1_matrix()))
    levels = build_similarity_tree(spair)
    result = {frozenset(level.cls) for level in levels}

    assert frozenset({B, C}) in result
    assert frozenset({D, E}) in result


def test_similarity_tree_only_mixes_blocks_at_low_similarity():
    spair = similarity_index(contingency(build_figure_1_matrix()))
    levels = build_similarity_tree(spair)

    for level in levels:
        members = set(level.cls)
        if members & {B, C} and members & {D, E}:
            assert level.cohesion < 0.5


def test_similarity_tree_significant_levels_are_valid_indices():
    spair = similarity_index(contingency(build_figure_1_matrix()))
    levels = build_similarity_tree(spair)
    significant = significant_levels(levels, spair)

    assert all(0 <= index < len(levels) for index in significant)


def _small_matrix() -> np.ndarray:
    return np.array(
        [
            [1, 0, 1],
            [1, 1, 0],
            [0, 1, 1],
            [1, 1, 1],
            [0, 0, 1],
        ]
    )
