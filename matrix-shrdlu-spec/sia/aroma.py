"""AROMA hierarchy matching through implication intensity (chapter 11 section 3)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .contingency import Contingency
from .hierarchy import Level
from .intensity import phi_classical, phi_entropic


@dataclass(frozen=True)
class Hierarchy:
    """One hierarchy as node terms and parent links."""

    terms: dict[str, frozenset[str]]
    parent: dict[str, str | None]


@dataclass(frozen=True)
class Match:
    """One significant rule between a node of each hierarchy."""

    a: str
    b: str
    phi: float
    n_a: int
    n_b: int
    n_anb: int


def hierarchy_from_levels(names: list[str], levels: list[Level]) -> Hierarchy:
    """Builds a hierarchy from the amalgamation levels of a class tree."""

    terms: dict[str, frozenset[str]] = {name: frozenset({name}) for name in names}
    for level in levels:
        node = "_".join(names[index] for index in level.cls)
        terms[node] = frozenset(names[index] for index in level.cls)
    parent: dict[str, str | None] = {}
    for node, node_terms in terms.items():
        containers = [other for other, other_terms in terms.items() if other != node and other_terms > node_terms]
        parent[node] = min(containers, key=lambda other: (len(terms[other]), other)) if containers else None
    return Hierarchy(terms=terms, parent=parent)


def ancestors(h: Hierarchy, node: str) -> list[str]:
    """Returns the node and its parents up to the root."""

    chain: list[str] = []
    current: str | None = node
    while current is not None and current not in chain:
        chain.append(current)
        current = h.parent.get(current)
    return chain


def descendants(h: Hierarchy, node: str) -> list[str]:
    """Returns the node and every node below it."""

    return [other for other in h.terms if node in ancestors(h, other)]


def aroma(
    h1: Hierarchy,
    h2: Hierarchy,
    phi_r: float = 0.85,
    alpha: float | None = None,
) -> list[Match]:
    """Returns the significant rules between two hierarchies, strongest first."""

    universe1 = set().union(*h1.terms.values()) if h1.terms else set()
    universe2 = set().union(*h2.terms.values()) if h2.terms else set()
    shared = universe1 & universe2
    n = len(shared)
    if n < 5:
        return []

    nodes1 = list(h1.terms)
    nodes2 = list(h2.terms)
    index1 = {node: position for position, node in enumerate(nodes1)}
    index2 = {node: position for position, node in enumerate(nodes2)}
    counts1 = np.array([len(h1.terms[node] & shared) for node in nodes1], dtype=np.float64)
    counts2 = np.array([len(h2.terms[node] & shared) for node in nodes2], dtype=np.float64)
    cooccurrence = np.array(
        [[len(h1.terms[a] & h2.terms[b] & shared) for b in nodes2] for a in nodes1],
        dtype=np.float64,
    )

    counts = _rectangular_contingency(n, counts1, counts2, cooccurrence)
    matrix = phi_entropic(counts, alpha) if alpha is not None else phi_classical(counts)
    phi = matrix[: len(nodes1), len(nodes1) :]

    matches: list[Match] = []
    for position_a, a in enumerate(nodes1):
        for position_b, b in enumerate(nodes2):
            value = float(phi[position_a, position_b])
            if value < phi_r:
                continue
            rows = [index1[node] for node in ancestors(h1, a)]
            columns = [index2[node] for node in descendants(h2, b)]
            if np.any(phi[np.ix_(rows, columns)] > value):
                continue
            matches.append(
                Match(
                    a=a,
                    b=b,
                    phi=value,
                    n_a=int(counts1[position_a]),
                    n_b=int(counts2[position_b]),
                    n_anb=int(counts1[position_a] - cooccurrence[position_a, position_b]),
                )
            )
    matches.sort(key=lambda match: match.phi, reverse=True)
    return matches


def _rectangular_contingency(
    n: int,
    counts1: np.ndarray,
    counts2: np.ndarray,
    cooccurrence: np.ndarray,
) -> Contingency:
    size1 = counts1.shape[0]
    size2 = counts2.shape[0]
    n_a = np.concatenate([counts1, counts2])
    n_ab = np.zeros((size1 + size2, size1 + size2), dtype=np.float64)
    n_ab[:size1, size1:] = cooccurrence
    n_anb = n_a[:, None] - n_ab
    n_nb = np.broadcast_to(n - n_a, n_ab.shape).copy()
    return Contingency(n=n, n_a=n_a, n_ab=n_ab, n_anb=n_anb, n_nb=n_nb)
