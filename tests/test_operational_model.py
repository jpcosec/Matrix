import pytest
from src.operational_model import (
    Context,
    Fact,
    LiSpace,
    LogicalSystem,
    Name,
    Proposition,
    Relation,
    RouteTargetKind,
    RoutingProjection,
    SearchVector,
    SenseValue,
    Symbol,
    Thing,
    TruthValue,
    WiGame,
)


def build_system() -> LogicalSystem:
    system = LogicalSystem()

    for thing in (
        Thing(Symbol("dog"), Name("perro")),
        Thing(Symbol("wolf"), Name("lobo")),
        Thing(Symbol("fur"), Name("peludo")),
        Thing(Symbol("canine_kind"), Name("canino")),
        Thing(Symbol("domestic"), Name("domestico")),
        Thing(Symbol("wild"), Name("salvaje")),
    ):
        system.register_thing(thing)

    system.register_relation(Relation("es", "es"))

    animals = WiGame(
        wigame_id="wigame:animales",
        context_id="ctx:animales",
        li=LiSpace(
            li_id="li:animales",
            axis_a=["dog", "wolf"],
            axis_b=["fur", "canine_kind"],
            relation_id="es",
        ),
    )
    canines = WiGame(
        wigame_id="wigame:caninos",
        context_id="ctx:caninos",
        li=LiSpace(
            li_id="li:caninos",
            axis_a=["dog", "wolf"],
            axis_b=["domestic", "wild"],
            relation_id="es",
        ),
    )
    system.register_wigame(animals)
    system.register_wigame(canines)

    projection = RoutingProjection.empty(
        source_wigame_id=animals.wigame_id,
        source_axis=animals.axis_a,
        target_wigame_id=canines.wigame_id,
        target_axis=canines.axis_a,
        relation_id="proyeccion_animales_caninos",
    )
    projection.link("dog", "dog")
    projection.link("wolf", "wolf")
    system.register_projection(projection)

    root = Context("ctx:root")
    root.route_to_context("ctx:animales")
    root.route_to_context("ctx:caninos")
    root.route_to_wigame(animals.wigame_id)
    root.route_to_wigame(canines.wigame_id)
    system.register_context(root)

    for fact in (
        Fact(Proposition("es", "dog", "fur", animals.wigame_id), TruthValue.TRUE),
        Fact(Proposition("es", "wolf", "fur", animals.wigame_id), TruthValue.TRUE),
        Fact(
            Proposition("es", "dog", "canine_kind", animals.wigame_id), TruthValue.TRUE
        ),
        Fact(
            Proposition("es", "wolf", "canine_kind", animals.wigame_id), TruthValue.TRUE
        ),
        Fact(Proposition("es", "dog", "domestic", canines.wigame_id), TruthValue.TRUE),
        Fact(Proposition("es", "wolf", "wild", canines.wigame_id), TruthValue.TRUE),
    ):
        system.add_fact(fact)

    return system


def test_wigame_serializes_direct_matrices() -> None:
    system = build_system()
    wigame = system.wigames["wigame:animales"]

    payload = wigame.to_dict()
    restored = WiGame.from_dict(payload)

    assert payload["axis_a"] == ["dog", "wolf"]
    assert payload["axis_b"] == ["fur", "canine_kind"]
    assert payload["relation"] == "es"
    assert payload["Vi"]["values"] == ["11", "11"]
    assert restored.Vi.get("dog", "fur") == "true"
    assert restored.Si.get("wolf", "canine_kind") == "sinnvoll"


def test_vi_and_si_are_specialized_matrices() -> None:
    system = build_system()
    wigame = system.wigames["wigame:animales"]

    assert wigame.Vi.get("dog", "fur") == TruthValue.TRUE.value
    assert wigame.Si.get("dog", "fur") == SenseValue.SINNVOLL.value
    assert wigame.is_pure() is True
    assert wigame.tautological_columns() == ["fur", "canine_kind"]


def test_search_vector_filters_inside_wigame() -> None:
    system = build_system()
    wigame = system.wigames["wigame:animales"]

    search_vector = SearchVector(wigame_id=wigame.wigame_id, terms=["canine_kind"])

    assert wigame.search(search_vector) == ["dog", "wolf"]
    assert system.search(wigame.wigame_id, ["fur", "canine_kind"]) == ["dog", "wolf"]


def test_routing_projection_crosses_between_wigames() -> None:
    system = build_system()
    projection_id = next(iter(system.projections.keys()))

    result = system.cross_search(
        source_wigame_id="wigame:animales",
        source_terms=["canine_kind"],
        projection_id=projection_id,
        target_terms=["domestic"],
    )

    assert result.source_hits == ["dog", "wolf"]
    assert result.projected_hits == ["dog", "wolf"]
    assert result.target_hits == ["dog"]
    assert result.cross_hits == ["dog"]


def test_context_can_route_to_contexts_and_wigames() -> None:
    system = build_system()
    root = system.contexts["ctx:root"]

    assert [route.target_kind for route in root.routes] == [
        RouteTargetKind.CONTEXT,
        RouteTargetKind.CONTEXT,
        RouteTargetKind.WIGAME,
        RouteTargetKind.WIGAME,
    ]


def test_symbol_support_is_differential_and_accumulative() -> None:
    system = build_system()

    assert len(system.symbols["dog"].supporting_fact_ids) == 3
    assert "wigame:animales" in system.symbols["dog"].supporting_wigame_ids
    assert "wigame:caninos" in system.symbols["dog"].supporting_wigame_ids


def test_search_with_unknown_terms_raises_keyerror() -> None:
    system = build_system()
    with pytest.raises(KeyError):
        system.search("wigame:animales", ["non-existent-term"])


def test_route_search_with_empty_path_returns_local_hits() -> None:
    system = build_system()
    result = system.route_search("wigame:animales", ["canine_kind"], [])
    assert result.source_hits == ["dog", "wolf"]
    assert result.projected_hits == ["dog", "wolf"]
