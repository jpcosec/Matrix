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


@dataclass(frozen=True)
class PairContingency:
    """Counts for a list of ordered pairs, all arrays 1-D and aligned by pair."""

    n: int
    n_a: np.ndarray
    n_b: np.ndarray
    n_ab: np.ndarray
    n_anb: np.ndarray
    n_nb: np.ndarray


def contingency_pairs(
    matrix: np.ndarray | sparse.csr_matrix,
    rows: np.ndarray,
    cols: np.ndarray,
    block: int = 200_000,
) -> PairContingency:
    """Counts the given ordered pairs of the matrix's columns, block by block."""

    rows = np.asarray(rows, dtype=np.int64)
    cols = np.asarray(cols, dtype=np.int64)
    size = int(rows.shape[0])
    n = int(matrix.shape[0])
    n_a_all = np.asarray(matrix.sum(axis=0)).ravel().astype(np.float64)
    n_ab = np.empty(size, dtype=np.float64)
    for start in range(0, size, block):
        stop = min(start + block, size)
        left = matrix[:, rows[start:stop]]
        right = matrix[:, cols[start:stop]]
        if sparse.issparse(left):
            values = left.multiply(right).sum(axis=0)
            n_ab[start:stop] = np.asarray(values).ravel()
        else:
            values = np.asarray(left, dtype=np.float64) * np.asarray(right, dtype=np.float64)
            n_ab[start:stop] = values.sum(axis=0)
    n_a = n_a_all[rows]
    n_b = n_a_all[cols]
    return PairContingency(
        n=n,
        n_a=n_a,
        n_b=n_b,
        n_ab=n_ab,
        n_anb=n_a - n_ab,
        n_nb=n - n_b,
    )
