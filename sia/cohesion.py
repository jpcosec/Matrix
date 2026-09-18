"""Cohesion of pairs and R-rules (Gras & Kuntz, SCI 127, Def. 7-8)."""

from __future__ import annotations

import numpy as np


def cohesion_pair(phi: np.ndarray) -> np.ndarray:
    """Returns the cohesion ``c = sqrt(1 - H(phi)^2)`` for every pair."""

    p = np.clip(np.asarray(phi, dtype=np.float64), 0.0, 1.0)
    with np.errstate(divide="ignore", invalid="ignore"):
        h = -p * np.log2(p) - (1.0 - p) * np.log2(1.0 - p)
    h = np.where((p == 0.0) | (p == 1.0), 0.0, h)
    cohesion = np.sqrt(np.clip(1.0 - h**2, 0.0, None))
    return np.where(p <= 0.5, 0.0, cohesion)


def cohesion_class(cls: tuple[int, ...], cpair: np.ndarray) -> float:
    """Returns the geometric mean cohesion of all ordered pairs inside a class."""

    r = len(cls)
    if r == 1:
        return 1.0
    product = 1.0
    for i in range(r):
        for j in range(i + 1, r):
            product *= float(cpair[cls[i], cls[j]])
    if product <= 0.0:
        return 0.0
    return float(product ** (2.0 / (r * (r - 1))))
