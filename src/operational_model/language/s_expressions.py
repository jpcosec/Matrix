"""Minimal s-expression parser for the canonical Matrix surface."""

from __future__ import annotations

from collections import deque

SExpression = str | list["SExpression"]


def parse_s_expression(source: str) -> SExpression:
    """Parses one s-expression into nested Python lists and atoms."""

    raw_tokens = _tokenize(source)
    if not raw_tokens:
        raise ValueError("empty s-expression")
    tokens = deque(raw_tokens)
    expr = _parse_tokens(tokens)
    if tokens:
        raise ValueError(f"unexpected trailing tokens: {' '.join(tokens)}")
    return expr


def _tokenize(source: str) -> list[str]:
    """Splits source into parentheses and atom tokens."""

    tokens: list[str] = []
    current: list[str] = []
    for ch in source:
        if ch in "()":
            if current:
                tokens.append("".join(current))
                current.clear()
            tokens.append(ch)
        elif ch.isspace():
            if current:
                tokens.append("".join(current))
                current.clear()
        else:
            current.append(ch)
    if current:
        tokens.append("".join(current))
    return tokens


def _parse_tokens(tokens: deque[str]) -> SExpression:
    """Consumes tokens for one expression."""

    if not tokens:
        raise ValueError("unexpected end of s-expression")
    token = tokens.popleft()
    if token == "(":
        items: list[SExpression] = []
        while True:
            if not tokens:
                raise ValueError("unclosed s-expression")
            if tokens[0] == ")":
                tokens.popleft()
                return items
            items.append(_parse_tokens(tokens))
    if token == ")":
        raise ValueError("unexpected closing parenthesis")
    return token
