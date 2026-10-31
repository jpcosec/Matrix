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
    # `taut_df=1.0`: the synthetic corpus repeats its core facts in every
    # context on purpose, so they are the identity signal there.
    convergence = symbol_convergence(system, contexts, declarations, taut_df=1.0)
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


def _unidirectional_world():
    from src.operational_model import LogicalSystem, SExpressionRuntime

    system = LogicalSystem()
    runtime = SExpressionRuntime(system)
    runtime.evaluate("(create relation mentions mentions)")
    for context, symbol, objects in (
        ("A", "alpha", [f"obj{index}" for index in range(1, 7)]),
        ("B", "beta", [f"obj{index}" for index in range(1, 10)]),
        ("C", "gamma", [f"unique{index}" for index in range(1, 11)]),
    ):
        for name in [symbol] + objects:
            runtime.evaluate(f"(create symbol {name}@{context} {name})")
        axes = " ".join(f"{name}@{context}" for name in objects)
        runtime.evaluate(
            f"(create li li:{context}:mentions mentions (axis-a {symbol}@{context}) (axis-b {axes}))"
        )
        runtime.evaluate(f"(create wigame wigame:{context}:mentions li:{context}:mentions)")
        for obj in objects:
            runtime.evaluate(
                f"(assert wigame:{context}:mentions (mentions {symbol}@{context} {obj}@{context}))"
            )
    return system, runtime


def test_unidirectional_projection_is_promoted_and_followed():
    from pipeline.convergence import symbol_convergence
    from pipeline.decompose import Declaration
    from pipeline.query import ask

    system, _ = _unidirectional_world()
    declarations = [
        Declaration(ctx_id=ctx, relation="mentions", a=f"{symbol}@{ctx}", b=f"obj{index}@{ctx}",
                    a_sign=symbol, b_sign=f"obj{index}", sentence_index=0, span=(0, 1))
        for ctx, symbol, count in (("A", "alpha", 6), ("B", "beta", 9))
        for index in range(1, count + 1)
    ]
    declarations += [
        Declaration(ctx_id="C", relation="mentions", a="gamma@C", b=f"unique{index}@C",
                    a_sign="gamma", b_sign=f"unique{index}", sentence_index=0, span=(0, 1))
        for index in range(1, 11)
    ]

    # `min_contexts=1`: each configuration is declared in a single context here.
    convergence = symbol_convergence(system, [], declarations, min_contexts=1, taut_df=1.0)

    promoted = {(entry["source"], entry["target"]) for entry in convergence.promoted}
    assert ("alpha@A", "beta@B") in promoted
    assert ("beta@B", "alpha@A") not in promoted

    forward = ask(system, "mentions", "alpha@A", None)
    backward = ask(system, "mentions", "beta@B", None)

    assert len(forward.path) >= 2
    assert any(obj.startswith("obj7") for obj, _, _, _ in forward.objects)
    assert backward.path == ["wigame:B:mentions"]
