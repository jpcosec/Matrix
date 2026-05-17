"""Focused tests for dimensional collapse migrated from legacy runtime.

Dimensional collapse computes object-object similarity as W = V @ V^T,
where V is an object×properties truth matrix. W[i,j] is true when
objects i and j share at least one property.
"""

from src.operational_model.matrices.boolean_matrix import BooleanMatrix


def test_collapse_connected_objects():
    V = BooleanMatrix(
        row_axis=["o1", "o2", "o3"],
        column_axis=["p1", "p2"],
        values=[
            [True, False],
            [True, False],
            [False, True],
        ],
    )
    W = V.collapse_similarity()
    assert W.row_axis == ["o1", "o2", "o3"]
    assert W.column_axis == ["o1", "o2", "o3"]
    # o1 and o2 share p1
    assert W.get("o1", "o2") is True
    assert W.get("o2", "o1") is True
    # o1 and o3 share nothing
    assert W.get("o1", "o3") is False
    assert W.get("o3", "o1") is False


def test_collapse_self_loop():
    V = BooleanMatrix(
        row_axis=["o1"],
        column_axis=["p1", "p2"],
        values=[[True, True]],
    )
    W = V.collapse_similarity()
    assert W.get("o1", "o1") is True


def test_collapse_no_shared_properties():
    V = BooleanMatrix(
        row_axis=["o1", "o2"],
        column_axis=["p1", "p2"],
        values=[
            [True, False],
            [False, True],
        ],
    )
    W = V.collapse_similarity()
    assert W.get("o1", "o2") is False
    assert W.get("o2", "o1") is False


def test_collapse_three_objects_chain():
    V = BooleanMatrix(
        row_axis=["o1", "o2", "o3"],
        column_axis=["p1", "p2", "p3"],
        values=[
            [True, False, False],
            [True, True, False],
            [False, True, True],
        ],
    )
    W = V.collapse_similarity()
    assert W.get("o1", "o2") is True
    assert W.get("o2", "o1") is True
    assert W.get("o2", "o3") is True
    assert W.get("o3", "o2") is True
    # o1 and o3 share no direct property (only transitive via o2)
    assert W.get("o1", "o3") is False
    assert W.get("o3", "o1") is False
