"""Accent-folded tokenization and stopword handling."""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from dataclasses import dataclass

from .extract import Sentence

_ALLOWED = set("abcdefghijklmnopqrstuvwxyz0123456789- ")
_TOKEN_RE = re.compile(r"[^\W_]+(?:-[^\W_]+)*", re.UNICODE)

STOPWORDS_ES: list[str] = [
    "a", "al", "algo", "algunas", "algunos", "ante", "antes", "aqui", "asi", "aun",
    "bajo", "bastante", "bien", "cada", "casi", "cierto", "como", "con", "contra",
    "cual", "cuando", "de", "del", "desde", "donde", "dos", "durante", "el", "ella",
    "ellas", "ellos", "en", "entre", "era", "es", "esa", "esas", "ese", "eso", "esos",
    "esta", "estas", "este", "esto", "estos", "fue", "ha", "hasta", "hay", "la", "las",
    "le", "les", "lo", "los", "mas", "me", "menos", "mi", "mismo", "mucho", "muy",
    "nada", "ni", "no", "nos", "o", "otra", "otras", "otro", "otros", "para", "pero",
    "poco", "por", "porque", "pues", "que", "quien", "se", "según", "ser", "si", "sin",
    "sobre", "son", "su", "sus", "tal", "tan", "también", "tanto", "te", "tiene", "todo",
    "todos", "tras", "tu", "un", "una", "unas", "uno", "unos", "y", "ya", "yo",
]

STOPWORDS_EN: list[str] = [
    "a", "about", "after", "again", "all", "also", "am", "an", "and", "another", "any",
    "are", "as", "at", "be", "because", "been", "before", "being", "between", "both",
    "but", "by", "can", "did", "do", "does", "during", "each", "either", "else", "for",
    "from", "further", "had", "has", "have", "having", "he", "her", "here", "hers",
    "him", "his", "how", "i", "if", "in", "into", "is", "it", "its", "just", "me",
    "more", "most", "my", "no", "nor", "not", "now", "of", "off", "on", "once", "only",
    "or", "other", "our", "out", "over", "own", "same", "she", "should", "so", "some",
    "such", "than", "that", "the", "their", "them", "then", "there", "these", "they",
    "this", "those", "through", "to", "too", "under", "until", "up", "very", "was",
    "we", "were", "what", "when", "where", "which", "while", "who", "whom", "why",
    "will", "with", "would", "you", "your",
]


@dataclass(frozen=True)
class Token:
    """One surface token with its normalized form and exact span."""

    text: str
    norm: str
    char_span: tuple[int, int]


def normalize(text: str) -> str:
    """Lowercases, strips accents and keeps only ``[a-z0-9- ]``."""

    decomposed = unicodedata.normalize("NFKD", text)
    without_marks = "".join(char for char in decomposed if not unicodedata.combining(char))
    return "".join(char for char in without_marks.lower() if char in _ALLOWED)


def tokenize(sentence: Sentence) -> list[Token]:
    """Tokenizes a sentence into normalized tokens with exact spans."""

    return [
        Token(match.group(0), normalize(match.group(0)), (match.start(), match.end()))
        for match in _TOKEN_RE.finditer(sentence.text)
    ]


def auto_stopwords(sentences_tokens: list[list[str]], df_ratio: float = 0.5) -> set[str]:
    """Returns tokens appearing in more than ``df_ratio`` of the sentences."""

    if not sentences_tokens:
        return set()
    document_frequency: Counter[str] = Counter()
    for tokens in sentences_tokens:
        document_frequency.update(set(tokens))
    threshold = df_ratio * len(sentences_tokens)
    return {token for token, count in document_frequency.items() if count > threshold}
