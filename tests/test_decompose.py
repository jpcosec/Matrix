"""Tests for sentence decomposition into local `(R a b)` declarations."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pipeline.curate import FakeBackend
from pipeline.decompose import Declaration, decompose, decompose_heuristic, decompose_llm
from populator import build_context, build_contexts, chunk_documents, read_documents
from populator.extract import Document

CORPUS = Path(__file__).resolve().parents[1] / "corpus" / "vegetales"

CURIE_DOC = (
    "# Marie Curie\n"
    "Marie Curie was born in Warsaw. "
    "She was a physicist. "
    "She won the Nobel Prize. "
    "She studied at the Sorbonne. "
    "She worked at Paris. "
    "She discovered polonium. "
    "She married Pierre Curie. "
    "She died in Paris. "
    "She was very gifted. "
    "She was a physics physicist.\n"
)

CURIE_EXPECTED = {
    ("born_in", "marie_curie@Q7186", "warsaw@Q7186"),
    ("instance", "she@Q7186", "physicist@Q7186"),
    ("award", "she@Q7186", "nobel_prize@Q7186"),
    ("educated_at", "she@Q7186", "sorbonne@Q7186"),
    ("employer", "she@Q7186", "paris@Q7186"),
    ("discovered", "she@Q7186", "polonium@Q7186"),
    ("spouse", "she@Q7186", "pierre_curie@Q7186"),
    ("died_in", "she@Q7186", "paris@Q7186"),
    ("has_property", "she@Q7186", "gifted@Q7186"),
    ("instance", "she@Q7186", "physics@Q7186"),
    ("field", "she@Q7186", "physics@Q7186"),
}


@pytest.fixture(scope="module")
def curie_context():
    return build_contexts([Document("Q7186.md", CURIE_DOC)], lang="en")[0]


def test_english_patterns(curie_context):
    found = {
        (declaration.relation, declaration.a, declaration.b)
        for declaration in decompose_heuristic(curie_context, lang="en")
    }

    assert CURIE_EXPECTED <= found


def test_declarations_use_only_local_symbols(curie_context):
    local = {sign.symbol_id for sign in curie_context.signs.values()}

    for declaration in decompose_heuristic(curie_context, lang="en"):
        assert declaration.a in local
        assert declaration.b in local
        assert declaration.ctx_id == "Q7186"
        assert declaration.source == "heuristic"


def test_declaration_spans_point_into_the_document(curie_context):
    text = CURIE_DOC

    for declaration in decompose_heuristic(curie_context, lang="en"):
        start, end = declaration.span
        assert 0 <= start < end <= len(text)
        assert text[start:end].strip()


def test_declarations_are_frozen_and_span_ordered(curie_context):
    declarations = decompose_heuristic(curie_context, lang="en")

    assert all(isinstance(declaration, Declaration) for declaration in declarations)
    assert declarations == sorted(declarations, key=lambda item: item.span)


def test_spanish_patterns_on_vegetales():
    zanahorias = build_context(chunk_documents(read_documents(CORPUS / "03_zanahorias.md"))[0], lang="es")
    apio = build_context(chunk_documents(read_documents(CORPUS / "04_apio.md"))[0], lang="es")

    zanahoria_facts = {(d.relation, d.a, d.b) for d in decompose_heuristic(zanahorias, lang="es")}
    apio_facts = {(d.relation, d.a, d.b) for d in decompose_heuristic(apio, lang="es")}

    assert ("has_property", "zanahoria@03_zanahorias", "raiz@03_zanahorias") in zanahoria_facts
    assert ("has_property", "zanahoria@03_zanahorias", "naranja@03_zanahorias") in zanahoria_facts
    assert ("part_of", "raiz@03_zanahorias", "naranja@03_zanahorias") in zanahoria_facts
    assert ("has_property", "apio@04_apio", "tallo@04_apio") in apio_facts


def test_vegetales_fallback_relations_use_the_verb_lemma():
    lechugas = build_context(chunk_documents(read_documents(CORPUS / "01_lechugas.md"))[0], lang="es")

    relations = {declaration.relation for declaration in decompose_heuristic(lechugas, lang="es")}

    assert any(relation.startswith("rel:") for relation in relations)
    assert not any(relation == "rel:de" for relation in relations)


def test_decompose_llm_parses_clean_json(curie_context):
    reply = json.dumps([{"r": "born_in", "a_sign": "Marie Curie", "b_sign": "Warsaw"}])

    declarations = decompose_llm(curie_context, FakeBackend(reply), lang="en")

    assert declarations == [
        Declaration(
            ctx_id="Q7186",
            relation="born_in",
            a="marie_curie@Q7186",
            b="warsaw@Q7186",
            a_sign="Marie Curie",
            b_sign="Warsaw",
            sentence_index=declarations[0].sentence_index,
            span=declarations[0].span,
            source="llm",
        )
    ]
    assert declarations[0].source == "llm"


def test_decompose_llm_discards_non_local_signs_and_relations(curie_context):
    reply = json.dumps(
        [
            {"r": "born_in", "a_sign": "Marie Curie", "b_sign": "Mars"},
            {"r": "invented", "a_sign": "Marie Curie", "b_sign": "Warsaw"},
            {"r": "award", "a_sign": "Marie Curie", "b_sign": "Warsaw"},
        ]
    )

    declarations = decompose_llm(curie_context, FakeBackend(reply), lang="en")

    assert [(declaration.relation, declaration.a, declaration.b) for declaration in declarations] == [
        ("award", "marie_curie@Q7186", "warsaw@Q7186")
    ]


def test_decompose_merges_heuristic_and_llm(curie_context):
    reply = json.dumps([{"r": "born_in", "a_sign": "Marie Curie", "b_sign": "Warsaw"}])

    merged = decompose(curie_context, lang="en", backend=FakeBackend(reply))

    assert len(merged) == len(decompose_heuristic(curie_context, lang="en"))
    assert all(declaration.source == "heuristic" for declaration in merged)
