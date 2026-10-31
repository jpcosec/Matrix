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
_NP_TOKEN_RE = re.compile(r"[^\W\d_]+|,")
_NP_STOPWORDS = {
    "to", "who", "whom", "whose", "that", "which",
    "in", "on", "at", "of", "for", "with", "from", "by", "during", "after", "before",
    "near", "under", "over", "into", "about", "against", "between", "through", "as", "than",
}
_VERB_SUFFIXES = ("ed", "ing", "s")
_IRREGULAR_VERBS = {
    "was", "is", "has", "had", "made", "won", "led", "found", "taught", "wrote", "built",
    "left", "gave", "took", "ran", "held", "met", "did", "said", "saw", "knew", "became",
    "began", "brought", "chose", "sent", "set", "spent", "stood", "told", "thought",
    "understood", "spoke", "shared", "ve", "va", "da", "ha", "son",
}
_JSON_RE = re.compile(r"\[.*\]", re.DOTALL)

_EN_VERBS: list[tuple[str, str]] = [
    (r"was born(?: on| in)?\s+[^,]*?\s+in", "born_in"),
    (r"was born[^,]*?,\s*in", "born_in"),
    (r"was born in", "born_in"),
    (r"died(?: on| in)?\s+[^,]*?\s+in", "died_in"),
    (r"died[^,]*?,\s*in", "died_in"),
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
        found = _sentence_declarations(sentence_index, sentence, pairs, verbs, lang)
        if found:
            declarations.extend(found)
            continue
        declaration = _fallback(ctx, sentence_index, sentence, pairs)
        if declaration is not None:
            declarations.append(declaration)
    return declarations


def _sentence_declarations(
    sentence_index: int,
    sentence,
    pairs: list[tuple[LocalSign, tuple[int, int]]],
    verbs: list[tuple[str, str]],
    lang: str,
) -> list[Declaration]:
    """Reads up to three clauses of one sentence, earliest verb first."""

    declarations: list[Declaration] = []
    search_from = 0
    for _ in range(3):
        match = _match_verb(sentence.text[search_from:].lower(), verbs)
        if match is None:
            break
        relation = match[0]
        verb_start = search_from + match[1]
        verb_end = search_from + match[2]
        search_from = verb_end
        subject = _subject_before(pairs, sentence.char_span[0] + verb_start)
        obj = _sign_after(pairs, sentence.char_span[0] + verb_end)
        if subject is None or obj is None or subject[0] is obj[0]:
            continue
        if relation in {"copula", "copula_es"}:
            declarations.extend(_copula(sentence_index, sentence, pairs, subject, verb_end, lang))
            continue
        if relation == "part_of":
            declarations.append(_declaration(sentence_index, relation, obj, subject))
            continue
        declaration = _declaration(sentence_index, relation, subject, obj)
        declarations.append(declaration)
        if relation == "award" and "nobel prize" in normalize(declaration.b_sign):
            canonical = _canonical_sign(subject, "nobel_prize", sentence_index, declaration)
            if canonical is not None:
                declarations.append(canonical)
    return declarations


def _canonical_sign(
    subject: tuple[LocalSign, tuple[int, int]],
    norm: str,
    sentence_index: int,
    declaration: Declaration,
) -> Declaration | None:
    """Adds the canonical object variant (e.g. `nobel_prize` for `Nobel Prize in Physics`)."""

    if norm == declaration.b:
        return None
    return Declaration(
        ctx_id=declaration.ctx_id,
        relation=declaration.relation,
        a=declaration.a,
        b=f"{norm}@{declaration.ctx_id}",
        a_sign=declaration.a_sign,
        b_sign=norm.replace("_", " "),
        sentence_index=sentence_index,
        span=declaration.span,
        source=declaration.source,
    )


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
        relation = str(item.get("r", "")).strip()
        if relation not in RELATION_FAMILIES and not relation.startswith("rel:"):
            continue
        if not _is_atom(relation):
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


def decompose_llm_chunk(
    ctx: ContextIndex,
    backend: Backend,
    lang: str = "en",
    attempts: int = 2,
) -> list[Declaration]:
    """Asks a backend for one chunk's declarations, once per chunk.

    The model is a surface decomposer: it may only use the chunk's own signs
    (pronouns included), may not resolve pronouns, and may not invent relations
    outside `RELATION_FAMILIES` or `rel:<verb>`. Invalid triples are dropped.
    """

    prompt = build_chunk_prompt(ctx, lang=lang)
    payload: list[Any] | None = None
    for _ in range(max(attempts, 1)):
        reply = backend(prompt)
        payload = _parse_json_list(reply)
        if payload is not None:
            break
    if not payload:
        return []
    lookup = _sign_lookup(ctx)
    declarations: list[Declaration] = []
    for item in payload:
        declaration = _declaration_from_item(ctx, lookup, item)
        if declaration is not None:
            declarations.append(declaration)
    return declarations


def _parse_json_list(reply: str) -> list[Any] | None:
    """Parses the first JSON array in a reply, tolerating surrounding prose."""

    match = _JSON_RE.search(reply)
    if match is None:
        return None
    try:
        payload = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, list) else None


def _declaration_from_item(
    ctx: ContextIndex,
    lookup: dict[str, LocalSign],
    item: object,
) -> Declaration | None:
    """Validates one model triple against the chunk's own signs and relations."""

    if not isinstance(item, dict):
        return None
    relation = str(item.get("r", "")).strip()
    if relation not in RELATION_FAMILIES and not relation.startswith("rel:"):
        return None
    if not _is_atom(relation):
        return None
    a_sign = _lookup_sign(lookup, item.get("a_sign"))
    b_sign = _lookup_sign(lookup, item.get("b_sign"))
    if a_sign is None or b_sign is None or a_sign.norm == b_sign.norm:
        return None
    default_sentence = a_sign.occurrences[0].sentence_index if a_sign.occurrences else 0
    try:
        sentence_index = int(item.get("s", default_sentence))
    except (TypeError, ValueError):
        sentence_index = default_sentence
    span = _sentence_span(ctx, sentence_index, a_sign, b_sign)
    return Declaration(
        ctx_id=ctx.chunk.ctx_id,
        relation=relation,
        a=a_sign.symbol_id,
        b=b_sign.symbol_id,
        a_sign=a_sign.sign,
        b_sign=b_sign.sign,
        sentence_index=sentence_index,
        span=span,
        source="llm",
    )


def _sentence_span(
    ctx: ContextIndex,
    sentence_index: int,
    a_sign: LocalSign,
    b_sign: LocalSign,
) -> tuple[int, int]:
    for sentence in ctx.sentences:
        if sentence.index == sentence_index:
            return sentence.char_span
    spans = [occurrence.span for sign in (a_sign, b_sign) for occurrence in sign.occurrences]
    if spans:
        return (spans[0][0], spans[-1][1])
    return (0, 0)


def build_chunk_prompt(ctx: ContextIndex, lang: str = "en") -> str:
    """Builds the one-call-per-chunk decomposition prompt."""

    sentences = "\n".join(f"[{index}] {sentence.text.strip()}" for index, sentence in enumerate(ctx.sentences))
    signs = "\n".join(
        f"- symbol_id={sign.symbol_id} sign={sign.sign!r} kind={sign.kind}"
        for sign in sorted(ctx.signs.values(), key=lambda sign: sign.symbol_id)
    )
    relations = ", ".join(RELATION_FAMILIES)
    return (
        "Eres un descompositor de superficie. Convierte las oraciones en tripletas lógicas "
        "usando SOLO los signos locales listados.\n"
        f"Contexto: {ctx.chunk.ctx_id} — {ctx.chunk.title} ({lang})\n"
        f"Signos locales:\n{signs}\n"
        f"Relaciones permitidas: {relations}, o `rel:<verbo en infinitivo>`.\n"
        f"Oraciones:\n{sentences}\n\n"
        "Reglas: (1) usa SOLO los signos de la lista; los pronombres (she, he) son signos válidos; "
        "(2) NO resuelvas pronombres; (3) no inventes relaciones fuera de las familias salvo "
        "`rel:<verbo en infinitivo>`; (4) una tripleta por hecho; (5) el objeto es el signo más largo "
        "disponible (por ejemplo `nobel prize in physics` mejor que `nobel prize`), y añade además la "
        "variante canónica `nobel prize` cuando exista como signo.\n"
        'Responde SOLO un array JSON: [{"s": <nº de oración>, "r": "<relación>", '
        '"a_sign": "<signo local>", "b_sign": "<signo local>"}].'
    )


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
    """Finds the earliest verb pattern on word boundaries.

    Order matters inside a sentence ("X was a chemist who won the Nobel Prize"):
    the earliest verb wins, and the pattern list only breaks ties at the same
    position.
    """

    best: tuple[str, int, int] | None = None
    for pattern, relation in verbs:
        match = re.search(rf"\b(?:{pattern})\b", sentence_lower)
        if match is None:
            continue
        candidate = (relation, match.start(), match.end())
        if best is None or candidate[1] < best[1]:
            best = candidate
    return best


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
    phrase_end = sentence.char_span[0] + _noun_phrase_end(sentence.text, phrase_offset)
    phrase = [pair for pair in pairs if phrase_start <= pair[1][0] and pair[1][1] <= phrase_end]
    if not phrase:
        return []
    if lang == "es":
        head = phrase[0]
        relation = "instance" if head[0].kind == "name" else "has_property"
        return [_declaration(sentence_index, relation, subject, head)]
    if article is None:
        return [_declaration(sentence_index, "has_property", subject, phrase[0])]
    units = _split_terms(phrase, sentence, subject[0].ctx_id)
    head = units[-1]
    head_norm = normalize(head[0].sign)
    declarations = [_declaration(sentence_index, "instance", subject, head)]
    for modifier in units[:-1]:
        if not _is_modifier(modifier[0]):
            continue
        declarations.append(_declaration(sentence_index, "has_property", subject, modifier))
        if normalize(modifier[0].sign) in FIELD_TERMS and head_norm in {"physicist", "chemist"}:
            declarations.append(_declaration(sentence_index, "field", subject, modifier))
    return declarations


def _split_terms(
    phrase: list[tuple[LocalSign, tuple[int, int]]],
    sentence,
    ctx_id: str,
) -> list[tuple[LocalSign, tuple[int, int]]]:
    """Splits multi-token term signs so the head is the last nominal token."""

    units: list[tuple[LocalSign, tuple[int, int]]] = []
    base = sentence.char_span[0]
    for sign, span in phrase:
        if sign.kind != "term" or len(sign.norm.split()) <= 1:
            units.append((sign, span))
            continue
        surface = sentence.text[span[0] - base : span[1] - base]
        cursor = 0
        for word in surface.split():
            index = surface.index(word, cursor)
            cursor = index + len(word)
            units.append(
                (
                    LocalSign(sign=word, norm=normalize(word), ctx_id=ctx_id, kind="term"),
                    (span[0] + index, span[0] + cursor),
                )
            )
    return units


def _noun_phrase_end(text: str, start: int) -> int:
    """Returns where the copula noun phrase ends: preposition, `to`, relative or comma."""

    for match in _NP_TOKEN_RE.finditer(text, start):
        token = match.group(0)
        if token == "," or token.lower() in _NP_STOPWORDS:
            return match.start()
    return len(text)


def _is_atom(token: str) -> bool:
    """Reports whether a token can be written as a single s-expression atom."""

    return bool(token) and not any(char.isspace() or char in "()" for char in token)


def _is_modifier(sign: LocalSign) -> bool:
    """Adjectives and demonyms modify the head of the copula noun phrase."""

    return sign.kind == "term" or (sign.kind == "name" and " " not in sign.norm)


def _fallback(
    ctx: ContextIndex,
    sentence_index: int,
    sentence,
    pairs: list[tuple[LocalSign, tuple[int, int]]],
) -> Declaration | None:
    """Emits `rel:<lemma>` only for a plausible verb outside any name sign."""

    subject = pairs[0]
    skip = FUNCTION_WORDS["es"] | FUNCTION_WORDS["en"] | PRONOUNS
    name_spans = [(pair[1][0], pair[1][1]) for pair in pairs if pair[0].kind == "name"]
    for match in re.finditer(r"[^\W\d_]+", sentence.text):
        start = sentence.char_span[0] + match.start()
        end = sentence.char_span[0] + match.end()
        if end <= subject[1][1]:
            continue
        word = match.group(0).lower()
        if word in skip:
            continue
        if any(name_start <= start and end <= name_end for name_start, name_end in name_spans):
            continue
        if not _is_plausible_verb(word):
            continue
        obj = _sign_after(pairs, end)
        if obj is None or obj[0] is subject[0]:
            continue
        return _declaration(sentence_index, f"rel:{_lemma(word)}", subject, obj)
    return None


def _is_plausible_verb(word: str) -> bool:
    """Accepts only verb-looking tokens: irregular list or an -ed/-s/-ing ending."""

    if word in _IRREGULAR_VERBS:
        return True
    return len(word) > 3 and word.endswith(_VERB_SUFFIXES)


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


def _subject_before(
    pairs: list[tuple[LocalSign, tuple[int, int]]],
    position: int,
) -> tuple[LocalSign, tuple[int, int]] | None:
    """Returns the subject sign: the last name/pronoun before the verb, else any sign."""

    candidates = [pair for pair in pairs if pair[1][1] <= position]
    if not candidates:
        return None
    named = [pair for pair in candidates if pair[0].kind in {"name", "pronoun"}]
    return (named or candidates)[-1]


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
