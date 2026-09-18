"""Tests for traced deduction over the implication matrix."""

from __future__ import annotations

from src.operational_model import (
    Fact,
    IfFormula,
    LiSpace,
    LogicalSystem,
    Name,
    Proposition,
    Relation,
    RelationAtom,
    SenseValue,
    Symbol,
    Thing,
    TruthValue,
    WiGame,
)
from src.operational_model.core.evidence import make_evidence
from src.operational_model.system.deduction import deduce

WIGAME = "wigame:comida"

# The rule shares the WiGame relation: a LiSpace admits exactly one relation,
# so cross-relation implications cannot produce facts inside a single world.
RULE = IfFormula(
    RelationAtom("es", "x", "verdura"),
    RelationAtom("es", "x", "comestible"),
)
UNKNOWN_RULE = IfFormula(
    RelationAtom("es", "y", "verdura"),
    RelationAtom("es", "y", "comestible"),
)


def build_world() -> tuple[LogicalSystem, list[Fact]]:
    """Builds a small world with three true facts and one implication rule."""

    system = LogicalSystem()
    system.register_relation(Relation("es", "es"))
    for symbol_id in ("x", "y", "z", "verdura", "fruta", "comestible"):
        system.register_thing(Thing(Symbol(symbol_id), Name(symbol_id)))
    system.register_wigame(
        WiGame(
            wigame_id=WIGAME,
            li=LiSpace(
                li_id="li:comida",
                axis_a=["x", "y", "z"],
                axis_b=["verdura", "fruta", "comestible"],
                relation_id="es",
            ),
        )
    )
    facts = [
        Fact(Proposition("es", "x", "verdura", WIGAME), TruthValue.TRUE),
        Fact(Proposition("es", "y", "fruta", WIGAME), TruthValue.TRUE),
        Fact(Proposition("es", "z", "fruta", WIGAME), TruthValue.TRUE),
    ]
    for fact in facts:
        system.add_fact(fact)
    system.rules.append(RULE)
    return system, facts


def test_deduce_derives_with_derived_from():
    system, facts = build_world()

    derived = deduce(system, WIGAME)

    assert [fact.proposition.sexpr() for fact in derived] == ["(es x comestible)"]
    assert derived[0].truth == TruthValue.TRUE
    assert derived[0].evidence["tier"] == "inferred"
    assert derived[0].evidence["derived_from"] == [facts[0].fact_id]
    assert derived[0].evidence["rule"] == RULE.to_sexpr()
    assert system.wigames[WIGAME].Vi.get("x", "comestible") == TruthValue.TRUE.value


def test_unknown_facts_do_not_feed_deduction():
    system, _ = build_world()
    system.rules.append(UNKNOWN_RULE)
    system.add_fact(
        Fact(
            Proposition("es", "y", "verdura", WIGAME),
            TruthValue.UNKNOWN,
            evidence=make_evidence(tier="confirmed"),
        )
    )

    derived = deduce(system, WIGAME)

    assert [fact.proposition.sexpr() for fact in derived] == ["(es x comestible)"]


def test_statistical_facts_do_not_feed_deduction():
    system, _ = build_world()
    system.rules.append(UNKNOWN_RULE)
    system.add_fact(
        Fact(
            Proposition("es", "y", "verdura", WIGAME),
            TruthValue.TRUE,
            evidence=make_evidence(tier="statistical", curation="proposed"),
        )
    )

    derived = deduce(system, WIGAME)

    assert [fact.proposition.sexpr() for fact in derived] == ["(es x comestible)"]


def test_deduce_is_idempotent():
    system, _ = build_world()

    first = deduce(system, WIGAME)
    second = deduce(system, WIGAME)

    assert first
    assert second == []


def test_derived_facts_keep_sinnvoll_sense():
    system, _ = build_world()

    deduce(system, WIGAME)

    assert system.wigames[WIGAME].Si.get("x", "comestible") == SenseValue.SINNVOLL.value
