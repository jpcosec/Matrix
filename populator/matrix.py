"""Corpus construction: sparse individuals x concepts matrix with provenance."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

import numpy as np
from scipy import sparse

from .extract import Document, Sentence, split_sentences
from .phrases import count_ngrams, longest_match, select_phrases
from .tokenize import STOPWORDS_EN, STOPWORDS_ES, auto_stopwords, normalize, tokenize


@dataclass(frozen=True)
class Individual:
    """One row of the matrix: a sentence with its document coordinates."""

    document_id: str
    sentence_index: int
    char_span: tuple[int, int]


@dataclass(frozen=True)
class Occurrence:
    """One concept appearance mapped to matrix coordinates and text span."""

    row: int
    col: int
    char_span: tuple[int, int]


@dataclass(frozen=True)
class Corpus:
    """Sparse binary matrix plus concepts, individuals and provenance."""

    X: sparse.csr_matrix
    concepts: list[str]
    individuals: list[Individual]
    occurrences: list[Occurrence]
    vocab_source: dict[str, list[str]]


def _dedupe_sentences(sentences, tokens, sentence_norms):
    """Keeps the first occurrence of every normalized sentence sequence."""

    kept: list[int] = []
    seen: set[str] = set()
    for index, norms in enumerate(sentence_norms):
        key = " ".join(norms)
        if key in seen:
            continue
        seen.add(key)
        kept.append(index)
    return (
        [sentences[index] for index in kept],
        [tokens[index] for index in kept],
        [sentence_norms[index] for index in kept],
    )


def _is_valid_concept(concept: str) -> bool:
    """Rejects punctuation-only tokens that normalize to an empty concept."""

    return bool(concept.strip(" _-"))


def build_corpus(
    documents: list[Document],
    unit: str = "sentence",
    max_n: int = 3,
    min_count: int = 3,
    min_support: int = 5,
    pmi_min: float | None = None,
    extra_stopwords: tuple[str, ...] = (),
    max_concepts: int | None = None,
    lang: str | None = None,
    dedupe: bool = True,
) -> Corpus:
    """Builds the individuals x concepts Corpus from loaded documents.

    ``lang`` selects the stopword list (``"es"``, ``"en"``); ``None`` keeps both.
    ``max_concepts`` keeps the highest document-frequency concepts. ``dedupe``
    drops sentences whose normalized token sequence already appeared, keeping
    the first occurrence.
    """

    if unit != "sentence":
        raise ValueError(f"unsupported unit: {unit}")
    if lang not in {None, "es", "en"}:
        raise ValueError(f"unsupported lang: {lang}")
    sentences = [sentence for document in documents for sentence in split_sentences(document)]
    tokens = [tokenize(sentence) for sentence in sentences]
    sentence_norms = [[token.norm for token in token] for token in tokens]
    if dedupe:
        sentences, tokens, sentence_norms = _dedupe_sentences(sentences, tokens, sentence_norms)
    base_stopwords = {
        "es": {normalize(word) for word in STOPWORDS_ES},
        "en": {normalize(word) for word in STOPWORDS_EN},
        None: {normalize(word) for word in STOPWORDS_ES}
        | {normalize(word) for word in STOPWORDS_EN},
    }[lang]
    stopwords = (
        base_stopwords
        | {normalize(word) for word in extra_stopwords}
        | auto_stopwords(sentence_norms)
    )
    phrases = select_phrases(count_ngrams(sentence_norms, max_n), min_count, pmi_min)

    matched: list[tuple[int, str, tuple[int, int]]] = []
    for row, (sentence, sentence_tokens) in enumerate(zip(sentences, tokens)):
        offset = sentence.char_span[0]
        for occurrence in longest_match(sentence_tokens, phrases, stopwords):
            start, end = occurrence.char_span
            matched.append((row, occurrence.concept, (offset + start, offset + end)))

    support: Counter[str] = Counter()
    seen: set[tuple[int, str]] = set()
    for row, concept, _ in matched:
        if not _is_valid_concept(concept):
            continue
        if (row, concept) not in seen:
            seen.add((row, concept))
            support[concept] += 1
    concepts = sorted(concept for concept, count in support.items() if count >= min_support)
    if max_concepts is not None:
        ranked = [concept for concept, _ in support.most_common() if support[concept] >= min_support]
        concepts = sorted(ranked[:max_concepts])
    column = {concept: index for index, concept in enumerate(concepts)}

    rows: list[int] = []
    cols: list[int] = []
    for row, concept, _ in matched:
        if concept in column:
            rows.append(row)
            cols.append(column[concept])
    values = np.ones(len(rows), dtype=np.int8)
    shape = (len(sentences), len(concepts))
    matrix = sparse.csr_matrix((values, (rows, cols)), shape=shape, dtype=np.int8)
    matrix.data[:] = 1

    by_id = {document.document_id: document for document in documents}
    vocab_source: dict[str, list[str]] = {concept: [] for concept in concepts}
    occurrences: list[Occurrence] = []
    for row, concept, span in matched:
        if concept not in column:
            continue
        occurrences.append(Occurrence(row, column[concept], span))
        surface = by_id[sentences[row].document_id].text[span[0] : span[1]]
        if surface not in vocab_source[concept]:
            vocab_source[concept].append(surface)

    individuals = [
        Individual(sentence.document_id, sentence.index, sentence.char_span)
        for sentence in sentences
    ]
    return Corpus(
        X=matrix,
        concepts=concepts,
        individuals=individuals,
        occurrences=occurrences,
        vocab_source=vocab_source,
    )
