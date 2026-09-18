"""Document loading and sentence segmentation with exact offsets."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from pathlib import Path

_SENTENCE_END = ".!?;"
_DOCUMENT_SUFFIXES = (".md", ".txt")


@dataclass(frozen=True)
class Document:
    """A loaded text document with its NFC-normalized content."""

    document_id: str
    text: str


@dataclass(frozen=True)
class Sentence:
    """A sentence slice with an exact character span over its document."""

    document_id: str
    index: int
    char_span: tuple[int, int]
    text: str


def read_documents(
    paths: str | Path | list[str | Path],
    recursive: bool = False,
) -> list[Document]:
    """Reads ``.md``/``.txt`` files (or a directory of them) into Documents."""

    if isinstance(paths, (str, Path)):
        base = Path(paths)
        if base.is_dir():
            children = base.rglob("*") if recursive else base.iterdir()
            candidates = sorted(child for child in children if child.suffix in _DOCUMENT_SUFFIXES)
        else:
            candidates = [base]
    else:
        candidates = [Path(path) for path in paths]
    return [
        Document(str(path), unicodedata.normalize("NFC", path.read_text(encoding="utf-8")))
        for path in candidates
    ]


def split_sentences(doc: Document) -> list[Sentence]:
    """Splits a document on ``. ! ? ;`` and blank lines, keeping exact spans."""

    text = doc.text
    length = len(text)
    sentences: list[Sentence] = []
    start: int | None = None
    index = 0
    while index < length:
        char = text[index]
        if start is None:
            if char.isspace():
                index += 1
                continue
            start = index
        if char in _SENTENCE_END:
            _emit(doc, sentences, start, index + 1)
            start = None
            index += 1
            continue
        if char == "\n" and index + 1 < length and text[index + 1] == "\n":
            _emit(doc, sentences, start, index)
            start = None
            index += 2
            continue
        index += 1
    if start is not None:
        _emit(doc, sentences, start, length)
    return sentences


def _emit(doc: Document, sentences: list[Sentence], start: int, end: int) -> None:
    """Appends one trimmed sentence slice to the result list."""

    while end > start and doc.text[end - 1].isspace():
        end -= 1
    if end <= start:
        return
    index = len(sentences)
    sentences.append(Sentence(doc.document_id, index, (start, end), doc.text[start:end]))
