"""Tests for sia.intensity against Table 1 (book p. 22)."""

from __future__ import annotations

import numpy as np
import pytest
from scipy import stats

from sia.contingency import Contingency, contingency
from sia.intensity import (
    conditional_entropies,
    confidence,
    inclusion_index,
    phi_classical,
    phi_entropic,
)


def from_counts(n: int, n_a: int, n_b: int, n_ab: int) -> Contingency:
    """Builds a two-variable Contingency directly from counted values."""

    n_a_vector = np.array([n_a, n_b], dtype=np.float64)
    n_ab_matrix = np.array([[n_a, n_ab], [n_ab, n_b]], dtype=np.float64)
    n_anb = n_a_vector[:, None] - n_ab_matrix
    n_nb = np.broadcast_to(n - n_a_vector, n_ab_matrix.shape).copy()
    return Contingency(n=n, n_a=n_a_vector, n_ab=n_ab_matrix, n_anb=n_anb, n_nb=n_nb)


def test_table_1a_non_admissible_rule():
    c = from_counts(4000, 600, 800, 200)

    assert phi_classical(c)[0, 1] == pytest.approx(0.9999, abs=1e-3)
    assert inclusion_index(c)[0, 1] == 0.0
    assert phi_entropic(c)[0, 1] == 0.0
    assert confidence(c)[0, 1] == pytest.approx(0.3333, abs=1e-4)


def test_table_1b_admissible_rule():
    c = from_counts(4000, 600, 1400, 400)
    h_given_a, h_given_nb = conditional_entropies(c)

    assert phi_classical(c)[0, 1] > 0.99999
    assert h_given_a[0, 1] == pytest.approx(0.918, abs=2e-3)
    assert h_given_nb[0, 1] == pytest.approx(0.391, abs=2e-3)
    assert inclusion_index(c)[0, 1] == pytest.approx(0.6035, abs=2e-3)
    assert phi_entropic(c)[0, 1] == pytest.approx(0.777, abs=2e-3)
    assert confidence(c)[0, 1] == pytest.approx(0.6667, abs=1e-4)


def test_table_1c_smaller_sample_is_less_intense():
    c_b = from_counts(4000, 600, 1400, 400)
    c_c = from_counts(400, 60, 100, 40)

    assert phi_classical(c_c)[0, 1] < phi_classical(c_b)[0, 1]


def test_phi_is_zero_when_second_variable_is_universal():
    c = from_counts(1000, 500, 1000, 500)

    assert phi_classical(c)[0, 1] == 0.0


def test_phi_uses_poisson_exact_for_small_lambda():
    c = from_counts(100, 4, 10, 3)
    lam = 4 * 90 / 100

    assert lam <= 4.0
    assert phi_classical(c)[0, 1] == pytest.approx(1.0 - stats.poisson.cdf(1, lam), abs=1e-12)


def test_contingency_matches_manual_counts():
    x = np.array(
        [
            [1, 0, 1],
            [1, 1, 0],
            [0, 1, 1],
            [1, 1, 1],
            [0, 0, 1],
        ]
    )
    c = contingency(x)
    manual = x.T @ x

    assert c.n == 5
    assert list(c.n_a) == [3.0, 3.0, 4.0]
    for a in range(3):
        for b in range(3):
            assert c.n_ab[a, b] == manual[a, b]
            assert c.n_anb[a, b] == c.n_a[a] - manual[a, b]
            assert c.n_nb[a, b] == c.n - c.n_a[b]
