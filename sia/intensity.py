"""Implication intensity indices (classical, entropic and inclusion)."""

from __future__ import annotations

import numpy as np
from scipy import stats

from .contingency import Contingency


def _safe_ratio(numerator: np.ndarray, denominator: np.ndarray) -> np.ndarray:
    return np.where(denominator == 0.0, 0.0, numerator / np.where(denominator == 0.0, 1.0, denominator))


def _binary_entropy(p: np.ndarray) -> np.ndarray:
    p = np.clip(p, 0.0, 1.0)
    with np.errstate(divide="ignore", invalid="ignore"):
        h = -p * np.log2(p) - (1.0 - p) * np.log2(1.0 - p)
    return np.where((p == 0.0) | (p == 1.0), 0.0, h)


def _poisson_lambda(c: Contingency) -> np.ndarray:
    return c.n_a[:, None] * c.n_nb / c.n


def q_index(c: Contingency) -> np.ndarray:
    """Returns the standardized deviation index ``q(a, not b)``."""

    lam = _poisson_lambda(c)
    with np.errstate(divide="ignore", invalid="ignore"):
        q = (c.n_anb - lam) / np.sqrt(lam)
    return np.where(lam == 0.0, 0.0, q)


def phi_classical(c: Contingency, exact_below: float = 4.0) -> np.ndarray:
    """Returns the classical implication intensity ``phi``."""

    lam = _poisson_lambda(c)
    phi = np.where(lam > exact_below, stats.norm.sf(q_index(c)), 1.0 - stats.poisson.cdf(c.n_anb, lam))
    n_b = c.n - c.n_nb[0, :]
    phi = np.where(n_b[None, :] == c.n, 0.0, phi)
    phi = np.where(c.n_a[:, None] == 0.0, 0.0, phi)
    np.fill_diagonal(phi, 0.0)
    return phi


def conditional_entropies(c: Contingency) -> tuple[np.ndarray, np.ndarray]:
    """Returns ``H`` of ``a`` given ``b`` and of ``a`` given ``not b``."""

    h_given_a = _binary_entropy(_safe_ratio(c.n_ab, c.n_a[:, None]))
    n_na_nb = c.n_nb - c.n_anb
    h_given_nb = _binary_entropy(_safe_ratio(n_na_nb, c.n_nb))
    return h_given_a, h_given_nb


def inclusion_index(c: Contingency, alpha: float = 2.0) -> np.ndarray:
    """Returns the inclusion index ``tau`` for every ordered pair."""

    h_given_a, h_given_nb = conditional_entropies(c)
    f_a = c.n_a[:, None] / c.n
    f_nb = c.n_nb / c.n
    f_anb = c.n_anb / c.n
    i_a = np.where(f_anb < f_a / 2.0, 1.0 - h_given_a**alpha, 0.0)
    i_nb = np.where(f_anb < f_nb / 2.0, 1.0 - h_given_nb**alpha, 0.0)
    product = i_a * i_nb
    return np.where(product > 0.0, product ** (1.0 / (2.0 * alpha)), 0.0)


def phi_entropic(c: Contingency, alpha: float = 2.0, exact_below: float = 4.0) -> np.ndarray:
    """Returns the entropic implication intensity ``phi``."""

    return np.sqrt(phi_classical(c, exact_below) * inclusion_index(c, alpha))


def confidence(c: Contingency) -> np.ndarray:
    """Returns the conditional frequency ``n_ab / n_a``."""

    return _safe_ratio(c.n_ab, c.n_a[:, None])


def admissible(phi: np.ndarray, alpha_adm: float = 0.05) -> np.ndarray:
    """Returns the significance mask ``phi >= 1 - alpha_adm``."""

    return phi >= 1.0 - alpha_adm
