"""Tests for cross-world rules, conjunctive antecedents and projections."""

from __future__ import annotations

from src.operational_model import (
    Fact,
    LiSpace,
    LogicalSystem,
    Name,
    Proposition,
    Relation,
    SExpressionRuntime,
    Symbol,
    Thing,
    TruthValue,
    WiGame,
)


def build_worlds() -> tuple[LogicalSystem, SExpressionRuntime]:
    """Builds an `implies` world and a `has_property` world sharing symbols."""

    system = LogicalSystem()
    system.register_relation(Relation("implies", "implies"))
    system.register_relation(Relation("has_property", "has_property"))
    for symbol_id in ("lechuga", "hoja", "verde", "verdura", "rugosa"):
        system.register_thing(Thing(Symbol(symbol_id), Name(symbol_id)))
    system.register_wigame(
        WiGame(
            wigame_id="wigame:implies",
            li=LiSpace(
                li_id="li:implies",
                axis_a=["lechuga"],
                axis_b=["hoja", "verde", "verdura", "rugosa"],
                relation_id="implies",
            ),
        )
    )
    system.register_wigame(
        WiGame(
            wigame_id="wigame:prop",
            li=LiSpace(
                li_id="li:prop",
                axis_a=["lechuga"],
                axis_b=["verde", "verdura"],
                relation_id="has_property",
            ),
        )
    )
    runtime = SExpressionRuntime(system)
    return system, runtime


def test_rule_can_conclude_in_another_relation():
    system, runtime = build_worlds()
    runtime.evaluate("(assert wigame:implies (implies lechuga hoja))")

    defined = runtime.evaluate("(define (if (implies lechuga hoja) (has_property lechuga verde)))")
    check = runtime.evaluate("(check wigame:prop (has_property lechuga verde))")
    chain = runtime.evaluate("(why wigame:prop (has_property lechuga verde))").payload["chain"]

    assert defined.payload["derived"] == ["(has_property lechuga verde)"]
    assert check.payload["truth"] == TruthValue.TRUE.value
    assert chain[0]["tier"] == "inferred"
    assert chain[0]["derived_from"]
    assert chain[1]["proposition"] == "(implies lechuga hoja)"


def test_conjunctive_rule_waits_for_every_conjunct():
    _, runtime = build_worlds()
    rule = "(define (if (and (implies lechuga hoja) (implies lechuga verde)) (implies lechuga verdura)))"
    runtime.evaluate("(assert wigame:implies (implies lechuga hoja))")

    first = runtime.evaluate(rule)
    runtime.evaluate("(assert wigame:implies (implies lechuga verde))")
    second = runtime.evaluate(rule)
    chain = runtime.evaluate("(why wigame:implies (implies lechuga verdura))").payload["chain"]

    assert first.payload["derived"] == []
    assert second.payload["derived"] == ["(implies lechuga verdura)"]
    assert {node["proposition"] for node in chain} == {
        "(implies lechuga verdura)",
        "(implies lechuga hoja)",
        "(implies lechuga verde)",
    }
    assert len(chain[0]["derived_from"]) == 2
    assert runtime.evaluate(rule).payload["derived"] == []


def test_unplaced_atom_is_reported():
    system, runtime = build_worlds()
    runtime.evaluate("(assert wigame:implies (implies lechuga hoja))")

    defined = runtime.evaluate("(define (if (implies lechuga hoja) (is lechuga morada)))")

    assert defined.payload["derived"] == []
    assert defined.payload["unplaced"] == ["(is lechuga morada)"]
    assert not [fact for fact in system.wigames["wigame:prop"].facts.values()]


def test_ambiguous_atom_is_reported():
    system, runtime = build_worlds()
    runtime.evaluate("(assert wigame:implies (implies lechuga hoja))")
    system.register_wigame(
        WiGame(
            wigame_id="wigame:prop2",
            li=LiSpace(
                li_id="li:prop2",
                axis_a=["lechuga"],
                axis_b=["verde", "verdura"],
                relation_id="has_property",
            ),
        )
    )

    defined = runtime.evaluate("(define (if (implies lechuga hoja) (has_property lechuga verde)))")

    assert defined.payload["derived"] == []
    assert defined.payload["ambiguous"][0]["atom"] == "(has_property lechuga verde)"
    assert defined.payload["ambiguous"][0]["candidates"] == ["wigame:prop", "wigame:prop2"]


def test_project_verb_registers_pairs():
    system, runtime = build_worlds()

    result = runtime.evaluate("(project wigame:implies wigame:prop (lechuga lechuga))")
    listed = runtime.evaluate("(return projections wigame:implies)").payload["projections"]
    projection = system.projections["wigame:implies->wigame:prop"]

    assert result.status == "accept"
    assert projection.get("lechuga", "lechuga") is True
    assert projection.project_subjects(["lechuga"]) == ["lechuga"]
    assert listed[-1] == {"source": "wigame:implies", "target": "wigame:prop", "pairs": [["lechuga", "lechuga"]]}


def test_projection_candidate_promotes_into_a_matrix():
    system, runtime = build_worlds()
    candidate = runtime.evaluate(
        "(candidate projection wigame:implies (wigame:prop (lechuga lechuga)) "
        "evidence:{'stats':{'phi':0.99}})"
    ).payload

    promoted = runtime.evaluate(f"(promote {candidate['candidate_id']})")
    listed = runtime.evaluate("(return projections wigame:implies)").payload["projections"]

    assert promoted.status == "accept"
    assert promoted.payload["linked"] == 1
    assert listed[-1]["pairs"] == [["lechuga", "lechuga"]]
    assert system.projections["wigame:implies->wigame:prop"].get("lechuga", "lechuga") is True


def test_cross_world_facts_keep_their_own_truth_matrix():
    system, runtime = build_worlds()
    runtime.evaluate("(assert wigame:implies (implies lechuga hoja))")
    runtime.evaluate("(define (if (implies lechuga hoja) (has_property lechuga verde)))")

    assert system.wigames["wigame:prop"].Vi.get("lechuga", "verde") == TruthValue.TRUE.value
    assert system.wigames["wigame:implies"].Vi.get("lechuga", "verde") == TruthValue.UNKNOWN.value
