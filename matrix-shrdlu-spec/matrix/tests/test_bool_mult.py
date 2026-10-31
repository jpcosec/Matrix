"""Focused tests for boolean matrix multiplication migrated from legacy runtime."""

from src.operational_model.matrices.boolean_matrix import BooleanMatrix


def test_bool_mult_basic():
    A = BooleanMatrix(
        row_axis=["x", "y"],
        column_axis=["a", "b"],
        values=[[True, False], [False, True]],
    )
    B = BooleanMatrix(
        row_axis=["a", "b"],
        column_axis=["p", "q"],
        values=[[True, True], [False, True]],
    )
    C = A.bool_mult(B)
    assert C.row_axis == ["x", "y"]
    assert C.column_axis == ["p", "q"]
    assert C.get("x", "p") is True
    assert C.get("x", "q") is True
    assert C.get("y", "p") is False
    assert C.get("y", "q") is True


def test_bool_mult_no_connection():
    A = BooleanMatrix(
        row_axis=["x"],
        column_axis=["a"],
        values=[[False]],
    )
    B = BooleanMatrix(
        row_axis=["a"],
        column_axis=["p"],
        values=[[True]],
    )
    C = A.bool_mult(B)
    assert C.get("x", "p") is False


def test_bool_mult_square():
    I = BooleanMatrix(
        row_axis=["a", "b"],
        column_axis=["a", "b"],
        values=[[True, False], [False, True]],
    )
    C = I.bool_mult(I)
    assert C.get("a", "a") is True
    assert C.get("a", "b") is False
    assert C.get("b", "a") is False
    assert C.get("b", "b") is True


def test_bool_mult_identity():
    I = BooleanMatrix(
        row_axis=["a", "b"],
        column_axis=["a", "b"],
        values=[[True, False], [False, True]],
    )
    A = BooleanMatrix(
        row_axis=["a", "b"],
        column_axis=["x"],
        values=[[True], [False]],
    )
    C = I.bool_mult(A)
    assert C.get("a", "x") is True
    assert C.get("b", "x") is False


def test_transpose():
    A = BooleanMatrix(
        row_axis=["x", "y"],
        column_axis=["a", "b", "c"],
        values=[[True, False, True], [False, True, False]],
    )
    T = A.transpose()
    assert T.row_axis == ["a", "b", "c"]
    assert T.column_axis == ["x", "y"]
    assert T.get("a", "x") is True
    assert T.get("a", "y") is False
    assert T.get("b", "x") is False
    assert T.get("b", "y") is True
