"""Tests for object-to-subject composition across a shared middle term."""

from __future__ import annotations

from src.operational_model import (
    Fact,
    LiSpace,
    LogicalSystem,
    Name,
    Proposition,
    Relation,
    SenseValue,
    Symbol,
    Thing,
    TruthValue,
    WiGame,
)
from src.operational_model.routing.middle_term import (
    compose,
    compose_pairs,
    middle_terms,
)


def _world(system, wigame_id, relation_id, axis_a, axis_b, pairs):
    """Registers one WiGame with true facts for every given pair."""

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


def build_legumbre() -> tuple[WiGame, WiGame]:
    """Builds `(debe legumbre guisarse)` and `(necesita guisarse fuego)`."""

    system = LogicalSystem()
    w1 = _world(
        system, "w:debe", "debe", ["legumbre"], ["guisarse"], [("legumbre", "guisarse")]
    )
    w2 = _world(
        system, "w:nec", "necesita", ["guisarse"], ["fuego"], [("guisarse", "fuego")]
    )
    # The whole point: the two relations differ, so transitive_inference cannot chain them.
    assert w1.relation_id != w2.relation_id
    return w1, w2


def test_middle_term_is_detected_and_composed() -> None:
    w1, w2 = build_legumbre()

    assert middle_terms(w1, w2) == ["guisarse"]
    assert compose(w1, w2) == [("legumbre", "guisarse", "fuego")]
    assert compose_pairs(w1, w2) == [("legumbre", "fuego")]


def test_senseless_first_leg_breaks_the_chain() -> None:
    w1, w2 = build_legumbre()
    w1.Si.set("legumbre", "guisarse", SenseValue.SINNLOS.value)

    assert middle_terms(w1, w2) == ["guisarse"]
    assert compose(w1, w2) == []
    assert compose_pairs(w1, w2) == []


def test_unsinnig_second_leg_breaks_the_chain() -> None:
    w1, w2 = build_legumbre()
    w2.Si.set("guisarse", "fuego", SenseValue.UNSINNIG.value)

    assert compose(w1, w2) == []


def test_leg_that_is_not_true_breaks_the_chain() -> None:
    w1, w2 = build_legumbre()
    w2.Vi.set("guisarse", "fuego", TruthValue.UNKNOWN.value)

    assert compose(w1, w2) == []


def test_no_shared_middle_term_yields_nothing() -> None:
    system = LogicalSystem()
    w1 = _world(system, "w:a", "debe", ["legumbre"], ["guisarse"], [("legumbre", "guisarse")])
    w2 = _world(system, "w:b", "necesita", ["horno"], ["fuego"], [("horno", "fuego")])

    assert middle_terms(w1, w2) == []
    assert compose(w1, w2) == []
    assert compose_pairs(w1, w2) == []


def test_fan_composition_is_deterministic() -> None:
    system = LogicalSystem()
    subjects = ["lechuga", "acelga", "espinaca"]
    w1 = _world(
        system,
        "w:parte",
        "tiene_parte",
        subjects,
        ["hoja"],
        [(s, "hoja") for s in subjects],
    )
    w2 = _world(
        system,
        "w:grosor",
        "grosor",
        ["hoja"],
        ["gruesa", "nervada"],
        [("hoja", "gruesa"), ("hoja", "nervada")],
    )

    composed = compose(w1, w2)
    assert len(composed) == 6
    assert composed[0] == ("lechuga", "hoja", "gruesa")
    assert composed == compose(w1, w2)
    assert compose_pairs(w1, w2) == [
        ("lechuga", "gruesa"),
        ("lechuga", "nervada"),
        ("acelga", "gruesa"),
        ("acelga", "nervada"),
        ("espinaca", "gruesa"),
        ("espinaca", "nervada"),
    ]
