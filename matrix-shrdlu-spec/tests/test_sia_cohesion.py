"""Tests for sia.cohesion (Def. 7-8, book p. 25)."""

from __future__ import annotations

import numpy as np
import pytest

from sia.cohesion import cohesion_class, cohesion_pair


def test_cohesion_pair_is_zero_up_to_one_half():
    phi = np.array([0.0, 0.3, 0.5])

    assert list(cohesion_pair(phi)) == [0.0, 0.0, 0.0]


def test_cohesion_pair_is_one_for_certain_implication():
    assert cohesion_pair(np.array([1.0]))[0] == pytest.approx(1.0)


def test_cohesion_pair_is_monotone_above_one_half():
    phi = np.array([0.6, 0.7, 0.8, 0.9, 1.0])
    cohesion = cohesion_pair(phi)

    assert all(np.diff(cohesion) > 0.0)


def test_cohesion_class_singleton_is_one():
    cpair = np.zeros((3, 3))

    assert cohesion_class((0,), cpair) == 1.0


def test_cohesion_class_pair_is_the_pair_cohesion():
    cpair = np.zeros((3, 3))
    cpair[0, 1] = 0.42

    assert cohesion_class((0, 1), cpair) == pytest.approx(0.42)


def test_cohesion_class_is_geometric_mean_of_ordered_pairs():
    cpair = np.zeros((4, 4))
    values = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4]
    cpair[0, 1], cpair[0, 2], cpair[0, 3] = values[0], values[1], values[2]
    cpair[1, 2], cpair[1, 3], cpair[2, 3] = values[3], values[4], values[5]
    expected = float(np.prod(values) ** (2 / (4 * 3)))

    assert cohesion_class((0, 1, 2, 3), cpair) == pytest.approx(expected)


def test_cohesion_class_is_zero_when_any_pair_is_zero():
    cpair = np.ones((3, 3))
    cpair[1, 2] = 0.0

    assert cohesion_class((0, 1, 2), cpair) == 0.0
