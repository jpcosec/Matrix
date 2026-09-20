"""Tests for routed queries over the converged synthetic corpus."""

from __future__ import annotations

import pytest

from pipeline.convergence import symbol_convergence
from pipeline.decompose import decompose
from pipeline.ingest import ingest_contexts
from pipeline.query import ask, referent_of
from populator import build_contexts
from populator.tokenize import normalize
from src.operational_model import LogicalSystem, SExpressionRuntime
from tests.fixtures.curie_franklin import generate, planted_declarations


@pytest.fixture(scope="module")
def converged():
    documents = generate(0)
    contexts = build_contexts(documents, lang="en")
    declarations = [d for c in contexts for d in decompose(c, lang="en")]
    declarations += planted_declarations(0)
    system = LogicalSystem()
    runtime = SExpressionRuntime(system)
    ingest_contexts(system, runtime, contexts, declarations)
    convergence = symbol_convergence(system, contexts, declarations)
    return system, runtime, convergence


def test_ask_follows_projections_to_another_context(converged):
    system, _, _ = converged

    answer = ask(system, "born_in", "she@curie_3", "warsaw")

    assert answer.truth_for("warsaw") == "true"
    assert len(answer.path) >= 2
    foreign = [obj for obj in answer.objects if obj[0].startswith("warsaw") and obj[1] != "curie_3"]
    assert foreign


def test_ask_returns_no_foreign_fact_for_the_other_person(converged):
    system, _, _ = converged

    answer = ask(system, "born_in", "she@franklin_2", "warsaw")

    assert answer.truth_for("warsaw") in {"\u2205", "false"}
    assert not [obj for obj in answer.objects if obj[0].startswith("warsaw")]


def test_why_of_a_reached_fact_returns_foreign_provenance(converged):
    system, runtime, _ = converged
    answer = ask(system, "born_in", "she@curie_3", "warsaw")
    foreign = next(obj for obj in answer.objects if obj[0].startswith("warsaw") and obj[1] != "curie_3")
    context = foreign[1]
    world = system.wigames[f"wigame:{context}:born_in"]
    fact = next(
        fact
        for fact in world.facts.values()
        if fact.proposition.object_symbol_id == foreign[0]
    )

    chain = runtime.evaluate(
        f"(why wigame:{context}:born_in {fact.proposition.sexpr()})"
    ).payload["chain"]

    assert chain[0]["prov"]
    assert chain[0]["prov"][0]["document_id"] == f"{context}.md"
    assert fact.evidence["tier"] in {"observed", "confirmed"}


def test_referent_of_links_the_three_surface_forms(converged):
    system, _, convergence = converged

    reference = referent_of(system, "she@curie_3")
    group = {symbol for symbol, referent in convergence.referents.items() if referent == reference}

    assert reference is not None
    assert any(symbol.startswith("marie_curie@") for symbol in group)
    assert any(symbol.startswith("curie@curie") for symbol in group)


def test_ask_without_object_lists_the_true_objects(converged):
    system, _, _ = converged

    answer = ask(system, "born_in", "she@curie_3")

    assert answer.objects
    assert answer.truth_for(None) == "true"
    assert any(normalize(obj[0].split("@")[0]) == "warsaw" for obj in answer.objects)
