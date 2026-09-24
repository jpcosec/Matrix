"""Tests for assembling the block hypertensor from a LogicalSystem."""

from __future__ import annotations

import pytest

from src.operational_model import (
    Context,
    Fact,
    LiSpace,
    LogicalSystem,
    Name,
    Proposition,
    Relation,
    Symbol,
    Thing,
    TruthValue,
    WiGame,
)
from src.operational_model.system.hypertensor import (
    assemble_block_matrix,
    assemble_global_matrix,
    qualify,
    routed_wigame_ids,
    unqualify,
)


def build_routed_system() -> LogicalSystem:
    """Builds two contexts, each routing to one world, sharing a symbol."""

    system = LogicalSystem()
    for relation_id in ("grosor", "sabor"):
        system.register_relation(Relation(relation_id, relation_id))
    for symbol_id in ("hoja", "gruesa", "amarga"):
        system.register_thing(Thing(Symbol(symbol_id), Name(symbol_id)))

    w1 = WiGame(
        wigame_id="w:grosor",
        li=LiSpace("li:grosor", ["hoja"], ["gruesa"], "grosor"),
    )
    w2 = WiGame(
        wigame_id="w:sabor",
        li=LiSpace("li:sabor", ["hoja"], ["amarga"], "sabor"),
    )
    system.register_wigame(w1)
    system.register_wigame(w2)
    w1.add_fact(
        Fact(
            proposition=Proposition("grosor", "hoja", "gruesa", "w:grosor"),
            truth=TruthValue.TRUE,
        )
    )

    root = Context(context_id="ctx:root")
    leaf = Context(context_id="ctx:sabor")
    root.route_to_context("ctx:sabor")
    root.route_to_wigame("w:grosor")
    leaf.route_to_wigame("w:sabor")
    system.register_context(root)
    system.register_context(leaf)
    return system


def test_routed_wigames_follow_the_context_tree() -> None:
    system = build_routed_system()

    assert routed_wigame_ids(system, ["ctx:root", "ctx:sabor"]) == ["w:grosor", "w:sabor"]


def test_context_matrix_holds_the_parent_child_route() -> None:
    system = build_routed_system()

    block = assemble_block_matrix(system)

    assert block.context_matrix.get("ctx:root", "ctx:sabor") is True
    assert block.context_matrix.get("ctx:sabor", "ctx:root") is False


def test_shared_symbol_does_not_collide_across_worlds() -> None:
    system = build_routed_system()

    block = assemble_block_matrix(system)
    rows = block.truth_matrix.row_axis

    # `hoja` is a subject in both worlds and must appear twice, qualified.
    assert rows == ["w:grosor::hoja", "w:sabor::hoja"]
    assert len(rows) == len(set(rows))


def test_labels_round_trip_so_indexing_is_not_lost() -> None:
    system = build_routed_system()

    block = assemble_block_matrix(system)
    for label in block.truth_matrix.row_axis + block.truth_matrix.column_axis:
        wigame_id, symbol_id = unqualify(label)
        assert wigame_id in system.wigames
        assert qualify(wigame_id, symbol_id) == label


def test_unqualify_rejects_a_bare_label() -> None:
    with pytest.raises(ValueError, match="not qualified"):
        unqualify("hoja")


def test_global_matrix_contains_contexts_and_subjects() -> None:
    system = build_routed_system()

    global_matrix = assemble_global_matrix(system)

    assert global_matrix.row_axis == [
        "ctx:root",
        "ctx:sabor",
        "w:grosor::hoja",
        "w:sabor::hoja",
    ]
    assert global_matrix.column_axis[:2] == ["ctx:root", "ctx:sabor"]
    # the asserted fact survives into the Vi block
    assert global_matrix.get("w:grosor::hoja", "w:grosor::gruesa") == TruthValue.TRUE.value


def test_operational_matrix_is_truth_and_sense() -> None:
    system = build_routed_system()

    block = assemble_block_matrix(system)
    operational = block.evaluate_operational()

    assert operational.row_axis == block.truth_matrix.row_axis
    assert operational.column_axis == block.truth_matrix.column_axis
    # the asserted fact is true and its column is meaningful somewhere
    assert operational.get("w:grosor::hoja", "w:grosor::gruesa") == TruthValue.TRUE.value


def test_operational_matrix_gates_by_context() -> None:
    system = build_routed_system()
    block = assemble_block_matrix(system)

    # ctx:sabor only routes to w:sabor, so w:grosor's column is not admissible there.
    gated = block.evaluate_operational(context_id="ctx:sabor")

    assert gated.get("w:grosor::hoja", "w:grosor::gruesa") == "unsinnig"
    # under the context that does route to it, the fact survives
    allowed = block.evaluate_operational(context_id="ctx:root")
    assert allowed.get("w:grosor::hoja", "w:grosor::gruesa") == TruthValue.TRUE.value


def test_operational_matrix_rejects_unknown_context() -> None:
    system = build_routed_system()
    block = assemble_block_matrix(system)

    with pytest.raises(ValueError, match="not a row of the sense matrix"):
        block.evaluate_operational(context_id="ctx:nope")
