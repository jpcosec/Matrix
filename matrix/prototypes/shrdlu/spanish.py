"""Controlled-Spanish parsing for the SHRDLU REPL, mapped to S-expressions."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from itertools import product
from typing import TYPE_CHECKING

from populator.tokenize import normalize

if TYPE_CHECKING:
    from .dialog_state import DialogState

VERBS = "implica|tiene|es|lleva"
_ARTICLE = r"(?:la|el|los|las|un|una|unos|unas)\s+"
_CHECK_RE = re.compile(rf"^(?:{_ARTICLE})?(.+?)\s+({VERBS})\s+(?:{_ARTICLE})?(.+)$")
_WHY_RE = re.compile(rf"^(?:por que|porque)\s+(?:{_ARTICLE})?(.+?)\s+({VERBS})\s+(?:{_ARTICLE})?(.*)$")
_RETRACT_RE = re.compile(rf"^(?:{_ARTICLE})?(.+?)\s+ya no\s+({VERBS})\s+(?:{_ARTICLE})?(.+)$")
_DEFINE_RE = re.compile(rf"^si\s+(?:{_ARTICLE})?(.+?)\s+({VERBS})\s+(?:{_ARTICLE})?(.+?)\s+entonces\s+(?:{_ARTICLE})?(.+?)\s+({VERBS})\s+(?:{_ARTICLE})?(.+)$")
_DEFINE_AND_RE = re.compile(
    rf"^si\s+(?:{_ARTICLE})?(.+?)\s+({VERBS})\s+(?:{_ARTICLE})?(.+?)\s+y\s+"
    rf"(?:{_ARTICLE})?(.+?)\s+({VERBS})\s+(?:{_ARTICLE})?(.+?)\s+entonces\s+"
    rf"(?:{_ARTICLE})?(.+?)\s+({VERBS})\s+(?:{_ARTICLE})?(.+)$"
)
_ELLIPSIS_RE = re.compile(rf"^y\s+(?:{_ARTICLE})?(.+)$")
_REJECT_RE = re.compile(r"^rechaza\s+(\S+)\s+(.+)$")
_PROMOTE_RE = re.compile(r"^aprueba\s+(\S+)$")
_TELL_RE = re.compile(r"^tell foco\s+(\S+)$")


@dataclass(frozen=True)
class Clarification:
    """A question with ready-to-run s-expression options."""

    question: str
    options: list[str]


def fold(text: str) -> str:
    """Lowercases and strips accents while keeping ids, spaces and colons."""

    decomposed = unicodedata.normalize("NFKD", text)
    lowered = "".join(char for char in decomposed if not unicodedata.combining(char)).lower()
    return "".join(char for char in lowered if char.isalnum() or char in " _-:")


def parse_es(text: str, dialog: "DialogState") -> str | Clarification:
    """Parses one Spanish line into a runtime s-expression or a clarification."""

    raw = text.strip()
    if not raw:
        raise ValueError("empty line")
    question = raw.startswith("¿") or raw.endswith("?")
    norm = fold(raw)

    if norm in {"candidatos", "show candidatos"}:
        return f"(return candidates {_focus(dialog)} curation:proposed)"
    if norm == "show wigame":
        return f"(return facts {_focus(dialog)})"

    match = _PROMOTE_RE.fullmatch(norm)
    if match:
        return f"(promote {match.group(1)})"
    match = _REJECT_RE.fullmatch(norm)
    if match:
        return f'(reject {match.group(1)} "{match.group(2)}")'
    match = _TELL_RE.fullmatch(norm)
    if match:
        dialog.focus_wigame = match.group(1)
        return f"(return facts {_focus(dialog)})"

    match = _WHY_RE.fullmatch(norm)
    if match:
        return _build("why", match.group(1), match.group(3) or dialog.last_object, dialog)

    match = _DEFINE_AND_RE.fullmatch(norm)
    if match:
        subject, first, second = match.group(1), match.group(3), match.group(6)
        left, right = match.group(4), match.group(7)
        object_third = match.group(9)
        if subject != left or subject != right:
            raise ValueError("conjunctive define expects the same subject everywhere")
        return _build_define_and(subject, first, second, object_third, dialog)

    match = _DEFINE_RE.fullmatch(norm)
    if match:
        subject, first_object = match.group(1), match.group(3)
        second_subject, second_object = match.group(4), match.group(6)
        if subject != second_subject:
            raise ValueError("define expects the same subject on both sides")
        return _build_define(subject, first_object, second_object, dialog)

    match = _RETRACT_RE.fullmatch(norm)
    if match:
        return _build("retract", match.group(1), match.group(3), dialog)

    match = _ELLIPSIS_RE.fullmatch(norm)
    if match and dialog.last_subject is not None:
        verb = dialog.last_verb or "check"
        if verb in {"why", "assert", "retract", "check"}:
            return _build(verb, dialog.last_subject, match.group(1), dialog)

    match = _CHECK_RE.fullmatch(norm)
    if match:
        return _build("check" if question else "assert", match.group(1), match.group(3), dialog)

    raise ValueError(f"no entiendo: {text!r}")


def _focus(dialog: "DialogState") -> str:
    return dialog.focus_wigame or "wigame:vegetales"


def _build(verb: str, subject_sign: str, object_sign: str, dialog: "DialogState") -> str | Clarification:
    subjects = _symbols_for(subject_sign, dialog)
    objects = _symbols_for(object_sign, dialog)
    unknown = [sign for sign, found in ((subject_sign, subjects), (object_sign, objects)) if not found]
    subjects = subjects or [_literal(subject_sign)]
    objects = objects or [_literal(object_sign)]
    combinations = list(product(subjects, objects))
    if len(combinations) == 1 and not unknown:
        subject, obj = combinations[0]
        dialog.remember_turn(verb, subject, obj)
        return _render(verb, subject, obj, dialog)
    labels = [f"{first} + {second}" for first, second in combinations]
    options = [_render(verb, subject, obj, dialog) for subject, obj in combinations]
    return Clarification(question=_question(subject_sign, object_sign, labels, unknown), options=options)


def _build_define(
    subject_sign: str,
    first_object: str,
    second_object: str,
    dialog: "DialogState",
) -> str | Clarification:
    subjects = _symbols_for(subject_sign, dialog) or [_literal(subject_sign)]
    firsts = _symbols_for(first_object, dialog) or [_literal(first_object)]
    seconds = _symbols_for(second_object, dialog) or [_literal(second_object)]
    combinations = list(product(subjects, firsts, seconds))
    if len(combinations) == 1:
        subject, first, second = combinations[0]
        return f"(define (if (implies {subject} {first}) (implies {subject} {second})))"
    labels = [f"{subject} + {first} + {second}" for subject, first, second in combinations]
    question = _question(subject_sign, second_object, labels, [])
    options = [
        f"(define (if (implies {subject} {first}) (implies {subject} {second})))"
        for subject, first, second in combinations
    ]
    return Clarification(question=question, options=options)


def _build_define_and(
    subject_sign: str,
    first_object: str,
    second_object: str,
    third_object: str,
    dialog: "DialogState",
) -> str | Clarification:
    subjects = _symbols_for(subject_sign, dialog) or [_literal(subject_sign)]
    firsts = _symbols_for(first_object, dialog) or [_literal(first_object)]
    seconds = _symbols_for(second_object, dialog) or [_literal(second_object)]
    thirds = _symbols_for(third_object, dialog) or [_literal(third_object)]
    combinations = list(product(subjects, firsts, seconds, thirds))
    if len(combinations) == 1:
        subject, first, second, third = combinations[0]
        return _render_define_and(subject, first, second, third)
    labels = [" + ".join(combo) for combo in combinations]
    question = _question(subject_sign, third_object, labels, [])
    return Clarification(
        question=question,
        options=[_render_define_and(*combo) for combo in combinations],
    )


def _render_define_and(subject: str, first: str, second: str, third: str) -> str:
    return (
        f"(define (if (and (implies {subject} {first}) (implies {subject} {second})) "
        f"(implies {subject} {third})))"
    )


def _render(verb: str, subject: str, obj: str, dialog: "DialogState") -> str:
    focus = _focus(dialog)
    if verb == "why":
        return f"(why {focus} (implies {subject} {obj}))"
    if verb == "retract":
        return f"(retract {focus} (implies {subject} {obj}))"
    if verb == "assert":
        return f"(assert {focus} (implies {subject} {obj}))"
    return f"(check {focus} (implies {subject} {obj}))"


def _question(subject_sign: str, object_sign: str, labels: list[str], unknown: list[str]) -> str:
    options = " | ".join(f"{index + 1}) {label}" for index, label in enumerate(labels))
    if unknown:
        return f"«{', '.join(unknown)}» no está en el vocabulario (¿{subject_sign} / {object_sign}?): {options}. ¿Cuál? [1-{len(labels)}]"
    return f"«{subject_sign} / {object_sign}» es ambiguo: {options}. ¿Cuál? [1-{len(labels)}]"


def _literal(sign: str) -> str:
    return normalize(sign).replace(" ", "_")


def _symbols_for(sign: str, dialog: "DialogState") -> list[str]:
    """Resolves a normalized sign against the registered symbols."""

    needle = normalize(sign)
    keys = {needle, needle.replace(" ", "_")}
    if dialog.system is None:
        return [needle.replace(" ", "_")]
    matches: list[str] = []
    for symbol in dialog.system.symbols.values():
        for candidate in symbol.signs:
            folded = normalize(candidate)
            if keys & {folded, folded.replace(" ", "_")}:
                matches.append(symbol.symbol_id)
                break
    return sorted(set(matches))
