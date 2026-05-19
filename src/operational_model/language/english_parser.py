"""Controlled-English parser inspired by SHRDLU surface grammar."""

from __future__ import annotations

from dataclasses import dataclass

from .lexicon import LexiconToken, ShrdluLexicon, build_shrdlu_lexicon
from .semantic_frames import EntityDescriptor, ImperativeFrame, QueryFrame, RelationFrame, SemanticFrame


class ParseError(ValueError):
    """Raised when controlled English cannot be parsed."""


@dataclass
class TokenStream:
    """Small token reader for controlled-English parsing."""

    tokens: list[LexiconToken]
    index: int = 0

    def peek(self) -> LexiconToken | None:
        return self.tokens[self.index] if self.index < len(self.tokens) else None

    def take(self) -> LexiconToken:
        token = self.peek()
        if token is None:
            raise ParseError("unexpected end of sentence")
        self.index += 1
        return token

    def done(self) -> bool:
        return self.index >= len(self.tokens)


def parse_controlled_english(
    sentence: str,
    lexicon: ShrdluLexicon | None = None,
) -> SemanticFrame:
    """Parses one controlled-English sentence into a semantic frame."""

    lexicon = lexicon or build_shrdlu_lexicon()
    stream = TokenStream(lexicon.tokenize(sentence))
    first = stream.peek()
    if first is None:
        raise ParseError("empty sentence")
    if first.has("wh"):
        return _parse_wh_question(stream)
    if first.has("aux"):
        return _parse_yes_no_question(stream)
    if first.has("verb"):
        return _parse_imperative(stream)
    raise ParseError(f"unsupported sentence start: {first.surface}")


def _parse_imperative(stream: TokenStream) -> ImperativeFrame:
    token = stream.take()
    action = token.semantic_value or token.root
    direct_object = None if action in {"release", "show"} else _parse_entity(stream)
    relation = None
    if not stream.done():
        prep = _expect_category(stream.take(), "preposition")
        relation = RelationFrame(prep.semantic_value or prep.root, _parse_entity(stream))
    if not stream.done():
        raise ParseError("unexpected trailing tokens in imperative")
    return ImperativeFrame(action=action, direct_object=direct_object, relation=relation)


def _parse_yes_no_question(stream: TokenStream) -> QueryFrame:
    copula = stream.take()
    _ = copula
    subject = _parse_entity(stream)
    if stream.done():
        return QueryFrame(query_kind="describe", subject=subject)
    prep = _expect_category(stream.take(), "preposition")
    obj = _parse_entity(stream)
    if not stream.done():
        raise ParseError("unexpected trailing tokens in yes/no question")
    return QueryFrame(
        query_kind="truth",
        subject=subject,
        relation=prep.semantic_value or prep.root,
        object=obj,
    )


def _parse_wh_question(stream: TokenStream) -> QueryFrame:
    wh = stream.take()
    wh_value = wh.semantic_value or wh.root
    if wh_value == "what":
        return _parse_what_question(stream, wh_value)
    if wh_value == "which":
        return _parse_which_question(stream, wh_value)
    if wh_value == "where":
        return _parse_where_question(stream, wh_value)
    raise ParseError(f"unsupported wh-question: {wh_value}")


def _parse_what_question(stream: TokenStream, wh_value: str) -> QueryFrame:
    _expect_category(stream.take(), "aux")
    if stream.peek() and stream.peek().has("preposition"):
        prep = stream.take()
        obj = _parse_entity(stream)
        if not stream.done():
            raise ParseError("unexpected trailing tokens in what-question")
        return QueryFrame(
            query_kind="which-entity",
            wh=wh_value,
            relation=prep.semantic_value or prep.root,
            object=obj,
        )
    subject = _parse_entity(stream)
    if not stream.done():
        raise ParseError("unexpected trailing tokens in what-question")
    return QueryFrame(query_kind="describe", wh=wh_value, subject=subject)


def _parse_which_question(stream: TokenStream, wh_value: str) -> QueryFrame:
    subject = _parse_entity(stream, allow_missing_determiner=True)
    _expect_category(stream.take(), "aux")
    prep = _expect_category(stream.take(), "preposition")
    obj = _parse_entity(stream)
    if not stream.done():
        raise ParseError("unexpected trailing tokens in which-question")
    return QueryFrame(
        query_kind="which-entity",
        wh=wh_value,
        subject=subject,
        relation=prep.semantic_value or prep.root,
        object=obj,
    )


def _parse_where_question(stream: TokenStream, wh_value: str) -> QueryFrame:
    _expect_category(stream.take(), "aux")
    subject = _parse_entity(stream)
    if not stream.done():
        raise ParseError("unexpected trailing tokens in where-question")
    return QueryFrame(query_kind="where", wh=wh_value, subject=subject)


def _parse_entity(stream: TokenStream, allow_missing_determiner: bool = False) -> EntityDescriptor:
    determiner = None
    adjectives: list[str] = []
    noun = None
    referent = None

    token = stream.peek()
    if token and token.has("determiner"):
        determiner = stream.take().semantic_value or token.root
    elif not allow_missing_determiner and token and token.has("pronoun"):
        pronoun = stream.take()
        return EntityDescriptor(referent=pronoun.semantic_value or pronoun.root)

    while stream.peek() and stream.peek().has("adjective"):
        adjective = stream.take()
        adjectives.append(adjective.semantic_value or adjective.root)

    token = stream.peek()
    if token is None:
        raise ParseError("entity is incomplete")
    if token.has("pronoun"):
        referent = stream.take().semantic_value or token.root
    elif token.has("noun"):
        noun_token = stream.take()
        noun = noun_token.semantic_value or noun_token.root
        if noun_token.has("name") and noun_token.semantic_kind == "referent":
            referent = noun_token.semantic_value or noun_token.root
    else:
        raise ParseError(f"expected noun phrase, got {token.surface}")

    return EntityDescriptor(
        determiner=determiner,
        adjectives=tuple(adjectives),
        noun=noun,
        referent=referent,
    )


def _expect_category(token: LexiconToken, category: str) -> LexiconToken:
    """Checks one required category."""

    if not token.has(category):
        raise ParseError(f"expected {category}, got {token.surface}")
    return token
