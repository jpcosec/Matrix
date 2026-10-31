"""Tests for populator.extract: document loading and sentence spans."""

from __future__ import annotations

from pathlib import Path

from populator.extract import Document, read_documents, split_sentences


def test_split_sentences_has_exact_spans_and_count():
    text = "La sopa hierve.\n\n¿Está lista? Sí; ya casi.\nFalta la sal."
    doc = Document("test", text)
    sentences = split_sentences(doc)

    assert len(sentences) == 4
    assert [sentence.text for sentence in sentences] == [
        "La sopa hierve.",
        "¿Está lista?",
        "Sí; ya casi.",
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


def test_clean_markdown_blanks_boilerplate_and_preserves_offsets():
    from populator.extract import clean_markdown

    text = (
        "---\nid: atom-x\ntopic: y\n---\n"
        "# Título\n"
        "- item uno\n"
        "Co-Authored-By: Claude Fable 5.\n"
        "Ver https://example.com y /home/jp/proyectos/x\n"
        "```\ncode block\n```\n"
        "| a | b |\n"
    )
    cleaned = clean_markdown(text)

    assert len(cleaned) == len(text)
    assert "atom-x" not in cleaned
    assert "Claude Fable" not in cleaned
    assert "example.com" not in cleaned
    assert "/home/jp/proyectos" not in cleaned
    assert "code block" not in cleaned
    assert "Título" in cleaned
    assert "item uno" in cleaned


def test_read_documents_keeps_raw_text_and_cleaned_offsets(tmp_path):
    from populator.extract import Document, clean_markdown, read_documents, split_sentences

    path = tmp_path / "doc.md"
    raw = "---\nid: x\n---\nLa lechuga tiene hoja.\n"
    path.write_text(raw, encoding="utf-8")

    document = read_documents(path)[0]
    sentence = split_sentences(document)[0]

    assert document.raw_text == raw
    assert document.text == clean_markdown(raw)
    assert len(document.text) == len(document.raw_text)
    assert sentence.text == "La lechuga tiene hoja."
    assert document.text[sentence.char_span[0] : sentence.char_span[1]] == sentence.text


def test_split_sentences_keeps_parenthetical_dates_and_semicolons():
    text = (
        "Marie Salomea Sklodowska (born 7 November 1867; died 4 July 1934) was a physicist. "
        "She worked in Paris."
    )
    sentences = split_sentences(Document("test", text))

    assert [sentence.text for sentence in sentences] == [
        "Marie Salomea Sklodowska (born 7 November 1867; died 4 July 1934) was a physicist.",
        "She worked in Paris.",
    ]
    assert "1934)" in sentences[0].text
