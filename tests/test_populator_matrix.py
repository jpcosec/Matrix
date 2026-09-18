"""Tests for populator.matrix: Corpus shape, spans and vocabulary."""

from __future__ import annotations

from pathlib import Path

import pytest

from populator.extract import read_documents
from populator.matrix import build_corpus
from populator.tokenize import normalize

REQUIRED_CONCEPTS = {
    "lechuga",
    "espinaca",
    "zanahoria",
    "apio",
    "hoja",
    "raiz",
    "tallo",
    "hoja_lisa",
    "hoja_rugosa",
    "verde",
    "naranja",
}


@pytest.fixture(scope="module")
def corpus():
    root = Path(__file__).resolve().parents[1] / "corpus" / "vegetales"
    return build_corpus(read_documents(root))


def test_corpus_matrix_is_binary_with_matching_shape(corpus):
    assert corpus.X.shape == (len(corpus.individuals), len(corpus.concepts))
    assert set(corpus.X.data.tolist()) <= {1}
    assert corpus.X.nnz > 0


def test_corpus_has_at_least_250_sentences(corpus):
    assert len(corpus.individuals) >= 250


def test_corpus_contains_the_seed_vocabulary(corpus):
    assert REQUIRED_CONCEPTS <= set(corpus.concepts)


def test_concepts_are_sorted_and_supported(corpus):
    assert corpus.concepts == sorted(corpus.concepts)
    support = corpus.X.sum(axis=0).A1
    assert (support >= 5).all()


def test_occurrences_map_back_to_document_text(corpus):
    documents = read_documents(Path(__file__).resolve().parents[1] / "corpus" / "vegetales")
    by_id = {document.document_id: document for document in documents}

    assert corpus.occurrences
    for occurrence in corpus.occurrences:
        concept = corpus.concepts[occurrence.col]
        individual = corpus.individuals[occurrence.row]
        raw = by_id[individual.document_id].text[occurrence.char_span[0] : occurrence.char_span[1]]
        assert normalize(raw).replace(" ", "_") == concept
        assert raw in corpus.vocab_source[concept]


def test_individual_spans_fall_inside_their_document(corpus):
    documents = read_documents(Path(__file__).resolve().parents[1] / "corpus" / "vegetales")
    by_id = {document.document_id: document for document in documents}

    for individual in corpus.individuals:
        start, end = individual.char_span
        assert 0 <= start < end <= len(by_id[individual.document_id].text)
