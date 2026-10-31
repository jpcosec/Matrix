"""Tests for sia.graph: thresholds, closure and non-transitivity."""

from __future__ import annotations

import numpy as np

from sia.graph import implicative_graph, transitive_closure, transitive_reduction


def build_phi() -> np.ndarray:
    """Returns a 4x4 intensity matrix with known arcs."""

    phi = np.zeros((4, 4))
    phi[0, 1] = 0.99
    phi[1, 2] = 0.96
    phi[2, 3] = 0.90
    phi[0, 2] = 0.86
    return phi


def test_thresholds_select_the_expected_arcs():
    graph = implicative_graph(build_phi())

    assert graph[0.99][0, 1]
    assert not graph[0.99][1, 2]
    assert graph[0.95][1, 2]
    assert not graph[0.95][2, 3]
    assert graph[0.90][2, 3]
    assert not graph[0.90][0, 2]
    assert graph[0.85][0, 2]


def test_implicative_graph_has_no_self_loops():
    graph = implicative_graph(build_phi())

    assert not np.any([np.diag(arcs).any() for arcs in graph.values()])


def test_graph_does_not_infer_transitive_arcs():
    graph = implicative_graph(build_phi(), thresholds=(0.99,))

    assert graph[0.99][0, 1]
    assert not graph[0.99][0, 2]


def test_transitive_closure_adds_two_step_arc():
    adj = np.zeros((3, 3), dtype=bool)
    adj[0, 1] = True
    adj[1, 2] = True
    closure = transitive_closure(adj)

    assert closure[0, 1] and closure[1, 2] and closure[0, 2]


def test_transitive_reduction_removes_implied_arc():
    adj = np.zeros((3, 3), dtype=bool)
    adj[0, 1] = True
    adj[1, 2] = True
    adj[0, 2] = True
    reduced = transitive_reduction(adj)

    assert reduced[0, 1] and reduced[1, 2]
    assert not reduced[0, 2]
