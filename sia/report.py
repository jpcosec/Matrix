"""Serializable reports of rules and hierarchy levels."""

from __future__ import annotations

import numpy as np

from .cohesion import cohesion_pair
from .contingency import Contingency
from .hierarchy import Level
from .intensity import confidence, phi_classical, phi_entropic


def rules(
    names: list[str],
    c: Contingency,
    alpha: float = 2.0,
    threshold: float = 0.85,
) -> list[dict]:
    """Returns one record per ordered pair with entropic intensity above threshold."""

    phi = phi_classical(c)
    entropic = phi_entropic(c, alpha)
    conf = confidence(c)
    cohesion = cohesion_pair(entropic)
    size = len(names)
    records: list[dict] = []
    for a in range(size):
        for b in range(size):
            if a == b or entropic[a, b] < threshold:
                continue
            records.append(
                {
                    "a": names[a],
                    "b": names[b],
                    "n_a": int(c.n_a[a]),
                    "n_b": int(c.n_a[b]),
                    "n_anb": int(c.n_anb[a, b]),
                    "phi": float(phi[a, b]),
                    "phi_entropic": float(entropic[a, b]),
                    "confidence": float(conf[a, b]),
                    "cohesion": float(cohesion[a, b]),
                }
            )
    records.sort(key=lambda record: record["phi_entropic"], reverse=True)
    return records


def hierarchy_report(
    names: list[str],
    levels: list[Level],
    significant: list[int],
) -> list[dict]:
    """Returns one serializable record per hierarchy level."""

    flagged = set(significant)
    return [
        {
            "k": level.k,
            "cls": [names[index] for index in level.cls],
            "cohesion": float(level.cohesion),
            "height": float(level.height),
            "significant": level.k in flagged,
        }
        for level in levels
    ]
