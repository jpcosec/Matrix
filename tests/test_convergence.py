"""Tests for context taxonomy, symbol convergence and WiGame maintenance."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import pytest

from pipeline.convergence import context_taxonomy, maintain_wigame, symbol_convergence
from pipeline.decompose import decompose
from pipeline.ingest import build_world, ingest_contexts
from populator import build_contexts
from src.operational_model import LogicalSystem, SExpressionRuntime
from tests.fixtures.curie_franklin import generate, planted_declarations

CORPUS = Path(__file__).resolve().parents[1] / "corpus" / "vegetales"


@pytest.fixture(scope="module")
def synthetic():
    documents = generate(0)
    contexts = build_contexts(documents, lang="en")
    declarations = [d for c in contexts for d in decompose(c, lang="en")]
    declarations += planted_declarations(0)
    system = LogicalSystem()
    runtime = SExpressionRuntime(system)
    ingest_contexts(system, runtime, contexts, declarations)
    taxonomy = context_taxonomy(system, contexts, declarations)
    convergence = symbol_convergence(system, contexts, declarations)
    return system, contexts, declarations, taxonomy, convergence


def _groups(convergence):
    groups: dict[str, set[str]] = defaultdict(set)
    for symbol, referent in convergence.referents.items():
        groups[referent].add(symbol)
    return groups


def test_taxonomy_has_several_pure_nodes(synthetic):
    _, _, _, taxonomy, _ = synthetic

    assert len(taxonomy.nodes) >= 2
    for node, members in taxonomy.membership.items():
        assert members
        curie = sum(1 for member in members if member.startswith("curie_"))
        franklin = len(members) - curie
        assert min(curie, franklin) / len(members) <= 0.2, node


def test_curie_and_franklin_membership_is_different(synthetic):
    _, _, _, taxonomy, _ = synthetic

    for node, members in taxonomy.membership.items():
        curie = [member for member in members if member.startswith("curie_")]
        franklin = [member for member in members if member.startswith("franklin_")]
        assert not (curie and franklin), node
    curie_nodes = {taxonomy.context_nodes.get(f"curie_{index}") for index in range(15)}
    franklin_nodes = {taxonomy.context_nodes.get(f"franklin_{index}") for index in range(15)}
    assert curie_nodes and franklin_nodes
    assert not (curie_nodes & franklin_nodes)


def test_she_converges_with_curie_names(synthetic):
    _, _, _, _, convergence = synthetic
    groups = _groups(convergence)

    she_symbols = [symbol for symbol in convergence.scores if symbol.startswith("she@curie_")]
    converged = [symbol for symbol in she_symbols if symbol in convergence.referents]
    with_name = [
        symbol
        for symbol in converged
        if any(member.startswith(("marie_curie@", "curie@")) for member in groups[convergence.referents[symbol]])
    ]

    assert she_symbols
    assert len(with_name) / len(she_symbols) >= 0.8


def test_franklin_converges_with_itself_and_not_with_curie(synthetic):
    _, _, _, _, convergence = synthetic
    groups = _groups(convergence)

    franklin_symbols = [symbol for symbol in convergence.scores if symbol.startswith("franklin@")]
    franklin_converged = [symbol for symbol in franklin_symbols if symbol in convergence.referents]
    assert len(franklin_converged) / len(franklin_symbols) >= 0.8

    curie_names = ("marie_curie@", "curie@", "she@curie")
    for symbol, referent in convergence.referents.items():
        if not symbol.startswith("she@franklin"):
            continue
        assert not any(member.startswith(curie_names) for member in groups[referent])


def test_planted_garbage_stays_isolated(synthetic):
    _, _, _, _, convergence = synthetic
    planted = {declaration.b for declaration in planted_declarations(0)}

    assert len(planted) == 10
    garbage = 0
    for symbol in planted:
        projected = any(
            symbol in (entry.get("source"), entry.get("target"))
            for entry in convergence.proposed + convergence.promoted
        )
        assert symbol not in convergence.referents
        assert not projected
        if convergence.scores.get(symbol, 0.0) < 0.5:
            garbage += 1
    assert garbage >= 8


def test_convergence_is_idempotent(synthetic):
    system, contexts, declarations, _, _ = synthetic

    second = symbol_convergence(system, contexts, declarations)

    assert second.promoted == []


def _mini_world(include_leaves: bool = True):
    system = LogicalSystem()
    runtime = SExpressionRuntime(system)
    runtime.evaluate("(create relation has_property has_property)")
    for symbol in ("lechuga", "espinaca", "apio", "verde", "hoja_lisa", "hoja_rugosa"):
        runtime.evaluate(f"(create symbol {symbol} {symbol})")
    runtime.evaluate(
        "(create li li:v has_property (axis-a lechuga espinaca apio) (axis-b verde hoja_lisa hoja_rugosa))"
    )
    runtime.evaluate("(create wigame wigame:v li:v)")
    for subject in ("lechuga", "espinaca", "apio"):
        runtime.evaluate(f"(assert wigame:v (has_property {subject} verde))")
    if include_leaves:
        runtime.evaluate("(assert wigame:v (has_property lechuga hoja_lisa))")
        runtime.evaluate("(assert wigame:v (has_property espinaca hoja_rugosa))")
    return system, runtime


def test_vegetales_gate_on_verde():
    system, _, _, _, _ = build_world(CORPUS, lang="es")

    gates = {
        gate["gate"].split("@")[0]
        for wigame_id in sorted(system.wigames)
        if wigame_id.endswith(":has_property")
        for gate in maintain_wigame(system, wigame_id).gates
    }

    assert gates & {"verde", "verdura"}


def test_collision_discriminant_is_a_leaf():
    system, _ = _mini_world(include_leaves=True)

    maintenance = maintain_wigame(system, "wigame:v")
    gates = {gate["gate"] for gate in maintenance.gates}

    assert "verde" in gates
    assert ("lechuga", "espinaca") in maintenance.collisions
    discriminant = maintenance.discriminants[("lechuga", "espinaca")]
    assert discriminant in {"hoja_lisa", "hoja_rugosa"}


def test_collision_without_leaf_features_is_unresolved():
    system, _ = _mini_world(include_leaves=False)

    maintenance = maintain_wigame(system, "wigame:v")

    assert ("lechuga", "espinaca") in maintenance.collisions
    assert ("lechuga", "espinaca") in maintenance.unresolved
    assert maintenance.discriminants[("lechuga", "espinaca")] is None
