"""Tests for AROMA-driven projection candidates between two worlds."""

from __future__ import annotations

from pathlib import Path

import pytest

from pipeline.match import match_corpora
from pipeline.run import build_system
from populator import build_corpus, read_documents

BASE = Path(__file__).resolve().parents[1] / "corpus" / "vegetales"
HALF_A = [BASE / "01_lechugas.md", BASE / "02_espinacas.md", BASE / "03_zanahorias.md"]
HALF_B = [BASE / "04_apio.md", BASE / "05_hojas.md", BASE / "06_cocina.md"]
# The two halves share few concepts, so their strongest AROMA rule sits at phi ~0.76.
PHI_R = 0.7


@pytest.fixture(scope="module")
def matched():
    from src.operational_model import LogicalSystem, SExpressionRuntime

    documents_a = read_documents(HALF_A)
    documents_b = read_documents(HALF_B)
    corpus_a = build_corpus(documents_a, lang="es", dedupe=False)
    corpus_b = build_corpus(documents_b, lang="es", dedupe=False)
    system = LogicalSystem()
    build_system(HALF_A[0].parent, "a", corpus=corpus_a, documents=documents_a, lang="es", system=system)
    build_system(HALF_B[0].parent, "b", corpus=corpus_b, documents=documents_b, lang="es", system=system)
    runtime = SExpressionRuntime(system)
    sexprs = match_corpora(corpus_a, corpus_b, "a", "b", phi_r=PHI_R)
    results = [runtime.evaluate(sexpr) for sexpr in sexprs]
    return system, runtime, corpus_a, corpus_b, results


def candidate_pairs(system, result):
    """Returns the projection pairs stored in the queued candidate."""

    return system.candidates[result.payload["candidate_id"]].payload["pairs"]


def test_match_proposes_shared_concepts(matched):
    system, _, _, _, results = matched

    assert results
    assert all(result.status == "accept" for result in results)
    pairs = [pair for result in results for pair in candidate_pairs(system, result)]
    assert any(source == target for source, target in pairs)


def test_match_terms_belong_to_both_corpora(matched):
    system, _, corpus_a, corpus_b, results = matched
    concepts_a = set(corpus_a.concepts)
    concepts_b = set(corpus_b.concepts)

    system, _, _, _, _ = matched
    for result in results:
        for source, target in candidate_pairs(system, result):
            assert source in concepts_a
            assert target in concepts_b


def test_promoted_projection_projects_subjects(matched):
    system, runtime, _, _, results = matched
    result = next(
        result for result in results if any(s == t for s, t in candidate_pairs(system, result))
    )

    promoted = runtime.evaluate(f"(promote {result.payload['candidate_id']})")
    source, target = next((s, t) for s, t in candidate_pairs(system, result) if s == t)
    projection = system.projections[f"wigame:a->wigame:b"]
    listed = runtime.evaluate("(return projections wigame:a)").payload["projections"]

    assert promoted.status == "accept"
    assert projection.get(source, target) is True
    assert projection.project_subjects([source]) == [target]
    assert any(record["target"] == "wigame:b" for record in listed)


def test_class_match_flag_is_consistent_with_pairs(matched):
    system, _, _, _, results = matched

    for result in results:
        stats = system.candidates[result.payload["candidate_id"]].evidence["stats"]
        assert stats["class_match"] == (len(candidate_pairs(system, result)) > 1)
