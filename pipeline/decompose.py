"""Sentence → local `(R a b)` declarations over a chunk's own signs."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Callable

from populator.contexts import FUNCTION_WORDS, PRONOUNS, ContextIndex, LocalSign
from populator.tokenize import normalize

RELATION_FAMILIES = (
    "instance",
    "has_property",
    "born_in",
    "died_in",
    "citizen_of",
    "field",
    "award",
    "educated_at",
    "employer",
    "discovered",
    "spouse",
    "part_of",
    "causes",
    "precedes",
    "in_state",
)

FIELD_TERMS = {"physics", "chemistry", "radioactivity", "mathematics", "biology", "medicine", "astronomy"}

Backend = Callable[[str], str]

_ARTICLE_RE = re.compile(r"\s+(?:a|an|the|una|un|unos|unas|el|la|los|las)\s+", re.IGNORECASE)
_JSON_RE = re.compile(r"\[.*\]", re.DOTALL)

_EN_VERBS: list[tuple[str, str]] = [
    (r"was born in", "born_in"),
    (r"died in", "died_in"),
    (r"was awarded(?: the)?|won(?: the)?|received(?: the)?", "award"),
    (r"studied at|studied from|graduated at|graduated from", "educated_at"),
    (r"worked at|worked for|taught at|taught for", "employer"),
    (r"discovered", "discovered"),
    (r"married|was married to", "spouse"),
    (r"was|is", "copula"),
]
_ES_VERBS: list[tuple[str, str]] = [
    (r"lleva", "part_of"),
    (r"es de", "has_property"),
    (r"tiene", "has_property"),
    (r"es", "copula_es"),
]


@dataclass(frozen=True)
class Declaration:
    """One local declaration of a chunk, in terms of that chunk's symbols."""

    ctx_id: str
    relation: str
    a: str
    b: str
    a_sign: str
    b_sign: str
    sentence_index: int
    span: tuple[int, int]
    source: str = "heuristic"


def decompose(ctx: ContextIndex, lang: str = "en", backend: Backend | None = None) -> list[Declaration]:
    """Returns the heuristic declarations plus, if a backend is given, the LLM ones."""

    declarations = decompose_heuristic(ctx, lang=lang)
    if backend is not None:
        declarations += decompose_llm(ctx, backend, lang=lang)
    seen: set[tuple[str, str, str]] = set()
    unique: list[Declaration] = []
    for declaration in declarations:
        key = (declaration.relation, declaration.a, declaration.b)
        if key in seen:
            continue
        seen.add(key)
        unique.append(declaration)
    return unique


def decompose_heuristic(ctx: ContextIndex, lang: str = "en") -> list[Declaration]:
    """Extracts declarations from the sentences using only the chunk's local signs."""

    verbs = _ES_VERBS if lang == "es" else _EN_VERBS
    declarations: list[Declaration] = []
    for sentence_index, sentence in enumerate(ctx.sentences):
        pairs = _sentence_signs(ctx, sentence_index)
        if len(pairs) < 2:
            continue
        match = _match_verb(sentence.text.lower(), verbs)
        if match is None:
            declaration = _fallback(ctx, sentence_index, sentence, pairs)
            if declaration is not None:
                declarations.append(declaration)
            continue
        relation, verb_start, verb_end = match
        subject = _sign_before(pairs, sentence.char_span[0] + verb_start)
        obj = _sign_after(pairs, sentence.char_span[0] + verb_end)
        if subject is None or obj is None or subject[0] is obj[0]:
            continue
        if relation in {"copula", "copula_es"}:
            declarations.extend(_copula(sentence_index, sentence, pairs, subject, verb_end, lang))
            continue
        if relation == "part_of":
            declarations.append(_declaration(sentence_index, relation, obj, subject))
            continue
        declarations.append(_declaration(sentence_index, relation, subject, obj))
    return declarations


def decompose_llm(ctx: ContextIndex, backend: Backend, lang: str = "en") -> list[Declaration]:
    """Asks a backend for declarations, keeping only local signs and known relations."""

    reply = backend(build_prompt(ctx, lang=lang))
    match = _JSON_RE.search(reply)
    if match is None:
        return []
    try:
        payload = json.loads(match.group(0))
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, list):
        return []
    lookup = _sign_lookup(ctx)
    declarations: list[Declaration] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        relation = str(item.get("r", ""))
        if relation not in RELATION_FAMILIES and not relation.startswith("rel:"):
            continue
        a_sign = _lookup_sign(lookup, item.get("a_sign"))
        b_sign = _lookup_sign(lookup, item.get("b_sign"))
        if a_sign is None or b_sign is None or a_sign.norm == b_sign.norm:
            continue
        occurrence = a_sign.occurrences[0]
        declarations.append(
            Declaration(
                ctx_id=ctx.chunk.ctx_id,
                relation=relation,
                a=a_sign.symbol_id,
                b=b_sign.symbol_id,
                a_sign=a_sign.sign,
                b_sign=b_sign.sign,
                sentence_index=occurrence.sentence_index,
                span=(occurrence.span[0], b_sign.occurrences[0].span[1]),
                source="llm",
            )
        )
    return declarations


def build_prompt(ctx: ContextIndex, lang: str = "en") -> str:
    """Builds the decomposition prompt with the chunk's local signs."""

    sentences = "\n".join(f"[{index}] {sentence.text.strip()}" for index, sentence in enumerate(ctx.sentences))
    signs = ", ".join(sorted(sign.sign for sign in ctx.signs.values()))
    relations = ", ".join(RELATION_FAMILIES)
    return (
        "Eres un descompositor de oraciones a declaraciones lógicas locales. "
        f"Contexto: {ctx.chunk.ctx_id} ({lang}).\n"
        f"Signos locales del chunk (usa SOLO estos, tal cual): {signs}\n"
        f"Relaciones permitidas: {relations}, o bien `rel:<verbo>`.\n"
        f"Oraciones:\n{sentences}\n\n"
        "Responde SOLO un array JSON con objetos "
        '{"r": "<relación>", "a_sign": "<signo local>", "b_sign": "<signo local>"}. '
        "No inventes signos ni relaciones."
    )


def _match_verb(sentence_lower: str, verbs: list[tuple[str, str]]) -> tuple[str, int, int] | None:
    for pattern, relation in verbs:
        match = re.search(pattern, sentence_lower)
        if match:
            return relation, match.start(), match.end()
    return None


def _copula(
    sentence_index: int,
    sentence,
    pairs: list[tuple[LocalSign, tuple[int, int]]],
    subject: tuple[LocalSign, tuple[int, int]],
    verb_end: int,
    lang: str,
) -> list[Declaration]:
    article = _ARTICLE_RE.match(sentence.text, verb_end)
    phrase_offset = article.end() if article else verb_end
    phrase_start = sentence.char_span[0] + phrase_offset
    phrase = [pair for pair in pairs if pair[1][0] >= phrase_start]
    if not phrase:
        return []
    if lang == "es":
        head = phrase[0]
        relation = "instance" if head[0].kind == "name" else "has_property"
        return [_declaration(sentence_index, relation, subject, head)]
    if article is None:
        return [_declaration(sentence_index, "has_property", subject, phrase[0])]
    head = phrase[-1]
    head_norm = normalize(head[0].sign)
    declarations = [_declaration(sentence_index, "instance", subject, head)]
    for modifier in phrase[:-1]:
        if not _is_modifier(modifier[0]):
            continue
        declarations.append(_declaration(sentence_index, "has_property", subject, modifier))
        if normalize(modifier[0].sign) in FIELD_TERMS and head_norm in {"physicist", "chemist"}:
            declarations.append(_declaration(sentence_index, "field", subject, modifier))
    return declarations


def _is_modifier(sign: LocalSign) -> bool:
    """Adjectives and demonyms modify the head of the copula noun phrase."""

    return sign.kind == "term" or (sign.kind == "name" and " " not in sign.norm)


def _fallback(
    ctx: ContextIndex,
    sentence_index: int,
    sentence,
    pairs: list[tuple[LocalSign, tuple[int, int]]],
) -> Declaration | None:
    subject = pairs[0]
    skip = FUNCTION_WORDS["es"] | FUNCTION_WORDS["en"] | PRONOUNS
    sign_norms = {sign.norm for sign in ctx.signs.values()}
    for match in re.finditer(r"[^\W\d_]+", sentence.text):
        if sentence.char_span[0] + match.end() <= subject[1][1]:
            continue
        word = match.group(0).lower()
        if word in skip or normalize(word) in sign_norms:
            continue
        obj = _sign_after(pairs, sentence.char_span[0] + match.end())
        if obj is None or obj[0] is subject[0]:
            continue
        return _declaration(sentence_index, f"rel:{_lemma(word)}", subject, obj)
    return None


def _lemma(word: str) -> str:
    lowered = normalize(word)
    for suffix in ("ing", "ed", "es", "s"):
        if lowered.endswith(suffix) and len(lowered) - len(suffix) >= 3:
            return lowered[: -len(suffix)]
    return lowered


def _declaration(
    sentence_index: int,
    relation: str,
    subject: tuple[LocalSign, tuple[int, int]],
    obj: tuple[LocalSign, tuple[int, int]],
) -> Declaration:
    return Declaration(
        ctx_id=subject[0].ctx_id,
        relation=relation,
        a=subject[0].symbol_id,
        b=obj[0].symbol_id,
        a_sign=subject[0].sign,
        b_sign=obj[0].sign,
        sentence_index=sentence_index,
        span=(subject[1][0], obj[1][1]),
    )


def _sentence_signs(ctx: ContextIndex, sentence_index: int) -> list[tuple[LocalSign, tuple[int, int]]]:
    pairs: list[tuple[LocalSign, tuple[int, int]]] = []
    for sign in ctx.signs_in(sentence_index):
        span = next((occurrence.span for occurrence in sign.occurrences if occurrence.sentence_index == sentence_index), None)
        if span is not None:
            pairs.append((sign, span))
    pairs.sort(key=lambda pair: pair[1][0])
    return pairs


def _sign_before(
    pairs: list[tuple[LocalSign, tuple[int, int]]],
    position: int,
) -> tuple[LocalSign, tuple[int, int]] | None:
    candidates = [pair for pair in pairs if pair[1][1] <= position]
    return candidates[-1] if candidates else None


def _sign_after(
    pairs: list[tuple[LocalSign, tuple[int, int]]],
    position: int,
) -> tuple[LocalSign, tuple[int, int]] | None:
    for pair in pairs:
        if pair[1][0] >= position:
            return pair
    return None


def _sign_lookup(ctx: ContextIndex) -> dict[str, LocalSign]:
    lookup: dict[str, LocalSign] = {}
    for sign in ctx.signs.values():
        lookup[normalize(sign.sign)] = sign
        lookup[sign.norm] = sign
        lookup[sign.symbol_id] = sign
    return lookup


def _lookup_sign(lookup: dict[str, LocalSign], value: object) -> LocalSign | None:
    if not isinstance(value, str):
        return None
    return lookup.get(value) or lookup.get(normalize(value))
