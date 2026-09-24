"""UNL (Universal Networking Language) graph data model.

A UNL expression is a hypergraph consisting of:

* **Universal Words** (UWs) -- concept nodes with optional constraints.
* **Semantic relations** -- directed labelled edges between UWs
  (e.g. ``agt``, ``obj``, ``mod``, ``tim``, ...).
* **Attributes** -- node-level properties (e.g. ``@entry``, ``@topic``, ...).
"""

from __future__ import annotations

import dataclasses
import re
from collections.abc import Sequence

# -- Relation type catalogue (most common) -------------------------------

UNL_RELATIONS: dict[str, str] = {
    # ── top-level ────────────────────────────────────────────────
    "agt": "agent",
    "and": "conjunction",
    "aoj": "attribute-of-object",
    "ben": "beneficiary",
    "cnt": "content",
    "con": "condition",
    "dur": "duration",
    "exp": "experiencer",
    "man": "manner",
    "mod": "modifier",
    "obj": "patient",
    "or": "disjunction",
    "per": "proportion",
    "plc": "place",
    "ptn": "partner",
    "rsn": "reason",
    "seq": "consequence",
    "tim": "time",
    # ── sub-relations of aoj (object of attribute) ───────────────
    "ant": "antonym",
    "equ": "equivalent",
    "fld": "field",
    "icl": "subclass",
    "iof": "instance",
    "pof": "part-of",
    # ── sub-relations of mod (modifier) ──────────────────────────
    "mat": "material",
    "nam": "name",
    "pos": "possession",
    "qua": "quantity",
    # ── sub-relations of obj (patient) ───────────────────────────
    "opl": "objective-place",
    "res": "result",
    # ── sub-relations of plc (place) ─────────────────────────────
    "gol": "goal",
    "lpl": "logical-place",
    "src": "source",
    "via": "medium",
    # ── sub-relations of tim (time) ──────────────────────────────
    "coo": "co-occurrence",
    "tmf": "initial-time",
    "tmt": "final-time",
    # ── sub-relations of man (manner) ───────────────────────────
    "ins": "instrument",
    "met": "method",
    "pur": "purpose",
    # ── sub-relations of per (proportion) ────────────────────────
    "bas": "basis",
    # ── other ────────────────────────────────────────────────────
    "cag": "co-agent",
    "coa": "co-after",
    "cob": "co-before",
    "fmt": "format",
    "plf": "plurality-form",
    "scn": "scene",
    "to": "destination",
    "frm": "origin",
}

# Hierarchy: maps each relation to its parent (None for top-level)
_REL_HIERARCHY: dict[str, str | None] = {
    "ant": "aoj", "equ": "aoj", "fld": "aoj", "icl": "aoj", "iof": "aoj", "pof": "aoj",
    "mat": "mod", "nam": "mod", "pos": "mod", "qua": "mod",
    "opl": "obj", "res": "obj",
    "gol": "plc", "lpl": "plc", "src": "plc", "via": "plc",
    "coo": "tim", "tmf": "tim", "tmt": "tim",
    "ins": "man", "met": "man", "pur": "man",
    "bas": "per",
}


@dataclasses.dataclass(frozen=True)
class UniversalWord:
    """A concept node in a UNL graph.

    Attributes:
        id: Unique identifier within the graph.
        concept: The concept label (e.g. ``"eat"``, ``"dog"``).
        constraints: Optional parenthesised constraint string.
        attributes: Set of node-level attributes (``@entry``, ...).
    """

    id: str
    concept: str
    constraints: str = ""
    attributes: frozenset[str] = dataclasses.field(default_factory=frozenset)

    @property
    def label(self) -> str:
        return self.concept

    def __repr__(self) -> str:
        attrs = f" [{', '.join(sorted(self.attributes))}]" if self.attributes else ""
        return f"{self.concept}{self.constraints}{attrs}"


@dataclasses.dataclass(frozen=True)
class UNLRelation:
    """A directed labelled edge between two Universal Words.

    Attributes:
        type: Relation type (``"agt"``, ``"obj"``, ...).
        source: UW id of the source node.
        target: UW id of the target node.
        scope: Optional scope identifier (e.g. ``"01"``).
    """

    type: str
    source: str
    target: str
    scope: str = "00"

    @property
    def label(self) -> str:
        return UNL_RELATIONS.get(self.type, self.type)

    @property
    def parent(self) -> str | None:
        return _REL_HIERARCHY.get(self.type)


# -- Graph ---------------------------------------------------------------


_ATTR_LINE = re.compile(r"@(?P<attr>[a-z][\w.-]*)(?:\([^)]*\))?")
_REL_LINE = re.compile(
    r"(?P<rel>[a-z]{2,4})"
    r"(?::(?P<scope>[a-z0-9]+))?"        # optional scope
    r"\((?P<src>[^,{]+?)\s*,\s*(?P<tgt>[^)]+?)\)"
)


class UNLGraph:
    """A UNL semantic hypergraph.

    .. code-block:: text

        agt(eat, dog)
        obj(eat, food)
        @entry.eat
    """

    def __init__(
        self,
        relations: Sequence[UNLRelation] = (),
        words: Sequence[UniversalWord] = (),
        entry_word_id: str | None = None,
    ) -> None:
        self._relations: list[UNLRelation] = list(relations)
        self._words: dict[str, UniversalWord] = {w.id: w for w in words}
        self._entry_word_id = entry_word_id

    # -- accessors -------------------------------------------------------

    @property
    def relations(self) -> list[UNLRelation]:
        return list(self._relations)

    @property
    def words(self) -> list[UniversalWord]:
        return list(self._words.values())

    @property
    def entry_word_id(self) -> str | None:
        return self._entry_word_id

    def word(self, word_id: str) -> UniversalWord | None:
        return self._words.get(word_id)

    def add_word(self, word: UniversalWord) -> None:
        self._words[word.id] = word

    def add_relation(self, relation: UNLRelation) -> None:
        self._relations.append(relation)

    def relations_for(self, word_id: str) -> list[UNLRelation]:
        return [
            r for r in self._relations
            if word_id in (r.source, r.target)
        ]

    # -- construction helpers --------------------------------------------

    @classmethod
    def from_triples(
        cls,
        triples: Sequence[tuple[str, str, str]],
        attributes: dict[str, Sequence[str]] | None = None,
    ) -> UNLGraph:
        """Build a UNLGraph from bare triples ``(rel, source, target)``."""
        words: dict[str, UniversalWord] = {}
        relations: list[UNLRelation] = []

        for rel, src, tgt in triples:
            for cid, _ in ((src, src), (tgt, tgt)):
                if cid not in words:
                    words[cid] = UniversalWord(id=cid, concept=cid)
            relations.append(UNLRelation(type=rel, source=src, target=tgt))

        entry = None
        if attributes:
            for cid, raw_attrs in attributes.items():
                attr_set = set(raw_attrs)
                if "@entry" in attr_set:
                    entry = cid
                existing = words.get(cid, UniversalWord(id=cid, concept=cid))
                words[cid] = dataclasses.replace(
                    existing, attributes=frozenset(attr_set)
                )

        return cls(relations=relations, words=list(words.values()), entry_word_id=entry)

    # -- UNL text format -------------------------------------------------

    @classmethod
    def from_unl_text(cls, text: str) -> UNLGraph:
        """Parse a UNL text snippet into a ``UNLGraph``.

        Supports the classic UNL line format::

            agt(eat, dog)
            obj(eat, food)
            @entry.eat
            agt:01(kill, Peter)
        """
        words: dict[str, UniversalWord] = {}
        relations: list[UNLRelation] = []
        attributes: dict[str, set[str]] = {}
        entry: str | None = None

        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or line.startswith("//"):
                continue

            if line.startswith("@"):
                _parse_attribute_line(line, attributes, words)
                continue

            m = _REL_LINE.match(line)
            if m:
                rel = m.group("rel")
                scope = m.group("scope") or "00"
                src = m.group("src").strip()
                tgt = m.group("tgt").strip()
                relations.append(
                    UNLRelation(type=rel, source=src, target=tgt, scope=scope)
                )
                for cid, concept in ((src, src), (tgt, tgt)):
                    if cid not in words:
                        words[cid] = UniversalWord(id=cid, concept=concept)

        # detect entry from attributes
        for cid, attrs in attributes.items():
            if "@entry" in attrs:
                entry = cid

        final_words = _apply_attributes(words, attributes)
        return cls(relations=relations, words=final_words, entry_word_id=entry)

    def to_unl_text(self) -> str:
        """Serialize this graph to classic UNL text format."""
        rel_lines = [
            f"{rel.type}({rel.source}, {rel.target})"
            for rel in self._relations
        ]
        attr_lines = [
            f"@{attr.lstrip('@')}.{wid}"
            for wid, word in self._words.items()
            for attr in sorted(word.attributes)
        ]
        all_lines = rel_lines + attr_lines
        return "\n".join(all_lines) + "\n" if all_lines else ""

    def __repr__(self) -> str:
        return (
            f"UNLGraph(words={len(self._words)}, "
            f"relations={len(self._relations)}, "
            f"entry={self._entry_word_id})"
        )


# -- module-level helpers (extracted for complexity) ----------------------


def _parse_attribute_line(
    line: str,
    attributes: dict[str, set[str]],
    words: dict[str, UniversalWord],
) -> None:
    """Parse a ``@attr.word`` line and update state."""
    parts = line.split(".")
    if len(parts) != 2:  # noqa: PLR2004
        return
    attr = parts[0].lstrip("@")
    word_id = parts[1].strip().rstrip(")")
    attributes.setdefault(word_id, set()).add(f"@{attr}")
    if word_id not in words:
        words[word_id] = UniversalWord(id=word_id, concept=word_id)


def _apply_attributes(
    words: dict[str, UniversalWord],
    attributes: dict[str, set[str]],
) -> list[UniversalWord]:
    """Merge attributes into word dataclasses."""
    result: list[UniversalWord] = []
    for cid, w in words.items():
        if cid in attributes:
            updated = dataclasses.replace(w, attributes=frozenset(attributes[cid]))
        else:
            updated = w
        result.append(updated)
    return result
