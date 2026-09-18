"""Multi-token phrase candidates, PMI prefilters and greedy longest match."""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass

from .tokenize import Token


@dataclass(frozen=True)
class Occurrence:
    """A matched concept and its character span inside a sentence."""

    concept: str
    char_span: tuple[int, int]


def count_ngrams(sent_tokens: list[list[str]], max_n: int = 3) -> Counter[tuple[str, ...]]:
    """Counts all n-grams up to ``max_n`` across the given tokenized sentences."""

    counts: Counter[tuple[str, ...]] = Counter()
    for tokens in sent_tokens:
        for size in range(1, max_n + 1):
            for index in range(len(tokens) - size + 1):
                counts[tuple(tokens[index : index + size])] += 1
    return counts


def pmi(
    counter_uni: Counter[tuple[str, ...]],
    counter_bi: Counter[tuple[str, ...]],
    n: int,
    eps: float = 1.0,
) -> dict[tuple[str, ...], float]:
    """Returns the epsilon-smoothed pointwise mutual information of bigrams."""

    values: dict[tuple[str, ...], float] = {}
    for bigram, joint in counter_bi.items():
        if len(bigram) != 2:
            continue
        left = counter_uni.get((bigram[0],), 0)
        right = counter_uni.get((bigram[1],), 0)
        values[bigram] = math.log((joint + eps) * n / ((left + eps) * (right + eps)))
    return values


def select_phrases(
    counts: Counter[tuple[str, ...]],
    min_count: int = 3,
    pmi_min: float | None = None,
) -> set[tuple[str, ...]]:
    """Selects frequent n-grams (n >= 2), optionally PMI-filtering bigrams."""

    total = sum(count for key, count in counts.items() if len(key) == 1)
    bigrams = {key: count for key, count in counts.items() if len(key) == 2}
    scores = pmi(counts, Counter(bigrams), total) if pmi_min is not None and total else {}
    phrases: set[tuple[str, ...]] = set()
    for key, count in counts.items():
        if len(key) < 2 or count < min_count:
            continue
        if pmi_min is not None and len(key) == 2 and scores.get(key, float("-inf")) < pmi_min:
            continue
        phrases.add(key)
    return phrases


def longest_match(
    tokens: list[Token],
    phrases: set[tuple[str, ...]],
    stopwords: set[str],
) -> list[Occurrence]:
    """Greedily matches the longest non-stopword n-gram at every position."""

    occurrences: list[Occurrence] = []
    index = 0
    while index < len(tokens):
        matched = 0
        for size in (3, 2, 1):
            if index + size > len(tokens):
                continue
            window = tokens[index : index + size]
            norms = tuple(token.norm for token in window)
            if size == 1:
                candidate = norms[0] not in stopwords
            else:
                candidate = norms in phrases and not any(norm in stopwords for norm in norms)
            if candidate:
                occurrences.append(
                    Occurrence(
                        "_".join(norms),
                        (window[0].char_span[0], window[-1].char_span[1]),
                    )
                )
                matched = size
                break
        index += matched if matched else 1
    return occurrences
