"""Tests for the SIA to Matrix S-expression bridge."""

from __future__ import annotations

from pathlib import Path

import pytest

from pipeline import auto_confirm_candidates, build_system, corpus_to_sexprs
from populator import build_corpus, read_documents

CORPUS = str(Path(__file__).resolve().parents[1] / "corpus" / "vegetales")


@pytest.fixture(scope="module")
def corpus():
    return build_corpus(read_documents(CORPUS))


@pytest.fixture(scope="module")
def sexprs(corpus):
    return corpus_to_sexprs(corpus, "vegetales", documents=read_documents(CORPUS))


def find_candidate(system, kind: str, proposition: str):
    """Returns the candidate of a kind whose payload holds one proposition."""

    for candidate in system.candidates.values():
        if candidate.kind == kind and candidate.payload.get("proposition") == proposition:
            return candidate
    raise AssertionError(f"missing {kind} candidate for {proposition}")


def test_create_sexprs_are_all_accepted(sexprs):
    from src.operational_model import LogicalSystem, SExpressionRuntime

    runtime = SExpressionRuntime(LogicalSystem())
    for sexpr in sexprs:
        result = runtime.evaluate(sexpr)
        if sexpr.startswith("(create"):
            assert result.status == "accept", sexpr


def test_bridge_flags_auto_confirmable_arcs(sexprs):
    from src.operational_model import LogicalSystem, SExpressionRuntime

    system = LogicalSystem()
    runtime = SExpressionRuntime(system)
    for sexpr in sexprs:
        runtime.evaluate(sexpr)
    auto = auto_confirm_candidates(system)

    assert auto
    for candidate_id in auto:
        candidate = system.candidates[candidate_id]
        assert candidate.kind == "fact"
        assert candidate.evidence["stats"]["phi_entropic"] >= 0.99
        assert candidate.evidence["stats"]["n_a"] >= 20


def test_lechuga_implies_hoja_candidate_has_provenance():
    system, _, _ = build_system(CORPUS)
    candidate = find_candidate(system, "fact", "(implies lechuga hoja)")
    stats = candidate.evidence["stats"]

    assert stats["phi_entropic"] >= 0.85
    assert stats["n_a"] >= 20
    assert candidate.evidence["curation"] == "confirmed"  # auto-confirmed by build_system
    documents = {document.document_id: document for document in read_documents(CORPUS)}
    provenance = candidate.evidence["prov"]
    assert provenance
    first = provenance[0]
    start, end = first["span"]
    document = documents[first["document_id"]]
    assert 0 <= start < end <= len(document.text)
    assert "lechuga" in document.text[start:end]


def test_nonsense_candidate_for_zanahoria_implies_hoja():
    system, _, _ = build_system(CORPUS)
    candidate = find_candidate(system, "nonsense", "(implies zanahoria hoja)")

    assert candidate.evidence["stats"]["n_anb"] == 0
    assert candidate.evidence["curation"] == "proposed"


def test_class_candidate_from_significant_level():
    system, _, _ = build_system(CORPUS)
    classes = [candidate for candidate in system.candidates.values() if candidate.kind == "class"]

    assert classes
    assert all(len(candidate.payload["symbols"]) >= 2 for candidate in classes)
