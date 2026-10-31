"""Tests for order utilities in src/operational_model/core/relations/order.py."""

from pathlib import Path

import pytest
import yaml

from src.operational_model.core.relations.order import (
    CycleError,
    UnknownNodeError,
    assert_acyclic,
    is_total,
    linear_extension,
    topological_sequence,
)

RAGOUT_YAML = (
    Path(__file__).resolve().parents[1] / "tools" / "kb" / "machines" / "ragout.yaml"
)

CHAIN_NODES = ["picar", "sofreir", "desglasar", "agregar_caldo", "cocinar_lento", "servir"]


def _chain_edges() -> list[tuple[str, str]]:
    return [
        (edge["from"], edge["to"])
        for edge in yaml.safe_load(RAGOUT_YAML.read_text())["edges"]
    ]


def test_ragout_chain_is_total() -> None:
    assert is_total(CHAIN_NODES, _chain_edges()) is True


def test_ragout_chain_topological_sequence_equals_declared_order() -> None:
    assert topological_sequence(CHAIN_NODES, _chain_edges()) == CHAIN_NODES


def test_ragout_chain_linear_extension_matches_topological_sequence() -> None:
    edges = _chain_edges()
    assert linear_extension(CHAIN_NODES, edges) == topological_sequence(CHAIN_NODES, edges)


def test_ragout_chain_is_acyclic() -> None:
    assert_acyclic(CHAIN_NODES, _chain_edges())


def test_cycle_raises_typed_error_naming_the_cycle() -> None:
    with pytest.raises(CycleError) as excinfo:
        assert_acyclic(["a", "b", "c"], [("a", "b"), ("b", "c"), ("c", "a")])
    assert "cycle" in str(excinfo.value)
    assert "a" in str(excinfo.value)
    assert "b" in str(excinfo.value)
    assert "c" in str(excinfo.value)


def test_cycle_message_lists_cycle_in_order() -> None:
    with pytest.raises(CycleError) as excinfo:
        assert_acyclic(["a", "b", "c"], [("a", "b"), ("b", "c"), ("c", "a")])
    assert str(excinfo.value) == "cycle: a -> b -> c -> a"


def test_self_loop_is_a_cycle() -> None:
    with pytest.raises(CycleError) as excinfo:
        assert_acyclic(["a"], [("a", "a")])
    assert "cycle: a -> a" in str(excinfo.value)


def test_branched_dag_is_deterministic_and_preserves_independent_order() -> None:
    branches = [
        "prep",
        "cook",
        "serve",
        "a_root",
        "b_left",
        "c_right",
        "z_tail",
    ]
    edges = [
        ("a_root", "b_left"),
        ("a_root", "c_right"),
        ("b_left", "z_tail"),
        ("c_right", "z_tail"),
    ]
    expected = ["prep", "cook", "serve", "a_root", "b_left", "c_right", "z_tail"]
    assert topological_sequence(branches, edges) == expected
    assert topological_sequence(branches, edges) == topological_sequence(branches, edges)
    assert linear_extension(branches, edges) == topological_sequence(branches, edges)


def test_branched_dag_is_not_total() -> None:
    branches = ["root", "left", "right"]
    edges = [("root", "left"), ("root", "right")]
    assert is_total(branches, edges) is False


def test_is_total_empty_and_single_node_are_true() -> None:
    assert is_total([], []) is True
    assert is_total(["solo"], []) is True


def test_is_total_reversed_order_still_total() -> None:
    assert is_total(["a", "b"], [("b", "a")]) is True


def test_unknown_node_in_edge_raises_value_error() -> None:
    with pytest.raises(ValueError) as excinfo:
        assert_acyclic(["a", "b"], [("a", "ghost")])
    assert "ghost" in str(excinfo.value)

    with pytest.raises(ValueError):
        topological_sequence(["a", "b"], [("ghost", "a")])

    with pytest.raises(ValueError):
        linear_extension(["a", "b"], [("a", "ghost")])

    with pytest.raises(ValueError):
        is_total(["a", "b"], [("a", "ghost")])


def test_unknown_node_error_is_typed() -> None:
    with pytest.raises(UnknownNodeError):
        is_total(["a"], [("a", "zzz")])
    assert issubclass(UnknownNodeError, ValueError)
    assert issubclass(CycleError, ValueError)
