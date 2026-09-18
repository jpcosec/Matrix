"""Tests for populator.phrases: n-grams, PMI and greedy longest match."""

from __future__ import annotations

from collections import Counter

from populator.extract import Sentence
from populator.phrases import count_ngrams, longest_match, pmi, select_phrases
from populator.tokenize import tokenize


def synthetic_sentences() -> list[list[str]]:
    return [
        ["la", "hoja", "rugosa", "es", "verde"],
        ["la", "hoja", "rugosa", "es", "tierna"],
        ["la", "hoja", "rugosa", "se", "lava"],
    ]


def test_count_ngrams_counts_all_sizes():
    counts = count_ngrams([["a", "b", "c"]], max_n=3)

    assert counts[("a",)] == 1
    assert counts[("a", "b")] == 1
    assert counts[("a", "b", "c")] == 1


def test_select_phrases_keeps_frequent_bigram():
    counts = count_ngrams(synthetic_sentences(), max_n=3)
    phrases = select_phrases(counts, min_count=3)

    assert ("hoja", "rugosa") in phrases


def test_longest_match_returns_the_whole_phrase_with_covering_span():
    sentence = Sentence("doc", 0, (0, 23), "La hoja rugosa es verde.")
    tokens = tokenize(sentence)
    phrases = {("hoja", "rugosa")}

    occurrences = longest_match(tokens, phrases, {"la", "es"})

    assert occurrences[0].concept == "hoja_rugosa"
    start, end = occurrences[0].char_span
    assert sentence.text[start:end] == "hoja rugosa"
    assert [occurrence.concept for occurrence in occurrences] == ["hoja_rugosa", "verde"]


def test_pmi_rewards_always_together_pairs():
    counter_uni: Counter[tuple[str, ...]] = Counter({("hoja",): 10, ("rugosa",): 10, ("sopa",): 10})
    counter_bi: Counter[tuple[str, ...]] = Counter({("hoja", "rugosa"): 10, ("hoja", "sopa"): 1})

    scores = pmi(counter_uni, counter_bi, n=30)

    assert scores[("hoja", "rugosa")] > scores[("hoja", "sopa")]


def test_select_phrases_applies_pmi_prefilter_to_bigrams():
    counter_uni: Counter[tuple[str, ...]] = Counter(
        {("hoja",): 10, ("rugosa",): 10, ("sopa",): 10, ("pan",): 10}
    )
    counter_bi: Counter[tuple[str, ...]] = Counter({("hoja", "rugosa"): 10, ("pan", "sopa"): 1})
    counts = Counter({**counter_uni, **counter_bi})

    phrases = select_phrases(counts, min_count=3, pmi_min=0.0)

    assert ("hoja", "rugosa") in phrases
    assert ("pan", "sopa") not in phrases
