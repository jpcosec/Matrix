"""SHRDLU-inspired controlled lexicon for the prototype package."""

from __future__ import annotations

import re
from dataclasses import dataclass


WORD_RE = re.compile(r"[A-Za-z-]+|[?.!]")


@dataclass(frozen=True)
class LexiconEntry:
    surface: str
    root: str
    categories: tuple[str, ...]
    semantic_kind: str | None = None
    semantic_value: str | None = None


@dataclass(frozen=True)
class LexiconToken:
    surface: str
    root: str
    categories: tuple[str, ...]
    semantic_kind: str | None = None
    semantic_value: str | None = None

    def has(self, category: str) -> bool:
        return category in self.categories


class ShrdluLexicon:
    def __init__(self, entries: list[LexiconEntry]) -> None:
        self.entries = {entry.surface: entry for entry in entries}
        self.multiword_surfaces = sorted(
            [surface for surface in self.entries if " " in surface],
            key=lambda item: len(item.split()),
            reverse=True,
        )

    def tokenize(self, text: str) -> list[LexiconToken]:
        raw_words = [word.lower() for word in WORD_RE.findall(text)]
        tokens: list[LexiconToken] = []
        index = 0
        while index < len(raw_words):
            matched = self._match_multiword(raw_words, index)
            if matched:
                tokens.append(self._entry_to_token(self.entries[matched]))
                index += len(matched.split())
                continue
            word = raw_words[index]
            if word in {"?", ".", "!"}:
                index += 1
                continue
            entry = self.entries.get(word)
            if entry is not None:
                tokens.append(self._entry_to_token(entry))
            else:
                tokens.append(
                    LexiconToken(
                        surface=word,
                        root=word,
                        categories=("name", "noun"),
                        semantic_kind="referent",
                        semantic_value=word,
                    )
                )
            index += 1
        return tokens

    def _match_multiword(self, raw_words: list[str], index: int) -> str | None:
        for surface in self.multiword_surfaces:
            words = surface.split()
            if raw_words[index : index + len(words)] == words:
                return surface
        return None

    def _entry_to_token(self, entry: LexiconEntry) -> LexiconToken:
        return LexiconToken(
            surface=entry.surface,
            root=entry.root,
            categories=entry.categories,
            semantic_kind=entry.semantic_kind,
            semantic_value=entry.semantic_value,
        )


def build_shrdlu_lexicon() -> ShrdluLexicon:
    return ShrdluLexicon(_entries())


def _entries() -> list[LexiconEntry]:
    entries = [
        _entry("a", "a", ("determiner",), "determiner", "indef"),
        _entry("an", "a", ("determiner",), "determiner", "indef"),
        _entry("all", "all", ("determiner", "quantifier"), "determiner", "all"),
        _entry("any", "any", ("determiner", "quantifier"), "determiner", "indef"),
        _entry("each", "each", ("determiner", "quantifier"), "determiner", "all"),
        _entry("every", "every", ("determiner", "quantifier"), "determiner", "all"),
        _entry("no", "no", ("determiner", "quantifier", "negation"), "determiner", "no"),
        _entry("some", "some", ("determiner", "quantifier"), "determiner", "indef"),
        _entry("the", "the", ("determiner",), "determiner", "def"),
        _entry("this", "this", ("determiner", "deictic"), "determiner", "def"),
        _entry("that", "that", ("determiner", "deictic"), "determiner", "def"),
        _entry("what", "what", ("wh", "pronoun", "determiner"), "wh", "what"),
        _entry("which", "which", ("wh", "determiner"), "wh", "which"),
        _entry("where", "where", ("wh",), "wh", "where"),
        _entry("is", "be", ("aux", "verb", "copula"), "verb", "be"),
        _entry("are", "be", ("aux", "verb", "copula"), "verb", "be"),
        _entry("was", "be", ("aux", "verb", "copula"), "verb", "be"),
        _entry("were", "be", ("aux", "verb", "copula"), "verb", "be"),
        _entry("do", "do", ("aux", "verb"), "verb", "do"),
        _entry("does", "do", ("aux", "verb"), "verb", "do"),
        _entry("did", "do", ("aux", "verb"), "verb", "do"),
        _entry("can", "can", ("aux", "modal", "verb"), "verb", "can"),
        _entry("will", "will", ("aux", "modal", "verb"), "verb", "will"),
        _entry("it", "it", ("pronoun", "noun"), "referent", "it"),
        _entry("them", "they", ("pronoun", "noun"), "referent", "them"),
        _entry("they", "they", ("pronoun", "noun"), "referent", "they"),
        _entry("you", "you", ("pronoun", "noun"), "referent", "you"),
        _entry("i", "i", ("pronoun", "noun"), "referent", "i"),
        _entry("red", "red", ("adjective",), "property", "red"),
        _entry("blue", "blue", ("adjective",), "property", "blue"),
        _entry("green", "green", ("adjective",), "property", "green"),
        _entry("yellow", "yellow", ("adjective",), "property", "yellow"),
        _entry("purple", "purple", ("adjective",), "property", "purple"),
        _entry("white", "white", ("adjective",), "property", "white"),
        _entry("black", "black", ("adjective",), "property", "black"),
        _entry("big", "big", ("adjective",), "property", "big"),
        _entry("small", "small", ("adjective",), "property", "small"),
        _entry("large", "large", ("adjective",), "property", "large"),
        _entry("little", "little", ("adjective",), "property", "little"),
        _entry("block", "block", ("noun",), "class", "block"),
        _entry("blocks", "block", ("noun",), "class", "block"),
        _entry("box", "box", ("noun",), "class", "box"),
        _entry("boxes", "box", ("noun",), "class", "box"),
        _entry("cube", "cube", ("noun",), "class", "cube"),
        _entry("cubes", "cube", ("noun",), "class", "cube"),
        _entry("pyramid", "pyramid", ("noun",), "class", "pyramid"),
        _entry("pyramids", "pyramid", ("noun",), "class", "pyramid"),
        _entry("ball", "ball", ("noun",), "class", "ball"),
        _entry("balls", "ball", ("noun",), "class", "ball"),
        _entry("sphere", "sphere", ("noun",), "class", "sphere"),
        _entry("spheres", "sphere", ("noun",), "class", "sphere"),
        _entry("table", "table", ("noun",), "class", "table"),
        _entry("object", "object", ("noun",), "class", "object"),
        _entry("thing", "thing", ("noun",), "class", "thing"),
        _entry("name", "name", ("noun", "verb"), "class", "name"),
        _entry("color", "color", ("noun",), "class", "color"),
        _entry("shape", "shape", ("noun",), "class", "shape"),
        _entry("size", "size", ("noun",), "class", "size"),
        _entry("on", "on", ("preposition",), "relation", "on"),
        _entry("onto", "on", ("preposition",), "relation", "on"),
        _entry("in", "in", ("preposition",), "relation", "in"),
        _entry("into", "in", ("preposition",), "relation", "in"),
        _entry("inside", "in", ("preposition",), "relation", "in"),
        _entry("inside of", "inside-of", ("preposition", "combination"), "relation", "in"),
        _entry("on top of", "on-top-of", ("preposition", "combination"), "relation", "on"),
        _entry("in front of", "in-front-of", ("preposition", "combination"), "relation", "in-front-of"),
        _entry("in back of", "in-back-of", ("preposition", "combination"), "relation", "behind"),
        _entry("under", "under", ("preposition",), "relation", "under"),
        _entry("underneath", "under", ("preposition",), "relation", "under"),
        _entry("below", "under", ("preposition",), "relation", "under"),
        _entry("beneath", "under", ("preposition",), "relation", "under"),
        _entry("above", "above", ("preposition",), "relation", "above"),
        _entry("over", "above", ("preposition",), "relation", "above"),
        _entry("behind", "behind", ("preposition",), "relation", "behind"),
        _entry("beside", "beside", ("preposition",), "relation", "beside"),
        _entry("by", "beside", ("preposition",), "relation", "beside"),
        _entry("out of", "out-of", ("preposition", "combination"), "relation", "out-of"),
        _entry("move", "move", ("verb",), "action", "move"),
        _entry("put", "put", ("verb",), "action", "put"),
        _entry("pick", "pick", ("verb",), "action", "pick"),
        _entry("pick up", "pick-up", ("verb", "combination"), "action", "pick-up"),
        _entry("put down", "put-down", ("verb", "combination"), "action", "put-down"),
        _entry("grab", "grasp", ("verb",), "action", "grasp"),
        _entry("grasp", "grasp", ("verb",), "action", "grasp"),
        _entry("drop", "drop", ("verb",), "action", "drop"),
        _entry("release", "release", ("verb",), "action", "release"),
        _entry("hold", "hold", ("verb",), "action", "hold"),
        _entry("find", "find", ("verb",), "action", "find"),
        _entry("list", "list", ("verb",), "action", "list"),
        _entry("stack", "stack", ("verb", "noun"), "action", "stack"),
        _entry("build", "build", ("verb",), "action", "build"),
        _entry("contain", "contain", ("verb",), "action", "contain"),
        _entry("support", "support", ("verb", "noun"), "action", "support"),
        _entry("call", "call", ("verb",), "action", "call"),
        _entry("show", "show", ("verb",), "action", "show"),
        _entry("describe", "describe", ("verb",), "action", "describe"),
    ]
    return entries


def _entry(surface: str, root: str, categories: tuple[str, ...], semantic_kind: str | None = None, semantic_value: str | None = None) -> LexiconEntry:
    return LexiconEntry(surface, root, categories, semantic_kind, semantic_value)
