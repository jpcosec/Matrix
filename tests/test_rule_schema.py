"""Tests for quantified rule schemas and their grounding."""

from __future__ import annotations

import pytest

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
from src.operational_model.kernel.rule_schema import (
    RuleSchema,
    expand_for_system,
    is_variable,
    parse_schema,
    substitute,
    system_universe,
    variables_of,
)
from src.operational_model.system.deduction import deduce


def test_variable_recognition() -> None:
    assert is_variable("?x")
    assert not is_variable("?")
    assert not is_variable("x")
    assert not is_variable("kern:true")


def test_schema_reports_its_variables_in_first_seen_order() -> None:
    schema = parse_schema("(if (parte ?planta ?organo) (grosor ?organo gruesa))")

    assert schema.variables == ("?planta", "?organo")
    assert not schema.is_ground


def test_ground_rule_expands_to_itself() -> None:
    schema = parse_schema("(if (es lechuga verdura) (es lechuga comestible))")

    assert schema.is_ground
    assert schema.variables == ()
    assert [f.to_sexpr() for f in schema.expand(["lechuga"])] == [
        "(if (es lechuga verdura) (es lechuga comestible))"
    ]


def test_one_variable_expands_over_the_universe() -> None:
    schema = parse_schema("(if (es ?x verdura) (es ?x comestible))")

    grounded = [f.to_sexpr() for f in schema.expand(["lechuga", "acelga"])]

    assert grounded == [
        "(if (es lechuga verdura) (es lechuga comestible))",
        "(if (es acelga verdura) (es acelga comestible))",
    ]


def test_expansion_is_deterministic_and_deduplicated() -> None:
    schema = parse_schema("(if (es ?x verdura) (es ?x comestible))")

    first = [f.to_sexpr() for f in schema.expand(["lechuga", "lechuga", "acelga"])]
    second = [f.to_sexpr() for f in schema.expand(["lechuga", "acelga"])]

    assert first == second


def test_two_variables_expand_over_the_product() -> None:
    schema = parse_schema("(if (precede ?a ?b) (antes ?a ?b))")

    grounded = schema.expand(["x", "y"])

    assert len(grounded) == 4
    assert grounded[0].to_sexpr() == "(if (precede x x) (antes x x))"


def test_empty_universe_expands_to_nothing() -> None:
    schema = parse_schema("(if (es ?x verdura) (es ?x comestible))")

    assert schema.expand([]) == []


def test_bind_requires_every_variable() -> None:
    schema = parse_schema("(if (parte ?planta ?organo) (grosor ?organo gruesa))")

    bound = schema.bind({"?planta": "lechuga", "?organo": "hoja"})
    assert bound.to_sexpr() == "(if (parte lechuga hoja) (grosor hoja gruesa))"

    with pytest.raises(ValueError, match=r"\?organo"):
        schema.bind({"?planta": "lechuga"})


def test_conjunctive_antecedent_keeps_its_variables() -> None:
    schema = parse_schema(
        "(if (and (es ?x verdura) (es ?x fresca)) (es ?x comestible))"
    )

    assert schema.variables == ("?x",)
    grounded = schema.expand(["lechuga"])
    assert grounded[0].to_sexpr() == (
        "(if (and (es lechuga verdura) (es lechuga fresca)) (es lechuga comestible))"
    )


def test_a_bare_variable_is_not_a_formula() -> None:
    with pytest.raises(ValueError, match="bare variable"):
        parse_schema("?x")


def test_variables_of_ignores_kernel_atoms() -> None:
    schema = parse_schema("(if kern:true (es ?x comestible))")

    assert variables_of(schema.formula) == ("?x",)


def test_substitute_leaves_unbound_variables_alone() -> None:
    schema = parse_schema("(if (precede ?a ?b) (antes ?a ?b))")

    partial = substitute(schema.formula, {"?a": "picar"})

    assert partial.to_sexpr() == "(if (precede picar ?b) (antes picar ?b))"
    assert variables_of(partial) == ("?b",)


def _vegetable_system() -> LogicalSystem:
    """Builds a world of vegetables with no `x` symbol registered."""

    system = LogicalSystem()
    system.register_relation(Relation("es", "es"))
    subjects = ["lechuga", "acelga"]
    objects = ["verdura", "comestible"]
    for symbol_id in subjects + objects:
        system.register_thing(Thing(Symbol(symbol_id), Name(symbol_id)))
    wigame = WiGame(
        wigame_id="w:es",
        li=LiSpace("li:es", subjects, objects, "es"),
    )
    system.register_wigame(wigame)
    for subject in subjects:
        wigame.add_fact(
            Fact(
                proposition=Proposition("es", subject, "verdura", "w:es"),
                truth=TruthValue.TRUE,
            )
        )
    return system


def test_universe_comes_from_the_worlds() -> None:
    system = _vegetable_system()

    assert system_universe(system) == [
        "acelga",
        "comestible",
        "lechuga",
        "verdura",
    ]


def test_one_schema_replaces_one_rule_per_symbol() -> None:
    system = _vegetable_system()
    schema = parse_schema("(if (es ?x verdura) (es ?x comestible))")

    system.rules.extend(expand_for_system(schema, system))
    derived = deduce(system)

    sexprs = sorted(fact.proposition.sexpr() for fact in derived)
    assert "(es lechuga comestible)" in sexprs
    assert "(es acelga comestible)" in sexprs
    # no `x` symbol was ever registered: the schema did the quantifying
    assert "x" not in system.things
    for fact in derived:
        assert fact.evidence["tier"] == "inferred"


def test_schema_is_hashable_and_comparable() -> None:
    a = parse_schema("(if (es ?x verdura) (es ?x comestible))")
    b = parse_schema("(if (es ?x verdura) (es ?x comestible))")

    assert a == b
    assert isinstance(a, RuleSchema)
    assert len({a, b}) == 1
