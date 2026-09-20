"""Declaration contexts: chunks with local, unnormalized signs.

A chunk is the context of declaration and a symbol is ``(sign, context)``:
``she@Q7186`` and ``she@Q937`` are different symbols. Normalization exists only
to recognise repetitions *inside* a chunk.
"""

from __future__ import annotations

from collections import Counter
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from .extract import Document, Sentence, split_sentences
from .tokenize import normalize, tokenize

HEADING_RE = re.compile(r"^#\s+(.*)$", re.MULTILINE)

PRONOUNS = {
    "she", "he", "it", "they", "her", "him", "his", "hers", "their",
    "ella", "él", "ellos", "ellas", "su",
}

FUNCTION_WORDS_EN = {
    "a", "about", "above", "after", "again", "all", "also", "am", "an", "and", "any",
    "are", "as", "at", "be", "because", "been", "before", "being", "below", "between",
    "both", "but", "by", "can", "could", "did", "do", "does", "during", "each", "either",
    "else", "for", "from", "further", "had", "has", "have", "having", "how", "if", "in",
    "into", "is", "just", "may", "might", "more", "most", "much", "must", "no", "nor",
    "not", "now", "of", "off", "on", "once", "only", "or", "other", "our", "out", "over",
    "own", "same", "should", "so", "some", "such", "than", "that", "the", "then", "there",
    "these", "this", "those", "through", "to", "too", "under", "until", "up", "very",
    "was", "we", "were", "what", "when", "where", "which", "while", "who", "whom", "why",
    "will", "with", "would", "you", "your",
}

FUNCTION_WORDS_ES = {
    "a", "al", "algo", "algunas", "algunos", "ante", "antes", "aqui", "asi", "aun",
    "bajo", "bastante", "bien", "cada", "casi", "cierto", "como", "con", "contra", "cual",
    "cuando", "de", "del", "desde", "donde", "dos", "durante", "el", "en", "entre", "era",
    "eran", "es", "esa", "esas", "ese", "eso", "esos", "esta", "estas", "este", "esto",
    "estos", "fue", "fueron", "ha", "han", "hasta", "hay", "la", "las", "les", "lo", "los",
    "mas", "me", "menos", "mi", "mis", "mismo", "mucho", "muy", "nada", "ni", "no", "nos",
    "o", "otra", "otras", "otro", "otros", "para", "pero", "poco", "por", "porque", "pues",
    "que", "quien", "se", "sin", "sobre", "son", "tal", "tan", "tambien", "tanto", "te",
    "todo", "todos", "tras", "tu", "tus", "un", "una", "unas", "uno", "unos", "y", "ya",
}

FUNCTION_WORDS = {"en": FUNCTION_WORDS_EN, "es": FUNCTION_WORDS_ES}

MAX_NAME_TOKENS = 4
MIN_TERM_LENGTH = 3


@dataclass(frozen=True)
class Chunk:
    """One declaration context: a document or one of its level-1 sections."""

    ctx_id: str
    document_id: str
    title: str
    text: str
    char_offset: int


@dataclass(frozen=True)
class Occurrence:
    """One appearance of a sign, with an absolute span over `Document.text`."""

    sentence_index: int
    span: tuple[int, int]


@dataclass
class LocalSign:
    """A sign as declared inside one chunk."""

    sign: str
    norm: str
    ctx_id: str
    occurrences: list[Occurrence] = field(default_factory=list)
    kind: Literal["name", "pronoun", "term"] = "term"

    @property
    def symbol_id(self) -> str:
        """Returns the context-local symbol identifier."""

        return f"{self.norm}@{self.ctx_id}"


@dataclass
class ContextIndex:
    """The signs declared by one chunk, indexed by their normalized form."""

    chunk: Chunk
    sentences: list[Sentence]
    signs: dict[str, LocalSign]

    def signs_in(self, sentence_index: int) -> list[LocalSign]:
        """Returns the signs occurring in one sentence, ordered by span."""

        found: list[tuple[int, LocalSign]] = []
        for sign in self.signs.values():
            for occurrence in sign.occurrences:
                if occurrence.sentence_index == sentence_index:
                    found.append((occurrence.span[0], sign))
                    break
        found.sort(key=lambda item: item[0])
        return [sign for _, sign in found]


@dataclass(frozen=True)
class _Token:
    """One token with its sentence index and absolute span."""

    text: str
    norm: str
    span: tuple[int, int]
    sentence_index: int


def chunk_documents(
    docs: list[Document],
    unit: Literal["document", "section"] = "document",
) -> list[Chunk]:
    """Splits documents into declaration contexts."""

    if unit not in {"document", "section"}:
        raise ValueError(f"unsupported unit: {unit}")
    chunks: list[Chunk] = []
    for document in docs:
        stem = Path(document.document_id).stem
        if unit == "document":
            chunks.append(
                Chunk(
                    ctx_id=stem,
                    document_id=document.document_id,
                    title=_first_heading(document.text) or stem,
                    text=document.text,
                    char_offset=0,
                )
            )
            continue
        headings = list(HEADING_RE.finditer(document.text))
        if not headings:
            chunks.append(
                Chunk(
                    ctx_id=f"{stem}#0",
                    document_id=document.document_id,
                    title=stem,
                    text=document.text,
                    char_offset=0,
                )
            )
            continue
        for index, heading in enumerate(headings):
            start = heading.start()
            end = headings[index + 1].start() if index + 1 < len(headings) else len(document.text)
            chunks.append(
                Chunk(
                    ctx_id=f"{stem}#{index}",
                    document_id=document.document_id,
                    title=heading.group(1).strip(),
                    text=document.text[start:end],
                    char_offset=start,
                )
            )
    return chunks


def build_contexts(
    docs: list[Document],
    unit: Literal["document", "section"] = "document",
    lang: str = "en",
) -> list[ContextIndex]:
    """Builds one ContextIndex per declaration context."""

    return [build_context(chunk, lang=lang) for chunk in chunk_documents(docs, unit=unit)]


def build_context(
    chunk: Chunk,
    lang: str = "en",
    max_n: int = 3,
    min_count: int = 1,
) -> ContextIndex:
    """Extracts the local signs of one chunk with exact absolute offsets."""

    function_words = FUNCTION_WORDS.get(lang, FUNCTION_WORDS_EN)
    sentences = _chunk_sentences(chunk)
    rows = [_row(sentence, index) for index, sentence in enumerate(sentences)]
    token_text = {id(token): token for row in rows for token in row}
    title_norms = _title_norms(chunk.title)
    capitalized = [token for token in token_text.values() if _is_capitalized(token) and token.norm not in function_words]
    non_initial_caps = {
        token.norm
        for row in rows
        for position, token in enumerate(row)
        if position > 0 and _is_capitalized(token) and token.norm not in function_words
    }
    repeated_caps = {norm for norm, count in Counter(token.norm for token in capitalized).items() if count > 1}
    available = non_initial_caps | repeated_caps | title_norms

    signs: dict[str, LocalSign] = {}
    for surface, norm in _title_signs(chunk, function_words):
        signs.setdefault(norm, LocalSign(sign=surface, norm=norm, ctx_id=chunk.ctx_id, kind="name"))
    consumed: set[int] = set()
    for row in rows:
        _collect_names(row, chunk, function_words, available, title_norms, signs, consumed)
    for token in token_text.values():
        surface = token.text.lower()
        if surface in PRONOUNS:
            _add_sign(signs, token.text, surface, chunk.ctx_id, "pronoun", token)
    vocabulary = _term_vocabulary(rows, consumed, function_words, max_n, min_count)
    for row in rows:
        _collect_terms(row, chunk, vocabulary, max_n, consumed, function_words, signs)
    return ContextIndex(chunk=chunk, sentences=sentences, signs=signs)


def _chunk_sentences(chunk: Chunk) -> list[Sentence]:
    """Splits the chunk text into sentences with absolute spans."""

    local = Document(document_id=chunk.document_id, text=chunk.text)
    offset = chunk.char_offset
    return [
        Sentence(
            document_id=chunk.document_id,
            index=sentence.index,
            char_span=(sentence.char_span[0] + offset, sentence.char_span[1] + offset),
            text=sentence.text,
        )
        for sentence in split_sentences(local)
    ]


def _row(sentence: Sentence, index: int) -> list[_Token]:
    offset = sentence.char_span[0]
    return [
        _Token(
            text=token.text,
            norm=token.norm,
            span=(offset + token.char_span[0], offset + token.char_span[1]),
            sentence_index=index,
        )
        for token in tokenize(sentence)
    ]


def _same_line(chunk: Chunk, left: _Token, right: _Token) -> bool:
    """Reports whether two tokens sit on the same text line."""

    segment = chunk.text[left.span[1] - chunk.char_offset : right.span[0] - chunk.char_offset]
    return "\n" not in segment


def _title_signs(chunk: Chunk, function_words: set[str]) -> list[tuple[str, str]]:
    """Returns the `(surface, norm)` name windows declared by the chunk title."""

    title = chunk.title.strip()
    if not title:
        return []
    sentence = Sentence(document_id=chunk.document_id, index=0, char_span=(0, len(title)), text=title)
    tokens = tokenize(sentence)
    windows: list[tuple[str, str]] = []
    index = 0
    while index < len(tokens):
        if not tokens[index].text[:1].isupper() or tokens[index].norm in function_words:
            index += 1
            continue
        end = index + 1
        while end < len(tokens) and end - index < MAX_NAME_TOKENS:
            if not tokens[end].text[:1].isupper() or tokens[end].norm in function_words:
                break
            end += 1
        window = tokens[index:end]
        windows.append((" ".join(part.text for part in window), " ".join(part.norm for part in window)))
        index = end
    return windows


def _is_capitalized(token: _Token) -> bool:
    first = token.text[:1]
    return bool(first) and first.isupper() and first.isalpha()


def _title_norms(title: str) -> set[str]:
    return {norm for norm in (normalize(part) for part in title.split()) if norm}


def _collect_names(
    row: list[_Token],
    chunk: Chunk,
    function_words: set[str],
    available: set[str],
    title_norms: set[str],
    signs: dict[str, LocalSign],
    consumed: set[int],
) -> None:
    index = 0
    while index < len(row):
        token = row[index]
        if not _is_capitalized(token) or token.norm in function_words:
            index += 1
            continue
        qualified = token.norm in available or token.norm in title_norms
        if index == 0 and not qualified:
            index += 1
            continue
        end = index + 1
        while end < len(row) and end - index < MAX_NAME_TOKENS:
            following = row[end]
            if not _is_capitalized(following) or following.norm in function_words:
                break
            if not _same_line(chunk, row[end - 1], following):
                break
            end += 1
        window = row[index:end]
        span = (window[0].span[0], window[-1].span[1])
        surface = chunk.text[span[0] - chunk.char_offset : span[1] - chunk.char_offset]
        norm = " ".join(part.norm for part in window)
        _add_occurrence(signs, surface, norm, chunk.ctx_id, "name", window[0].sentence_index, span)
        for part in window:
            consumed.add(id(part))
        index = end


def _term_vocabulary(
    rows: list[list[_Token]],
    consumed: set[int],
    function_words: set[str],
    max_n: int,
    min_count: int,
) -> set[str]:
    """Returns the eligible unigrams plus the n-grams repeated in the chunk."""

    def eligible(token: _Token) -> bool:
        return (
            id(token) not in consumed
            and token.norm not in function_words
            and token.text.lower() not in PRONOUNS
            and len(token.norm) >= MIN_TERM_LENGTH
        )

    counts: Counter[str] = Counter()
    for row in rows:
        for start in range(len(row)):
            if not eligible(row[start]):
                continue
            for size in range(1, max_n + 1):
                if start + size > len(row):
                    break
                window = row[start : start + size]
                if not all(eligible(token) for token in window):
                    break
                counts[" ".join(token.norm for token in window)] += 1
    return {
        norm
        for norm, count in counts.items()
        if len(norm.split()) == 1 or count >= max(min_count, 2)
    }


def _collect_terms(
    row: list[_Token],
    chunk: Chunk,
    vocabulary: set[str],
    max_n: int,
    consumed: set[int],
    function_words: set[str],
    signs: dict[str, LocalSign],
) -> None:
    index = 0
    while index < len(row):
        token = row[index]
        if id(token) in consumed or token.norm in function_words or token.text.lower() in PRONOUNS:
            index += 1
            continue
        size = 0
        for candidate in range(min(max_n, len(row) - index), 0, -1):
            window = row[index : index + candidate]
            norm = " ".join(part.norm for part in window)
            if norm not in vocabulary or any(id(part) in consumed for part in window):
                continue
            if any(not _same_line(chunk, window[position - 1], window[position]) for position in range(1, len(window))):
                continue
            size = candidate
            break
        if size == 0:
            index += 1
            continue
        window = row[index : index + size]
        span = (window[0].span[0], window[-1].span[1])
        surface = chunk.text[span[0] - chunk.char_offset : span[1] - chunk.char_offset]
        norm = " ".join(part.norm for part in window)
        _add_occurrence(signs, surface, norm, chunk.ctx_id, "term", window[0].sentence_index, span)
        index += size


def _add_sign(
    signs: dict[str, LocalSign],
    surface: str,
    norm: str,
    ctx_id: str,
    kind: Literal["name", "pronoun", "term"],
    token: _Token,
) -> None:
    _add_occurrence(signs, surface, norm, ctx_id, kind, token.sentence_index, token.span)


def _add_occurrence(
    signs: dict[str, LocalSign],
    surface: str,
    norm: str,
    ctx_id: str,
    kind: Literal["name", "pronoun", "term"],
    sentence_index: int,
    span: tuple[int, int],
) -> None:
    sign = signs.get(norm)
    if sign is None:
        signs[norm] = LocalSign(
            sign=surface,
            norm=norm,
            ctx_id=ctx_id,
            occurrences=[Occurrence(sentence_index, span)],
            kind=kind,
        )
        return
    occurrence = Occurrence(sentence_index, span)
    if occurrence not in sign.occurrences:
        sign.occurrences.append(occurrence)


class SignIndex:
    """Routes and retrieves signs across contexts; never decides identity."""

    def __init__(self, contexts: list[ContextIndex]) -> None:
        self._signs: dict[str, dict[str, LocalSign]] = {}
        for context in contexts:
            for norm, sign in context.signs.items():
                self._signs.setdefault(norm, {})[sign.ctx_id] = sign

    def contexts_of(self, norm: str) -> list[str]:
        """Returns the contexts where one normalized sign was declared."""

        return sorted(self._signs.get(normalize(norm), {}))

    def occurrences_of(self, norm: str, ctx_id: str) -> list[Occurrence]:
        """Returns the occurrences of one sign inside one context."""

        sign = self._signs.get(normalize(norm), {}).get(ctx_id)
        return list(sign.occurrences) if sign else []


def _first_heading(text: str) -> str:
    match = HEADING_RE.search(text)
    return match.group(1).strip() if match else ""
