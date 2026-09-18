"""Document loading and sentence segmentation with exact offsets."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

_SENTENCE_END = ".!?;"
_DOCUMENT_SUFFIXES = (".md", ".txt")

_FRONTMATTER_RE = re.compile(r"\A---\r?\n.*?\r?\n---[ \t]*(?:\r?\n|\Z)", re.DOTALL)
_FENCE_RE = re.compile(r"```.*?(?:```|\Z)", re.DOTALL)
_INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
_URL_RE = re.compile(r"\b(?:https?://|www\.)\S*", re.IGNORECASE)
_PATH_RE = re.compile(r"(?<![\w#])/[\w.\-/]+")
_METADATA_RE = re.compile(r"(?m)^[ \t]*[A-Za-z_][A-Za-z0-9_.-]{0,30}[ \t]*:.*$")
_FOOTER_RE = re.compile(r"(?m)^[ \t]*(?:©|\(c\))[^\n]*$", re.IGNORECASE)
_HEADING_RE = re.compile(r"(?m)^[ \t]*#{1,6}[ \t]+")
_LIST_RE = re.compile(r"(?m)^[ \t]*[-*+][ \t]+")


@dataclass(frozen=True)
class Document:
    """A loaded text document with its NFC-normalized content.

    ``text`` is the cleaned text (markdown boilerplate removed) and ``raw_text``
    keeps the original bytes. ``clean_markdown`` preserves offsets, so sentence
    and ``Prov`` spans are valid over both strings.
    """

    document_id: str
    text: str
    raw_text: str = ""


@dataclass(frozen=True)
class Sentence:
    """A sentence slice with an exact character span over its document."""

    document_id: str
    index: int
    char_span: tuple[int, int]
    text: str


def clean_markdown(text: str) -> str:
    """Blanks markdown boilerplate while preserving character offsets."""

    cleaned = _FRONTMATTER_RE.sub(_blank_match, text)
    cleaned = _FENCE_RE.sub(_blank_match, cleaned)
    cleaned = _INLINE_CODE_RE.sub(_blank_match, cleaned)
    cleaned = _URL_RE.sub(_blank_match, cleaned)
    cleaned = _PATH_RE.sub(_blank_match, cleaned)
    cleaned = _METADATA_RE.sub(_blank_match, cleaned)
    cleaned = _FOOTER_RE.sub(_blank_match, cleaned)
    cleaned = _HEADING_RE.sub(_blank_match, cleaned)
    cleaned = _LIST_RE.sub(_blank_match, cleaned)
    return cleaned.replace("|", " ")


def _blank_match(match: re.Match[str]) -> str:
    """Returns same-length whitespace so every offset stays valid."""

    return "".join("\n" if char == "\n" else " " for char in match.group(0))


def read_documents(
    paths: str | Path | list[str | Path],
    recursive: bool = False,
    clean: bool = True,
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
    documents: list[Document] = []
    for path in candidates:
        raw_text = unicodedata.normalize("NFC", path.read_text(encoding="utf-8"))
        text = clean_markdown(raw_text) if clean else raw_text
        documents.append(Document(str(path), text, raw_text))
    return documents


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
