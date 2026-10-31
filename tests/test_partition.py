"""Tests for using E(R) and D_i as a partition criterion."""

from __future__ import annotations

from src.operational_model import (
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
from src.operational_model.system.partition import (
    compare_partition,
    middle_term_reuse,
    score_wigame,
)


def _world(system, wigame_id, relation_id, axis_a, axis_b, pairs):
    """Registers one WiGame with true facts for the given pairs."""

    if relation_id not in system.relations:
        system.register_relation(Relation(relation_id, relation_id))
    for symbol_id in list(axis_a) + list(axis_b):
        if symbol_id not in system.things:
            system.register_thing(Thing(Symbol(symbol_id), Name(symbol_id)))
    wigame = WiGame(
        wigame_id=wigame_id,
        li=LiSpace(
            li_id=f"li:{wigame_id}",
            axis_a=list(axis_a),
            axis_b=list(axis_b),
            relation_id=relation_id,
        ),
    )
    system.register_wigame(wigame)
    for subject, obj in pairs:
        wigame.add_fact(
            Fact(
                proposition=Proposition(relation_id, subject, obj, wigame_id),
                truth=TruthValue.TRUE,
            )
        )
    return wigame


def _case_triplet(plants: list[str]):
    """Returns `(composite, [part1, part2])` ready for `compare_partition`."""

    composite, part1, part2 = build_case(plants)
    return composite, [part1, part2]


def build_case(plants: list[str]):
    """Builds `grosor_hoja` against `tiene_parte` + `grosor` for N plants."""

    system = LogicalSystem()
    composite = _world(
        system,
        "w:comp",
        "grosor_hoja",
        plants,
        ["gruesa", "fina"],
        [(p, "gruesa") for p in plants],
    )
    part1 = _world(
        system, "w:parte", "tiene_parte", plants, ["hoja"], [(p, "hoja") for p in plants]
    )
    part2 = _world(
        system, "w:grosor", "grosor", ["hoja"], ["gruesa", "fina"], [("hoja", "gruesa")]
    )
    return composite, part1, part2


def test_score_reports_the_tautological_column() -> None:
    _composite, part1, _part2 = build_case(["lechuga", "acelga", "espinaca"])

    score = score_wigame(part1)

    assert score.tautological_columns == ("hoja",)
    assert score.discriminative_power == 0.0
    assert score.cells == 3


def test_factoring_the_middle_term_is_cheaper_even_at_three_subjects() -> None:
    composite, part1, part2 = build_case(["lechuga", "acelga", "espinaca"])

    verdict = compare_partition(composite, [part1, part2])

    # measured: 3x2=6 cells composite against 3x1 + 1x2 = 5 decomposed
    assert verdict.composite_cells == 6
    assert verdict.decomposed_cells == 5
    assert verdict.choice == "decomposed"
    assert verdict.metric == "cells"
    assert "cheaper outright" in verdict.reason


def test_the_advantage_widens_with_the_number_of_subjects() -> None:
    small = compare_partition(*_case_triplet(["a", "b", "c"]))
    large = compare_partition(*_case_triplet([f"planta_{i}" for i in range(300)]))

    assert small.choice == large.choice == "decomposed"
    # the composite grows as subjects x values, the split as subjects x 1 plus a constant
    assert small.composite_cells - small.decomposed_cells == 1
    assert large.composite_cells == 600
    assert large.decomposed_cells == 302
    assert large.composite_cells - large.decomposed_cells == 298
    assert large.reuse == 300


def test_verdict_carries_the_scores_of_every_part() -> None:
    composite, part1, part2 = build_case(["lechuga", "acelga", "espinaca"])

    verdict = compare_partition(composite, [part1, part2])

    assert verdict.composite.wigame_id == "w:comp"
    assert [p.wigame_id for p in verdict.parts] == ["w:parte", "w:grosor"]
    assert [p.cells for p in verdict.parts] == [3, 2]


def test_a_split_that_only_adds_cells_keeps_the_composite() -> None:
    system = LogicalSystem()
    # A composite that is already tight, split into two equally wide worlds that
    # share no middle term: pure overhead, nothing to amortise.
    composite = _world(
        system, "w:tight", "r", ["x"], ["v1"], [("x", "v1")]
    )
    part1 = _world(system, "w:p1", "r1", ["x"], ["m1", "m2"], [("x", "m1")])
    part2 = _world(system, "w:p2", "r2", ["zzz"], ["v1", "v2"], [("zzz", "v1")])

    verdict = compare_partition(composite, [part1, part2])

    assert verdict.choice == "composite"
    assert not verdict.splits
    assert verdict.reuse == 0
    assert verdict.metric == "discriminative_power"


def test_middle_term_reuse_needs_a_shared_term() -> None:
    system = LogicalSystem()
    a = _world(system, "w:a", "r1", ["x"], ["m"], [("x", "m")])
    b = _world(system, "w:b", "r2", ["m"], ["y"], [("m", "y")])
    c = _world(system, "w:c", "r3", ["otro"], ["y"], [("otro", "y")])

    assert middle_term_reuse([a, b]) == 1
    assert middle_term_reuse([a, c]) == 0
    assert middle_term_reuse([a]) == 0
