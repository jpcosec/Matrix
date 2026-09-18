"""Tests for the corpus-scale knobs (populator, bridge, pipeline reporting)."""

from __future__ import annotations

from pathlib import Path

import pytest

from populator import build_corpus, read_documents
from populator.extract import Document
from pipeline import corpus_to_sexprs
from pipeline.run import build_system

CORPUS = str(Path(__file__).resolve().parents[1] / "corpus" / "vegetales")


@pytest.fixture(scope="module")
def corpus():
    return build_corpus(read_documents(CORPUS))


def test_max_concepts_keeps_the_most_frequent(corpus):
    capped = build_corpus(read_documents(CORPUS), max_concepts=10)
    support = corpus.X.sum(axis=0).A1
    expected = {
        corpus.concepts[index]
        for index in sorted(range(len(corpus.concepts)), key=lambda index: -support[index])[:10]
    }

    assert len(capped.concepts) == 10
    assert set(capped.concepts) == expected


def test_lang_selects_the_stopword_list():
    text = "the zanahoria es raiz. " * 5 + "la zanahoria es raiz. " * 7
    document = Document("d", text)

    assert "the" in build_corpus([document], lang="es").concepts
    assert "the" not in build_corpus([document], lang="en").concepts


def test_recursive_reading(tmp_path):
    nested = tmp_path / "sub"
    nested.mkdir()
    (nested / "doc.md").write_text("La lechuga tiene hoja.", encoding="utf-8")

    assert read_documents(tmp_path) == []
    assert len(read_documents(tmp_path, recursive=True)) == 1


def test_bridge_caps_the_candidate_streams(corpus):
    sexprs = corpus_to_sexprs(
        corpus,
        "vegetales",
        max_fact_candidates=3,
        max_nonsense=2,
        max_class_candidates=1,
    )
    counts = _kind_counts(sexprs)

    assert counts["fact"] <= 3
    assert counts["nonsense"] <= 2
    assert counts["class"] <= 1


def test_build_system_reports_timings_and_memory():
    report: dict = {}
    system, runtime, results = build_system(
        CORPUS,
        "vegetales",
        max_fact_candidates=5,
        max_nonsense=5,
        report=report,
    )

    assert results
    assert report["concepts"] > 0
    assert report["populator_seconds"] >= 0
    assert report["runtime_seconds"] >= 0
    assert report["peak_memory_mb"] > 0
    assert report["total_seconds"] >= report["populator_seconds"]


def _kind_counts(sexprs: list[str]) -> dict[str, int]:
    counts = {"fact": 0, "nonsense": 0, "class": 0, "symbol": 0, "rule": 0}
    for sexpr in sexprs:
        for kind in counts:
            if sexpr.startswith(f"(candidate {kind} "):
                counts[kind] += 1
    return counts
