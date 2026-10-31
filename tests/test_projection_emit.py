"""Tests for the inverse projection: WiGame/matrices back to s-expressions."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from src.operational_model import (
    Fact,
    LiSpace,
    LogicalSystem,
    Proposition,
    SExpressionRuntime,
    SenseValue,
    TruthValue,
    WiGame,
)
from src.operational_model.matrices.si_matrix import SiMatrix
from src.operational_model.matrices.vi_matrix import ViMatrix
from src.operational_model.system.projection_emit import (
    matrix_to_s_expressions,
    system_to_s_expressions,
    wigame_to_s_expressions,
)

RAGOUT_YAML = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "kb"
    / "machines"
    / "ragout.yaml"
)

RAGOUT_CHAIN = [
    "picar",
    "sofreir",
    "desglasar",
    "agregar_caldo",
    "cocinar_lento",
    "servir",
]


def build_chain_wigame() -> WiGame:
    """Builds a `precede` WiGame whose facts form the ragout chain reversed.

    Facts are inserted in reversed chain order so any sequence-driven
    reordering is actually observable.
    """

    edges = [
        (edge["from"], edge["to"])
        for edge in yaml.safe_load(RAGOUT_YAML.read_text())["edges"]
    ]
    wigame = WiGame(
        wigame_id="wigame:ragout",
        li=LiSpace(
            li_id="li:ragout",
            axis_a=[frm for frm, _ in edges],
            axis_b=[to for _, to in edges],
            relation_id="precede",
        ),
    )
    for frm, to in reversed(edges):
        wigame.add_fact(
            Fact(
                Proposition("precede", frm, to, wigame.wigame_id),
                TruthValue.TRUE,
            )
        )
    return wigame


def build_round_trip_system() -> LogicalSystem:
    """Builds a small system with one WiGame holding TRUE/UNKNOWN facts."""

    system = LogicalSystem()
    wigame = WiGame(
        wigame_id="wigame:precede",
        li=LiSpace(
            li_id="li:precede",
            axis_a=["a", "b", "c", "z"],
            axis_b=["b", "c", "d", "e"],
            relation_id="precede",
        ),
    )
    system.register_wigame(wigame)
    true_facts = [
        Fact(Proposition("precede", "a", "b", wigame.wigame_id), TruthValue.TRUE),
        Fact(Proposition("precede", "b", "c", wigame.wigame_id), TruthValue.TRUE),
        Fact(Proposition("precede", "c", "d", wigame.wigame_id), TruthValue.TRUE),
        Fact(Proposition("precede", "z", "e", wigame.wigame_id), TruthValue.TRUE),
    ]
    unknown_fact = Fact(
        Proposition("precede", "a", "d", wigame.wigame_id), TruthValue.UNKNOWN
    )
    for fact in true_facts + [unknown_fact]:
        system.add_fact(fact)
    return system


def test_matrix_to_s_expressions_recovers_true_and_sinnvoll_cells() -> None:
    vi = ViMatrix(
        row_axis=["a", "b"],
        column_axis=["x", "y"],
        values=[
            [TruthValue.TRUE.value, TruthValue.TRUE.value],
            [TruthValue.FALSE.value, TruthValue.TRUE.value],
        ],
    )
    si = SiMatrix(
        row_axis=["a", "b"],
        column_axis=["x", "y"],
        values=[
            [SenseValue.SINNVOLL.value, SenseValue.SINNLOS.value],
            [SenseValue.SINNVOLL.value, SenseValue.SINNVOLL.value],
        ],
    )

    assert matrix_to_s_expressions(vi, si, "R") == [
        "(R a x)",
        "(R b y)",
    ]


def test_matrix_to_s_expressions_skips_true_but_sinnlos_cells() -> None:
    vi = ViMatrix(
        row_axis=["a"],
        column_axis=["x", "y"],
        values=[[TruthValue.TRUE.value, TruthValue.TRUE.value]],
    )
    si = SiMatrix(
        row_axis=["a"],
        column_axis=["x", "y"],
        values=[[SenseValue.SINNVOLL.value, SenseValue.SINNLOS.value]],
    )

    assert matrix_to_s_expressions(vi, si, "R") == ["(R a x)"]


def test_matrix_to_s_expressions_shape_mismatch_raises_naming_both_shapes() -> None:
    vi = ViMatrix(
        row_axis=["a"],
        column_axis=["x"],
        values=[[TruthValue.TRUE.value]],
    )
    si = SiMatrix(
        row_axis=["a", "b"],
        column_axis=["x"],
        values=[
            [SenseValue.SINNVOLL.value],
            [SenseValue.SINNVOLL.value],
        ],
    )

    with pytest.raises(ValueError, match=r"vi \(1, 1\), si \(2, 1\)"):
        matrix_to_s_expressions(vi, si, "R")


def test_round_trip_rebuilds_original_true_facts() -> None:
    system = build_round_trip_system()
    original = system.wigames["wigame:precede"]

    emitted = wigame_to_s_expressions(original)
    fresh = LogicalSystem()
    runtime = SExpressionRuntime(fresh)
    results = [runtime.evaluate(expression) for expression in emitted]

    assert all(result.status == "accept" for result in results)
    rebuilt = fresh.wigames["wigame:precede"]
    original_sexprs = {
        fact.proposition.sexpr()
        for fact in original.facts.values()
        if fact.truth == TruthValue.TRUE
    }
    rebuilt_sexprs = {fact.proposition.sexpr() for fact in rebuilt.facts.values()}
    assert rebuilt_sexprs == original_sexprs
    assert len(rebuilt_sexprs) == 4
    assert all(
        fact.proposition.wigame_id == rebuilt.wigame_id
        for fact in rebuilt.facts.values()
    )


def test_sequence_controls_assert_order_and_default_is_deterministic() -> None:
    system = build_round_trip_system()
    wigame = system.wigames["wigame:precede"]

    ordered = wigame_to_s_expressions(wigame, sequence=["b", "a", "c"])
    assert [line for line in ordered if line.startswith("(assert")] == [
        "(assert wigame:precede (precede b c))",
        "(assert wigame:precede (precede a b))",
        "(assert wigame:precede (precede c d))",
        "(assert wigame:precede (precede z e))",
    ]

    first = wigame_to_s_expressions(wigame)
    second = wigame_to_s_expressions(wigame)
    assert first == second
    assert [line for line in first if line.startswith("(assert")] == [
        "(assert wigame:precede (precede a b))",
        "(assert wigame:precede (precede b c))",
        "(assert wigame:precede (precede c d))",
        "(assert wigame:precede (precede z e))",
    ]


def test_ragout_yaml_chain_assert_order_follows_sequence() -> None:
    wigame = build_chain_wigame()

    emitted = wigame_to_s_expressions(wigame, sequence=RAGOUT_CHAIN)
    assert_lines = [line for line in emitted if line.startswith("(assert")]
    expected = [
        f"(assert wigame:ragout (precede {frm} {to}))"
        for frm, to in [
            ("picar", "sofreir"),
            ("sofreir", "desglasar"),
            ("desglasar", "agregar_caldo"),
            ("agregar_caldo", "cocinar_lento"),
            ("cocinar_lento", "servir"),
        ]
    ]
    assert assert_lines == expected


def test_system_to_s_expressions_orders_wigames_by_id() -> None:
    system = build_round_trip_system()
    other = WiGame(
        wigame_id="wigame:alpha",
        li=LiSpace(
            li_id="li:alpha",
            axis_a=["dog"],
            axis_b=["kind"],
            relation_id="es",
        ),
    )
    system.register_wigame(other)
    system.add_fact(
        Fact(Proposition("es", "dog", "kind", other.wigame_id), TruthValue.TRUE)
    )

    emitted = system_to_s_expressions(system)
    lines = " ".join(emitted)
    assert lines.index("wigame:alpha") < lines.index("wigame:precede")
    assert all(
        line.startswith("(assert")
        for line in emitted
        if "(" in line and line.startswith("(assert")
    )
