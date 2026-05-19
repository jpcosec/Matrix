from src.operational_model import (
    LiSpace,
    LogicalSystem,
    Name,
    Relation,
    SExpressionRuntime,
    Symbol,
    Thing,
    TruthValue,
    WiGame,
    parse_s_expression,
)

from tests.test_operational_model import build_system


def build_ambiguous_system() -> LogicalSystem:
    system = LogicalSystem()
    for thing in (
        Thing(Symbol("dog"), Name("perro")),
        Thing(Symbol("kind"), Name("clase")),
    ):
        system.register_thing(thing)
    system.register_relation(Relation("es", "es"))
    for wigame_id in ("wigame:a", "wigame:b"):
        system.register_wigame(
            WiGame(
                wigame_id=wigame_id,
                li=LiSpace(
                    li_id=f"li:{wigame_id}",
                    axis_a=["dog"],
                    axis_b=["kind"],
                    relation_id="es",
                ),
            )
        )
    return system


def test_parse_s_expression_builds_nested_lists() -> None:
    assert parse_s_expression("(assert (es dog fur))") == [
        "assert",
        ["es", "dog", "fur"],
    ]


def test_assert_returns_ambiguous_when_multiple_wigames_fit() -> None:
    runtime = SExpressionRuntime(build_ambiguous_system())

    result = runtime.evaluate("(assert (es dog kind))")

    assert result.status == "ambiguous"
    assert result.payload == {
        "candidates": ["wigame:a", "wigame:b"],
        "proposition": "(es dog kind)",
    }


def test_targeted_assert_adds_fact_to_one_wigame() -> None:
    system = build_system()
    runtime = SExpressionRuntime(system)

    result = runtime.evaluate("(assert wigame:animales (es dog canine_kind))")

    assert result.status == "accept"
    assert result.payload == {
        "wigame_id": "wigame:animales",
        "proposition": "(es dog canine_kind)",
        "action": "noop",
    }

    added = runtime.evaluate("(assert wigame:caninos (es dog wild))")
    assert added.status == "accept"
    assert added.payload == {
        "wigame_id": "wigame:caninos",
        "proposition": "(es dog wild)",
        "action": "added",
    }
    assert system.wigames["wigame:caninos"].Vi.get("dog", "wild") == TruthValue.TRUE.value


def test_check_rejects_proposition_with_no_candidate_wigame() -> None:
    runtime = SExpressionRuntime(build_system())

    result = runtime.evaluate("(check (es dog missing))")

    assert result.status == "reject"
    assert result.reason == "no WiGame accepts this proposition"


def test_return_facts_groups_results_by_wigame_and_matches_names() -> None:
    system = build_system()
    runtime = SExpressionRuntime(system)

    result = runtime.evaluate("(return facts symbol:perro)")

    assert result.status == "accept"
    groups = {group["wigame_id"]: group["facts"] for group in result.payload["groups"]}
    assert set(groups) == {"wigame:animales", "wigame:caninos"}
    assert [fact["proposition"] for fact in groups["wigame:animales"]] == [
        "(es dog canine_kind)",
        "(es dog fur)",
    ]
    assert [fact["proposition"] for fact in groups["wigame:caninos"]] == [
        "(es dog domestic)",
    ]
    assert all(fact["truth"] == TruthValue.TRUE.value for facts in groups.values() for fact in facts)
    assert all(fact["sinn"] == "sinnvoll" for facts in groups.values() for fact in facts)
