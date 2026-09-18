"""Contingency counts for all variable pairs of a binary matrix."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import sparse


@dataclass(frozen=True)
class Contingency:
    """Pairwise counts for an ``n x p`` binary matrix.

    All matrices are ``p x p`` float64 except ``n``.
    """

    n: int
    n_a: np.ndarray
    n_ab: np.ndarray
    n_anb: np.ndarray
    n_nb: np.ndarray


def contingency(X: np.ndarray | sparse.csr_matrix) -> Contingency:
    """Computes ``n_a``, ``n_ab``, ``n_anb`` and ``n_nb`` for every pair."""

    n = int(X.shape[0])
    n_a = np.asarray(X.sum(axis=0)).ravel().astype(np.float64)
    if sparse.issparse(X):
        n_ab = np.asarray((X.T @ X).todense(), dtype=np.float64)
    else:
        matrix = np.asarray(X, dtype=np.float64)
        n_ab = matrix.T @ matrix
    n_anb = n_a[:, None] - n_ab
    n_nb = np.broadcast_to(n - n_a, n_ab.shape).copy()
    return Contingency(n=n, n_a=n_a, n_ab=n_ab, n_anb=n_anb, n_nb=n_nb)
