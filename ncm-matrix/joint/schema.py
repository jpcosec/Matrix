"""Record contract of SPEC §2: validation and the inputs/targets separation.

`supervision` reaches only the oracle and the losses. `model_inputs()` is the
single path from a record to the encoder, so nothing else can leak into it.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

MAX_TOKENS = 64
MAX_CHARS = 512
TOKEN = re.compile(r"\w+|[^\w\s]")
TRUTHS = ("true", "false", "unknown")
IDENTITY = ("same_referent", "distinct_referent")


@dataclass(frozen=True)
class Mention:
    mention_id: str
    start: int
    end: int


@dataclass(frozen=True)
class Query:
    query_id: str
    subject: str  # mention_id or full resource URI
    relation: str
    object: str


@dataclass(frozen=True)
class Assertion:
    query_id: str
    truth: str
    applicable: str  # "true" | "false" | "unknown"
    provenance: dict


@dataclass(frozen=True)
class IdentityConstraint:
    first_mention: str
    second_mention: str
    relation: str
    scope: str


@dataclass(frozen=True)
class Rule:
    formula: str  # s-expression over query ids, e.g. (if q1 q2)
    scope: str
    provenance: dict


@dataclass(frozen=True)
class Supervision:
    reference_context_id: str
    assertions: tuple[Assertion, ...]
    identity_constraints: tuple[IdentityConstraint, ...] = ()
    rules: tuple[Rule, ...] = ()
    # cost[query][profile]: 1.0 explicitly inapplicable crossing, 0.0 applicable, None unknown
    costs: tuple[tuple[float | None, ...], ...] = ()


@dataclass(frozen=True)
class Record:
    example_id: str
    source_group: str
    text: str
    observed_context: tuple[tuple[str, str], ...]
    mentions: tuple[Mention, ...]
    queries: tuple[Query, ...]
    supervision: Supervision
    split: str = "train"
    tags: dict = field(default_factory=dict)  # bookkeeping for metrics, never a feature


@dataclass(frozen=True)
class ModelInputs:
    """Everything the encoder may see. IDs of sources, examples and queries are absent."""
    text: str
    observed_context: tuple[tuple[str, str], ...]
    mention_spans: tuple[tuple[int, int], ...]
    query_structure: tuple[tuple[int | str, str, int | str], ...]  # mention index or URI


def tokenize(text: str) -> list[tuple[str, int, int]]:
    """Lower-cased word tokens with their Unicode character offsets."""
    return [(m.group().lower(), m.start(), m.end()) for m in TOKEN.finditer(text)]


def token_span(tokens: list[tuple[str, int, int]], start: int, end: int) -> tuple[int, int]:
    """Token interval [a, b) covering the character span; rejects misaligned spans."""
    covered = [i for i, (_, s, e) in enumerate(tokens) if s < end and e > start]
    if not covered:
        raise ValueError(f"span [{start},{end}) covers no token")
    a, b = covered[0], covered[-1] + 1
    if tokens[a][1] != start or tokens[b - 1][2] != end:
        raise ValueError(f"span [{start},{end}) is not aligned to token boundaries")
    return a, b


def validate(record: Record) -> Record:
    """Reject invalid spans, dangling references and over-long fragments; never truncate."""
    if len(record.text) > MAX_CHARS:
        raise ValueError(f"{record.example_id}: fragment longer than {MAX_CHARS} characters")
    tokens = tokenize(record.text)
    if len(tokens) > MAX_TOKENS:
        raise ValueError(f"{record.example_id}: {len(tokens)} tokens exceed {MAX_TOKENS}")
    ids = [m.mention_id for m in record.mentions]
    if len(set(ids)) != len(ids):
        raise ValueError(f"{record.example_id}: duplicate mention ids")
    for mention in record.mentions:
        if not 0 <= mention.start < mention.end <= len(record.text):
            raise ValueError(f"{record.example_id}: span out of range for {mention.mention_id}")
        token_span(tokens, mention.start, mention.end)
    query_ids = {q.query_id for q in record.queries}
    if len(query_ids) != len(record.queries):
        raise ValueError(f"{record.example_id}: duplicate query ids")
    for query in record.queries:
        for endpoint in (query.subject, query.object):
            if endpoint not in ids and "://" not in endpoint:
                raise ValueError(f"{record.example_id}: endpoint {endpoint} is neither mention nor URI")
    for assertion in record.supervision.assertions:
        if assertion.query_id not in query_ids:
            raise ValueError(f"{record.example_id}: assertion for unknown query")
        if assertion.truth not in TRUTHS or assertion.applicable not in TRUTHS:
            raise ValueError(f"{record.example_id}: invalid assertion labels")
    for constraint in record.supervision.identity_constraints:
        if constraint.relation not in IDENTITY:
            raise ValueError(f"{record.example_id}: invalid identity relation")
        if {constraint.first_mention, constraint.second_mention} - set(ids):
            raise ValueError(f"{record.example_id}: identity constraint on unknown mention")
    return record


def model_inputs(record: Record) -> ModelInputs:
    index = {m.mention_id: i for i, m in enumerate(record.mentions)}
    return ModelInputs(
        text=record.text,
        observed_context=record.observed_context,
        mention_spans=tuple((m.start, m.end) for m in record.mentions),
        query_structure=tuple((index.get(q.subject, q.subject), q.relation, index.get(q.object, q.object))
                              for q in record.queries),
    )
