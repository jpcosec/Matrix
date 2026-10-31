"""Tests for reifying relations and contexts as first-class symbols."""

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
from src.operational_model.system.reflection import (
    context_symbol_id,
    dereference,
    describes,
    is_context_symbol,
    is_relation_symbol,
    reify_all_contexts,
    reify_all_relations,
    reify_context,
    reify_relation,
    relation_of_symbol,
    relation_symbol_id,
)


def build_chase_system() -> LogicalSystem:
    """Builds `(persigue pedrito maria)` plus an empty meta world."""

    system = LogicalSystem()
    system.register_relation(Relation("persigue", "perseguir"))
    system.register_relation(Relation("es", "es"))
    for symbol_id in ("pedrito", "maria", "verbo"):
        system.register_thing(Thing(Symbol(symbol_id), Name(symbol_id)))
    chase = WiGame(
        wigame_id="w:pers",
        li=LiSpace("li:pers", ["pedrito"], ["maria"], "persigue"),
        context_id="context:patio",
    )
    system.register_wigame(chase)
    chase.add_fact(
        Fact(
            proposition=Proposition("persigue", "pedrito", "maria", "w:pers"),
            truth=TruthValue.TRUE,
        )
    )
    return system


def test_the_two_registries_start_disjoint() -> None:
    system = build_chase_system()

    # the exact gap this module closes
    assert "persigue" in system.relations
    assert "persigue" not in system.things


def test_reifying_a_relation_creates_a_usable_symbol() -> None:
    system = build_chase_system()

    reification = reify_relation(system, "persigue")

    assert reification.symbol_id == "rel:persigue"
    assert reification.kind == "relation"
    assert "rel:persigue" in system.things
    # the relation still works as a relation
    assert "persigue" in system.relations


def test_the_meta_proposition_now_holds() -> None:
    system = build_chase_system()
    reify_relation(system, "persigue")

    meta = WiGame(
        wigame_id="w:meta",
        li=LiSpace("li:meta", ["rel:persigue"], ["verbo"], "es"),
        context_id="context:gramatica",
    )
    system.register_wigame(meta)
    proposition = Proposition("es", "rel:persigue", "verbo", "w:meta")

    assert meta.accepts(proposition)
    meta.add_fact(Fact(proposition=proposition, truth=TruthValue.TRUE))
    assert meta.Vi.get("rel:persigue", "verbo") == TruthValue.TRUE.value


def test_symbol_dereferences_back_to_the_relation() -> None:
    system = build_chase_system()
    reify_relation(system, "persigue")

    relation = relation_of_symbol(system, "rel:persigue")

    assert relation is not None
    assert relation.relation_id == "persigue"
    assert dereference("rel:persigue") == "persigue"
    assert describes(system, "rel:persigue") == "persigue"


def test_reifying_an_unknown_relation_fails() -> None:
    system = build_chase_system()

    with pytest.raises(KeyError, match="nope"):
        reify_relation(system, "nope")


def test_contexts_become_symbols_too() -> None:
    system = build_chase_system()

    reification = reify_context(system, "context:patio")

    assert reification.symbol_id == "ctx:context:patio"
    assert "ctx:context:patio" in system.things
    assert describes(system, "ctx:context:patio") == "context:patio"


def test_context_word_case_is_expressible() -> None:
    """`(es pedrito pulento)` + `(contexto_palabra pulento chileno)`."""

    system = LogicalSystem()
    system.register_relation(Relation("es", "es"))
    system.register_relation(Relation("contexto_palabra", "contexto de la palabra"))
    for symbol_id in ("pedrito", "pulento", "chileno"):
        system.register_thing(Thing(Symbol(symbol_id), Name(symbol_id)))
    reify_context(system, "habla:informal")

    meta = WiGame(
        wigame_id="w:palabra",
        li=LiSpace("li:palabra", ["pulento"], ["chileno"], "contexto_palabra"),
    )
    system.register_wigame(meta)
    proposition = Proposition("contexto_palabra", "pulento", "chileno", "w:palabra")

    assert meta.accepts(proposition)
    assert "ctx:habla:informal" in system.things


def test_namespace_predicates() -> None:
    assert is_relation_symbol("rel:persigue")
    assert not is_relation_symbol("rel:")
    assert is_context_symbol("ctx:patio")
    assert not is_context_symbol("pedrito")
    assert relation_symbol_id("rel:persigue") == "rel:persigue"
    assert context_symbol_id("ctx:patio") == "ctx:patio"


def test_dereference_rejects_a_plain_symbol() -> None:
    with pytest.raises(ValueError, match="does not mirror"):
        dereference("pedrito")


def test_bulk_reification_is_sorted_and_idempotent() -> None:
    system = build_chase_system()

    first = reify_all_relations(system)
    second = reify_all_relations(system)

    assert [r.source_id for r in first] == ["es", "persigue"]
    assert first == second
    contexts = reify_all_contexts(system)
    assert [c.source_id for c in contexts] == ["context:patio"]


def test_describes_returns_none_for_an_unbacked_mirror() -> None:
    system = build_chase_system()

    assert describes(system, "rel:inexistente") is None
    assert describes(system, "pedrito") is None
