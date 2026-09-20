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
    "She was a physics physicist. "
    "She was a gifted physicist. "
    "She was a Polish physicist.\n"
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
    ("has_property", "she@Q7186", "physics@Q7186"),
    ("has_property", "she@Q7186", "polish@Q7186"),
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


def test_copula_head_is_the_last_sign_of_the_noun_phrase(curie_context):
    found = {
        (declaration.relation, declaration.a, declaration.b)
        for declaration in decompose_heuristic(curie_context, lang="en")
    }

    assert ("instance", "she@Q7186", "physicist@Q7186") in found
    assert not any(relation == "instance" and b == "physics@Q7186" for relation, _, b in found)


def test_copula_modifiers_become_has_property(curie_context):
    found = {
        (declaration.relation, declaration.a, declaration.b)
        for declaration in decompose_heuristic(curie_context, lang="en")
    }

    for modifier in ("physics@Q7186", "gifted@Q7186", "polish@Q7186"):
        assert ("has_property", "she@Q7186", modifier) in found


def test_field_rule_needs_a_field_modifier_and_role_head(curie_context):
    found = {
        (declaration.relation, declaration.a, declaration.b)
        for declaration in decompose_heuristic(curie_context, lang="en")
    }

    assert ("field", "she@Q7186", "physics@Q7186") in found
    assert not any(relation == "field" and b == "gifted@Q7186" for relation, _, b in found)


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
    starts = [declaration.span[0] for declaration in declarations]
    assert starts == sorted(starts)


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

    heuristic = decompose_heuristic(curie_context, lang="en")
    merged = decompose(curie_context, lang="en", backend=FakeBackend(reply))

    keys = [(declaration.relation, declaration.a, declaration.b) for declaration in merged]
    assert len(keys) == len(set(keys))
    assert {(declaration.relation, declaration.a, declaration.b) for declaration in heuristic} <= set(keys)
    assert all(declaration.source == "heuristic" for declaration in merged)


CURIE_LINE = (
    "# Marie Curie\n\n"
    "Marie Curie was born in Warsaw. "
    "She was the first person to win two Nobel Prizes. "
    "She was the first female professor at the University of Paris. "
    "She was a Polish physicist. "
    "Alexander Fleming worked on penicillin.\n"
)


def test_copula_noun_phrase_stops_before_infinitive_and_preposition():
    context = build_context(chunk_documents([Document("Q7186.md", CURIE_LINE)])[0], lang="en")

    found = {(d.relation, d.a, d.b) for d in decompose_heuristic(context, lang="en")}

    assert ("instance", "she@Q7186", "person@Q7186") in found
    assert ("has_property", "she@Q7186", "first@Q7186") in found
    assert ("instance", "she@Q7186", "professor@Q7186") in found
    assert ("has_property", "she@Q7186", "female@Q7186") in found
    assert not any(relation == "instance" and "nobel" in obj for relation, _, obj in found)
    assert not any(relation == "instance" and "university" in obj for relation, _, obj in found)


def test_fallback_never_uses_names_as_verbs():
    context = build_context(chunk_documents([Document("Q7186.md", CURIE_LINE)])[0], lang="en")

    relations = {d.relation for d in decompose_heuristic(context, lang="en")}

    assert not any(relation in {"rel:alexander", "rel:robert", "rel:s"} for relation in relations)
    assert "rel:work" in relations
