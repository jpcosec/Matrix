"""Tests for populator.tokenize: normalization, spans and stopwords."""

from __future__ import annotations

from populator.extract import Sentence
from populator.phrases import longest_match
from populator.tokenize import STOPWORDS_EN, STOPWORDS_ES, auto_stopwords, normalize, tokenize


def test_normalize_folds_accents_and_case():
    assert normalize("Raíz VERDE") == "raiz verde"


def test_tokenize_spans_are_exact():
    sentence = Sentence("doc", 0, (0, 14), "La raíz verde.")
    tokens = tokenize(sentence)

    assert [token.norm for token in tokens] == ["la", "raiz", "verde"]
    for token in tokens:
        start, end = token.char_span
        assert sentence.text[start:end] == token.text


def test_longest_match_drops_stopwords():
    sentence = Sentence("doc", 0, (0, 19), "La raíz está verde.")
    tokens = tokenize(sentence)
    stopwords = {"la", "esta"}

    concepts = [occurrence.concept for occurrence in longest_match(tokens, set(), stopwords)]

    assert concepts == ["raiz", "verde"]


def test_stopword_lists_are_available():
    assert len(STOPWORDS_ES) >= 100
    assert len(STOPWORDS_EN) >= 100


def test_auto_stopwords_detects_very_frequent_token():
    sentences = [["agua", "sal"], ["agua", "pan"], ["agua", "pan"], ["agua", "sal"], ["agua", "pan"]]

    assert "agua" in auto_stopwords(sentences, df_ratio=0.5)
    assert "sal" not in auto_stopwords(sentences, df_ratio=0.5)
