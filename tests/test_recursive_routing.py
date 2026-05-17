"""Focused tests for recursive routing migrated from legacy runtime.

Recursive routing propagates connectivity through boolean matrix power:
subjects are connected if a chain of shared properties or projections exists.
"""

from src.operational_model.matrices.boolean_matrix import BooleanMatrix
from src.operational_model.routing.routing_projection import (
    RoutingProjection,
)


def test_recursive_power_two_step():
    W = BooleanMatrix(
        row_axis=["a", "b", "c"],
        column_axis=["a", "b", "c"],
        values=[
            [True, True, False],
            [True, True, True],
            [False, True, True],
        ],
    )
    W2 = W.recursive_power(steps=1)
    assert W2.get("a", "c") is True
    assert W2.get("c", "a") is True


def test_recursive_power_disconnected():
    W = BooleanMatrix(
        row_axis=["a", "b"],
        column_axis=["a", "b"],
        values=[
            [True, False],
            [False, True],
        ],
    )
    W2 = W.recursive_power(steps=2)
    assert W2.get("a", "b") is False


def test_routing_via_projection():
    subjects_a = ["o1_a", "o2_a", "o3_a"]
    subjects_b = ["o1_b", "o2_b"]
    R = RoutingProjection.empty(
        source_wigame_id="wigame_a",
        source_axis=subjects_a,
        target_wigame_id="wigame_b",
        target_axis=subjects_b,
    )
    R.link("o2_a", "o1_b")

    projected = R.project_subjects(["o2_a"])
    assert "o1_b" in projected
    assert "o2_b" not in projected

    projected_none = R.project_subjects(["o1_a"])
    assert projected_none == []


def test_multi_hop_routing():
    subjects_a = ["a1", "a2"]
    subjects_b = ["b1", "b2"]
    subjects_c = ["c1"]

    Rab = RoutingProjection.empty(
        source_wigame_id="wa",
        source_axis=subjects_a,
        target_wigame_id="wb",
        target_axis=subjects_b,
    )
    Rab.link("a1", "b1")

    Rbc = RoutingProjection.empty(
        source_wigame_id="wb",
        source_axis=subjects_b,
        target_wigame_id="wc",
        target_axis=subjects_c,
    )
    Rbc.link("b1", "c1")

    hop1 = Rab.project_subjects(["a1"])
    assert "b1" in hop1

    hop2 = Rbc.project_subjects(hop1)
    assert "c1" in hop2


def test_routing_composition_via_bool_mult():
    Rab = RoutingProjection(
        source_wigame_id="wa",
        target_wigame_id="wb",
        row_axis=["a1", "a2"],
        column_axis=["b1", "b2"],
        values=[[True, False], [False, True]],
    )
    Rbc = RoutingProjection(
        source_wigame_id="wb",
        target_wigame_id="wc",
        row_axis=["b1", "b2"],
        column_axis=["c1"],
        values=[[True], [False]],
    )
    Rac = Rab.bool_mult(Rbc)
    assert Rac.get("a1", "c1") is True
    assert Rac.get("a2", "c1") is False
