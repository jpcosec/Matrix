"""Tests for sia.aroma: hierarchy matching by implication intensity."""

from __future__ import annotations

import numpy as np

from sia.aroma import Hierarchy, ancestors, aroma, descendants, hierarchy_from_levels
from sia.contingency import Contingency
from sia.hierarchy import Level
from sia.intensity import phi_classical


def _block(prefix: str, start: int, stop: int) -> list[str]:
    return [f"{prefix}{index}" for index in range(start, stop)]


def _hierarchy(terms: dict[str, list[str]], parent: dict[str, str | None]) -> Hierarchy:
    return Hierarchy(
        terms={node: frozenset(values) for node, values in terms.items()},
        parent=parent,
    )


def _leaf_and_root_hierarchies() -> tuple[Hierarchy, Hierarchy]:
    """Builds the two synthetic hierarchies over a 40-term vocabulary."""

    leaf = _block("hoja", 1, 17)
    root = _block("raiz", 1, 13)
    terrain = _block("tierra", 1, 13)
    green_leaf = _block("hoja", 1, 9)
    root_tip = _block("raiz", 1, 7)
    vegetable = green_leaf + root_tip
    food = vegetable + _block("hoja", 9, 13) + _block("tierra", 1, 7)

    h1 = _hierarchy(
        {
            "hoja_verde": green_leaf,
            "raiz": root_tip,
            "verdura": vegetable,
            "alimento": food,
        },
        {"hoja_verde": "verdura", "raiz": "verdura", "verdura": "alimento", "alimento": None},
    )
    # `terreno` keeps `vegetal` from covering the whole shared vocabulary, which
    # would force phi = 0 by the "n_b = n" convention.
    h2 = _hierarchy(
        {
            "leaf": leaf,
            "root": root,
            "vegetal": leaf + root,
            "terreno": leaf + root + terrain,
        },
        {"leaf": "vegetal", "root": "vegetal", "vegetal": "terreno", "terreno": None},
    )
    return h1, h2


def _phi_between(h1: Hierarchy, h2: Hierarchy, a: str, b: str) -> float:
    """Recomputes the classical intensity of one rule outside AROMA."""

    shared = set().union(*h1.terms.values()) & set().union(*h2.terms.values())
    n = len(shared)
    n_a = len(h1.terms[a] & shared)
    n_b = len(h2.terms[b] & shared)
    n_ab = len(h1.terms[a] & h2.terms[b] & shared)
    n_a_vector = np.array([n_a, n_b], dtype=np.float64)
    n_ab_matrix = np.array([[n_a, n_ab], [n_ab, n_b]], dtype=np.float64)
    counts = Contingency(
        n=n,
        n_a=n_a_vector,
        n_ab=n_ab_matrix,
        n_anb=n_a_vector[:, None] - n_ab_matrix,
        n_nb=np.broadcast_to(n - n_a_vector, n_ab_matrix.shape).copy(),
    )
    return float(phi_classical(counts)[0, 1])


def test_hierarchy_from_levels_builds_terms_and_parents():
    levels = [Level(0, (0, 1), 0.9, 0.1), Level(1, (0, 1, 2), 0.8, 0.2)]
    hierarchy = hierarchy_from_levels(["a", "b", "c"], levels)

    assert hierarchy.terms["a_b"] == frozenset({"a", "b"})
    assert hierarchy.terms["a_b_c"] == frozenset({"a", "b", "c"})
    assert hierarchy.parent["a"] == "a_b"
    assert hierarchy.parent["c"] == "a_b_c"
    assert hierarchy.parent["a_b_c"] is None
    assert set(ancestors(hierarchy, "a")) == {"a", "a_b", "a_b_c"}
    assert set(descendants(hierarchy, "a_b_c")) == {"a_b_c", "a_b", "a", "b", "c"}


def test_aroma_matches_leaf_and_root_blocks():
    h1, h2 = _leaf_and_root_hierarchies()
    matches = {(match.a, match.b) for match in aroma(h1, h2)}

    assert ("hoja_verde", "leaf") in matches
    assert ("raiz", "root") in matches


def test_aroma_matches_the_vegetable_block_through_the_shared_terms():
    h1, h2 = _leaf_and_root_hierarchies()
    matches = aroma(h1, h2)

    assert [(match.a, match.b) for match in matches] == [
        ("raiz", "root"),
        ("hoja_verde", "leaf"),
        ("verdura", "vegetal"),
    ]
    assert matches[0].phi >= matches[1].phi >= matches[2].phi
    assert matches[2].n_a == 14
    assert matches[2].n_b == 18
    assert matches[2].n_anb == 0


def test_aroma_maximality_rejects_a_dominated_rule():
    fine_leaf = _block("hoja", 1, 17)
    leaf = fine_leaf + _block("hoja", 17, 25)
    root = _block("hoja", 13, 17) + _block("raiz", 1, 9)
    vegetable = fine_leaf
    green_leaf = _block("hoja", 1, 13)
    root_tip = _block("hoja", 13, 17) + _block("raiz", 1, 5)
    food = vegetable + _block("hoja", 17, 23) + _block("raiz", 5, 9)

    h1 = _hierarchy(
        {"hoja_verde": green_leaf, "raiz": root_tip, "verdura": vegetable, "alimento": food},
        {"hoja_verde": "verdura", "raiz": "verdura", "verdura": "alimento", "alimento": None},
    )
    h2 = _hierarchy(
        {"hoja_fina": fine_leaf, "leaf": leaf, "root": root, "vegetal": leaf + root},
        {"hoja_fina": "leaf", "leaf": "vegetal", "root": "vegetal", "vegetal": None},
    )

    assert _phi_between(h1, h2, "verdura", "leaf") >= 0.85
    matches = {(match.a, match.b) for match in aroma(h1, h2)}
    assert ("verdura", "leaf") not in matches
    assert ("verdura", "hoja_fina") in matches


def test_aroma_matches_both_directions_for_identical_hierarchies():
    shared = frozenset(_block("t", 1, 11))
    wider = shared | frozenset(_block("u", 1, 11))
    h1 = _hierarchy({"concepto": list(shared), "todo": list(wider)}, {"concepto": "todo", "todo": None})
    h2 = _hierarchy({"concepto": list(shared), "todo": list(wider)}, {"concepto": "todo", "todo": None})

    assert [(match.a, match.b) for match in aroma(h1, h2)] == [("concepto", "concepto")]
    assert [(match.a, match.b) for match in aroma(h2, h1)] == [("concepto", "concepto")]


def test_aroma_returns_empty_below_five_shared_terms():
    h1 = _hierarchy({"x": ["t1", "t2"], "r": ["t1", "t2", "t3"]}, {"x": "r", "r": None})
    h2 = _hierarchy({"y": ["t1", "t2"], "s": ["t1", "t2", "t4"]}, {"y": "s", "s": None})

    assert aroma(h1, h2) == []
