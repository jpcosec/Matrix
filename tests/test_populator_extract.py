"""Tests for populator.extract: document loading and sentence spans."""

from __future__ import annotations

from pathlib import Path

from populator.extract import Document, read_documents, split_sentences


def test_split_sentences_has_exact_spans_and_count():
    text = "La sopa hierve.\n\n¿Está lista? Sí; ya casi.\nFalta la sal."
    doc = Document("test", text)
    sentences = split_sentences(doc)

    assert len(sentences) == 5
    assert [sentence.text for sentence in sentences] == [
        "La sopa hierve.",
        "¿Está lista?",
        "Sí;",
        "ya casi.",
        "Falta la sal.",
    ]
    for sentence in sentences:
        start, end = sentence.char_span
        assert doc.text[start:end] == sentence.text


def test_split_sentences_indexes_are_sequential():
    doc = Document("test", "Uno. Dos. Tres.")

    assert [sentence.index for sentence in split_sentences(doc)] == [0, 1, 2]


def test_read_documents_reads_a_directory():
    corpus = Path(__file__).resolve().parents[1] / "corpus" / "vegetales"
    documents = read_documents(corpus)

    assert len(documents) >= 4
    assert all(document.text for document in documents)
    assert all(document.document_id.endswith(".md") for document in documents)
