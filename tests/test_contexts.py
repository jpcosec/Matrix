"""Tests for populator.contexts: declaration contexts with local signs."""

from __future__ import annotations

from pathlib import Path

import pytest

from populator import build_context, build_contexts, chunk_documents, read_documents
from populator.contexts import SignIndex
from populator.extract import Document
from populator.tokenize import normalize

CORPUS = Path(__file__).resolve().parents[1] / "corpus" / "vegetales"
PHYSICISTS = Path(__file__).resolve().parents[1] / "corpus" / "physicists" / "articles" / "Q7186.md"

DOC_A = (
    "# Marie Curie\n"
    "Marie Curie was born in Warsaw. "
    "Curie worked on radiation. "
    "she won the Nobel Prize.\n"
)
DOC_B = (
    "# Rosalind Franklin\n"
    "Rosalind Franklin studied DNA. "
    "she used diffraction. "
    "Franklin died young.\n"
)


@pytest.fixture(scope="module")
def contexts():
    docs = [Document("A.md", DOC_A), Document("B.md", DOC_B)]
    return docs, build_contexts(docs, lang="en")


def test_same_sign_in_two_contexts_stays_two_symbols(contexts):
    _, built = contexts
    index = SignIndex(built)

    signs = [built[0].signs["she"], built[1].signs["she"]]
    assert signs[0].ctx_id != signs[1].ctx_id
    assert signs[0].symbol_id != signs[1].symbol_id
    assert index.contexts_of("she") == ["A", "B"]
    assert len(index.occurrences_of("she", "A")) == 1
    assert len(index.occurrences_of("she", "B")) == 1


def test_names_are_not_folded_into_each_other(contexts):
    _, built = contexts
    signs = built[0].signs

    assert signs["marie curie"].kind == "name"
    assert signs["marie curie"].sign == "Marie Curie"
    assert signs["marie curie"].norm != signs["curie"].norm
    assert signs["curie"].kind == "name"
    assert signs["curie"].symbol_id == "curie@A"


def test_pronouns_are_kept_and_function_words_are_not(contexts):
    _, built = contexts
    signs = built[0].signs

    assert signs["she"].kind == "pronoun"
    assert signs["she"].sign == "she"
    assert all(word not in signs for word in ("the", "of", "was", "and", "on"))


def test_offsets_point_at_the_declared_sign(contexts):
    docs, built = contexts
    by_id = {document.document_id: document for document in docs}

    for context in built:
        document = by_id[context.chunk.document_id]
        for sign in context.signs.values():
            for occurrence in sign.occurrences:
                start, end = occurrence.span
                assert normalize(document.text[start:end]) == sign.norm


def test_signs_in_is_ordered_by_span(contexts):
    _, built = contexts

    for sentence_index in range(len(built[0].sentences)):
        spans = [
            next(
                occurrence.span[0]
                for occurrence in sign.occurrences
                if occurrence.sentence_index == sentence_index
            )
            for sign in built[0].signs_in(sentence_index)
        ]
        assert spans == sorted(spans)


def test_section_unit_splits_on_level_two_headings():
    document = Document(
        "d.md",
        "# Alpha\nalpha beta.\n## Beta\ngamma delta.\n### Beta one\ninner.\n## Gamma\nepsilon zeta.\n",
    )

    chunks = chunk_documents([document], unit="section")

    assert [chunk.ctx_id for chunk in chunks] == ["d#0", "d#1", "d#2"]
    assert [chunk.title for chunk in chunks] == ["Alpha", "Alpha — Beta", "Alpha — Gamma"]
    assert [chunk.metadata["article"] for chunk in chunks] == ["d", "d", "d"]
    assert "### Beta one" in chunks[1].text
    assert "### Beta one" not in chunks[0].text
    assert chunks[2].char_offset == document.text.index("## Gamma")


def test_section_chunks_keep_the_article_name_in_every_title():
    text = "# Marie Curie\n\nMarie Curie was born in Warsaw.\n## Life\nShe worked in Paris.\n"
    document = Document("Q7186.md", text)

    chunks = chunk_documents([document], unit="section")

    assert chunks[0].title == "Marie Curie"
    assert chunks[1].title == "Marie Curie — Life"
    context = build_context(chunks[1], lang="en")
    assert context.signs["marie curie"].kind == "name"


def test_document_unit_uses_the_stem_as_context_id():
    document = Document(str(CORPUS / "01_lechugas.md"), (CORPUS / "01_lechugas.md").read_text())

    chunks = chunk_documents([document])

    assert [chunk.ctx_id for chunk in chunks] == ["01_lechugas"]


def test_vegetales_terms_and_offsets():
    documents = read_documents(CORPUS / "01_lechugas.md")
    context = build_context(chunk_documents(documents)[0], lang="es")

    assert context.signs["lechuga"].symbol_id == "lechuga@01_lechugas"
    term = context.signs["hoja lisa"]
    assert term.kind == "term"
    assert term.norm == "hoja lisa"
    assert len(term.occurrences) > 1
    assert all("la" not in context.signs for _ in [0])
    for occurrence in term.occurrences:
        start, end = occurrence.span
        assert documents[0].text[start:end] == term.sign


@pytest.mark.skipif(not PHYSICISTS.exists(), reason="corpus/physicists is not available")
def test_physicists_signs():
    documents = read_documents(PHYSICISTS)
    context = build_context(chunk_documents(documents)[0], lang="en")

    # "Curie" never appears as a bare capitalised token outside a longer name
    # window ("Pierre Curie", "Skłodowska-Curie"): no alias folding happens.
    assert "curie" not in context.signs
    for norm in ("she", "marie curie", "nobel prize"):
        assert norm in context.signs, norm
    assert context.signs["marie curie"].kind == "name"
    assert context.signs["nobel prize"].kind == "name"
    assert context.signs["she"].kind == "pronoun"


def test_name_windows_allow_lowercase_connectors():
    documents = [
        Document(
            "U.md",
            "# Places\n"
            "University of Paris is famous. "
            "King's College London is old. "
            "Jacobus Henricus van 't Hoff studied here.\n",
        )
    ]

    context = build_context(chunk_documents(documents)[0], lang="en")

    assert context.signs["university of paris"].sign == "University of Paris"
    assert context.signs["university of paris"].kind == "name"
    assert context.signs["king s college london"].sign == "King's College London"
    assert context.signs["jacobus henricus van t hoff"].sign == "Jacobus Henricus van 't Hoff"
    assert all(
        context.signs[norm].kind == "name"
        for norm in ("university of paris", "king s college london", "jacobus henricus van t hoff")
    )


def test_sentence_initial_pronoun_is_still_a_pronoun():
    documents = [Document("C.md", "# Ada Lovelace\nShe wrote notes. She studied engines.\n")]

    context = build_context(chunk_documents(documents)[0], lang="en")

    assert context.signs["she"].kind == "pronoun"
    assert context.signs["she"].sign == "She"
    assert len(context.signs["she"].occurrences) == 2
    assert not [sign for sign in context.signs.values() if sign.norm == "she" and sign.kind == "name"]


def test_document_stem_is_never_a_sign():
    document = Document("/tmp/Q7186.md", "Marie Curie was born in Warsaw. Curie worked in Paris.")

    context = build_context(chunk_documents([document])[0], lang="en")

    assert context.chunk.title == ""
    assert "q7186" not in context.signs
    assert all(not sign.norm.startswith("q7186") for sign in context.signs.values())


def test_heading_is_the_only_title_source():
    document = Document("plain.md", "# Marie Curie\n\nMarie Curie was born in Warsaw.")

    context = build_context(chunk_documents([document])[0], lang="en")

    assert context.chunk.title == "Marie Curie"
    assert context.signs["marie curie"].kind == "name"


def test_name_windows_do_not_cross_punctuation():
    document = Document(
        "d.md",
        "# Apposition\n\nMarie Salomée Skłodowska, Madame Pierre Curie published papers.",
    )

    context = build_context(chunk_documents([document])[0], lang="en")

    # `normalize` drops the non-decomposable "ł", hence "skodowska".
    assert "marie salomee skodowska" in context.signs
    assert "madame pierre curie" in context.signs
