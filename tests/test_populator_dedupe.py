"""Tests for repeated-sentence deduplication in the populator."""

from __future__ import annotations

from populator import build_corpus
from populator.extract import Document


def test_repeated_sentences_collapse_to_the_first_occurrence():
    document = Document(
        "d",
        "La lechuga tiene hoja. "
        "La lechuga tiene hoja. "
        "La lechuga tiene hoja. "
        "La espinaca tiene hoja.",
    )

    corpus = build_corpus([document])

    assert len(corpus.individuals) == 2
    assert corpus.individuals[0].char_span == (0, 22)
    assert corpus.individuals[1].char_span[0] == 69
    assert corpus.X.shape[0] == 2
    assert all(occurrence.row < 2 for occurrence in corpus.occurrences)
    assert all(individual.sentence_index in {0, 3} for individual in corpus.individuals)


def test_dedupe_can_be_disabled():
    document = Document("d", "La lechuga tiene hoja. La lechuga tiene hoja. La lechuga tiene hoja.")

    corpus = build_corpus([document], dedupe=False)

    assert len(corpus.individuals) == 3
    assert corpus.X.shape[0] == 3
