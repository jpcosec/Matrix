"""Tests for shape diagnosis of degenerate WiGames."""

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
from src.operational_model.system.shape_guard import (
    SEVERITY_ERROR,
    diagnose_shape,
    is_well_shaped,
)


def _build(system, wigame_id, relation_id, axis_a, axis_b, pairs):
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


def build_universal() -> tuple[LogicalSystem, WiGame]:
    """Builds the widest, degenerate world: `(* pedrito es_hermano_de_maria)`."""

    system = LogicalSystem()
    people = ["pedrito", "maria", "juan"]
    objects = [
        "es_hermano_de_maria",
        "es_hermano_de_juan",
        "es_alto",
        "es_hermano_de_maria_y_alto",
    ]
    wigame = _build(
        system,
        "w:*",
        "*",
        people,
        objects,
        [("pedrito", "es_hermano_de_maria")],
    )
    return system, wigame


def build_factored() -> tuple[LogicalSystem, WiGame]:
    """Builds the well shaped counterpart: `(es_hermano_de pedrito maria)`."""

    system = LogicalSystem()
    people = ["pedrito", "maria", "juan"]
    wigame = _build(
        system,
        "w:herm",
        "es_hermano_de",
        people,
        people,
        [("pedrito", "maria"), ("maria", "pedrito"), ("juan", "maria")],
    )
    return system, wigame


def test_universal_relation_is_rejected() -> None:
    system, wigame = build_universal()

    findings = diagnose_shape(wigame, system)
    kinds = {finding.kind for finding in findings}

    assert "wildcard_relation" in kinds
    assert "packed_object" in kinds
    assert not is_well_shaped(wigame, system)


def test_packed_object_names_the_trapped_symbol() -> None:
    system, wigame = build_universal()

    packed = [f for f in diagnose_shape(wigame, system) if f.kind == "packed_object"]
    trapped = {f.subject: f.details["embedded"] for f in packed}

    assert "maria" in trapped["es_hermano_de_maria"]
    assert all(f.severity == SEVERITY_ERROR for f in packed)


def test_conjunctive_object_is_flagged() -> None:
    system, wigame = build_universal()

    conjunctive = [
        f for f in diagnose_shape(wigame, system) if f.kind == "conjunctive_object"
    ]

    assert [f.subject for f in conjunctive] == ["es_hermano_de_maria_y_alto"]


def test_factored_world_passes_clean() -> None:
    system, wigame = build_factored()

    findings = diagnose_shape(wigame, system)
    errors = [f for f in findings if f.severity == SEVERITY_ERROR]

    assert errors == []
    assert is_well_shaped(wigame, system)


def test_tautological_column_is_reported() -> None:
    system = LogicalSystem()
    plants = ["lechuga", "acelga", "espinaca"]
    wigame = _build(
        system,
        "w:parte",
        "tiene_parte",
        plants,
        ["hoja"],
        [(p, "hoja") for p in plants],
    )

    kinds = {f.kind for f in diagnose_shape(wigame, system)}

    assert "non_discriminative_column" in kinds
    # A column everyone shares is a warning, not a malformed world.
    assert is_well_shaped(wigame, system)


def test_sparse_world_is_reported() -> None:
    system, wigame = build_universal()

    sparse = [f for f in diagnose_shape(wigame, system) if f.kind == "sparse_world"]

    assert len(sparse) == 1
    assert sparse[0].details["facts"] == 1
    assert sparse[0].details["cells"] == 12


def test_diagnosis_without_system_skips_packed_objects() -> None:
    _system, wigame = build_universal()

    kinds = {f.kind for f in diagnose_shape(wigame)}

    assert "packed_object" not in kinds
    assert "wildcard_relation" in kinds
