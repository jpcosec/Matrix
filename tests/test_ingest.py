"""Tests for per-context ingestion into WiGames."""

from __future__ import annotations

from pathlib import Path

import pytest

from pipeline.ingest import build_world, ingest_contexts

CORPUS = Path(__file__).resolve().parents[1] / "corpus" / "vegetales"
PHYSICISTS = Path(__file__).resolve().parents[1] / "corpus" / "physicists" / "articles"
UNKNOWN = "\u2205"


@pytest.fixture(scope="module")
def vegetales():
    return build_world(CORPUS, lang="es", limit=3)


def test_contexts_symbols_and_wigames_exist(vegetales):
    system, _, contexts, declarations, report = vegetales

    assert report.contexts == len(contexts) == 3
    assert report.symbols > 0
    assert report.wigames > 0
    assert report.asserted == len(declarations)
    assert report.rejected == []
    assert "01_lechugas" in system.contexts
    assert "wigame:01_lechugas:has_property" in system.wigames


def test_has_property_fact_with_provenance(vegetales):
    system, runtime, _, _, _ = vegetales
    sexpr = "(has_property lechuga@01_lechugas hoja_lisa@01_lechugas)"

    checked = runtime.evaluate(f"(check wigame:01_lechugas:has_property {sexpr})")
    fact = next(
        fact
        for fact in system.wigames["wigame:01_lechugas:has_property"].facts.values()
        if fact.proposition.sexpr() == sexpr
    )
    prov = fact.evidence["prov"][0]
    document = Path(prov["document_id"]).read_text(encoding="utf-8")
    start, end = prov["span"]

    assert checked.payload["truth"] == "true"
    assert fact.evidence["tier"] == "observed"
    assert fact.evidence["curation"] == "confirmed"
    assert 0 <= start < end <= len(document)
    assert "lechuga" in document[start:end]
    assert prov["extractor"] == "decompose/heuristic"


def test_wigames_are_closed_contexts(vegetales):
    system, _, _, declarations, _ = vegetales

    for (ctx_id, relation) in {(declaration.ctx_id, declaration.relation) for declaration in declarations}:
        wigame = system.wigames[f"wigame:{ctx_id}:{relation}"]
        assert wigame.context_id == ctx_id
        assert wigame.relation_id == relation


def test_part_of_is_transitive_and_spouse_is_commutative(vegetales):
    system, _, _, _, _ = vegetales

    assert system.relations["part_of"].semantics.supports_transitive_closure()


def test_planted_contradiction_is_rejected(vegetales):
    system, runtime, contexts, declarations, _ = vegetales
    declaration = next(item for item in declarations if item.relation == "has_property")
    sexpr = f"({declaration.relation} {declaration.a} {declaration.b})"
    wigame_id = f"wigame:{declaration.ctx_id}:{declaration.relation}"

    runtime.evaluate(f"(retract {wigame_id} {sexpr})")
    runtime.evaluate(f"(check {wigame_id} {sexpr})")
    second = ingest_contexts(system, runtime, contexts, [declaration])

    assert [item[0] for item in second.rejected] == [sexpr]
    assert runtime.evaluate(f"(check {wigame_id} {sexpr})").payload["truth"] == "false"


@pytest.mark.skipif(not PHYSICISTS.exists(), reason="corpus/physicists is not available")
def test_physicists_ingestion():
    system, runtime, contexts, declarations, report = build_world(PHYSICISTS, lang="en", limit=3)

    assert report.asserted > 0
    facts = [fact for wigame in system.wigames.values() for fact in wigame.facts.values()]
    she_facts = [fact for fact in facts if fact.proposition.subject_symbol_id.startswith("she@")]
    assert len(she_facts) >= 3
    fact = facts[0]
    wigame_id = fact.proposition.wigame_id
    checked = runtime.evaluate(f"(check {wigame_id} {fact.proposition.sexpr()})")
    assert checked.payload["truth"] == "true"


@pytest.mark.skipif(not PHYSICISTS.exists(), reason="corpus/physicists is not available")
def test_physicists_planted_contradiction():
    system, runtime, contexts, declarations, _ = build_world(PHYSICISTS, lang="en", limit=1)
    declaration = declarations[0]
    sexpr = f"({declaration.relation} {declaration.a} {declaration.b})"
    wigame_id = f"wigame:{declaration.ctx_id}:{declaration.relation}"

    runtime.evaluate(f"(retract {wigame_id} {sexpr})")
    second = ingest_contexts(system, runtime, contexts, [declaration])

    assert [item[0] for item in second.rejected] == [sexpr]
