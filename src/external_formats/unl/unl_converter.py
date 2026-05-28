"""UNL -> Matrix s-expression converter.

Translates a UNL semantic graph into a sequence of s-expressions that
can be evaluated by ``SExpressionRuntime``.

Pipeline
--------
UNL graph  -->  S-expressions  -->  SExpressionRuntime.evaluate()

Mapping
-------
UNL relation               Matrix s-expression
--------------------------------------------------------------
agt(eat, dog)              ->  (ingest wigame:unl (agent eat dog))
obj(eat, food)             ->  (ingest wigame:unl (object eat food))
@entry.eat                 ->  (assert wigame:unl (entry eat))
tim(eat, yesterday)        ->  (ingest wigame:unl (time eat yesterday))
equ(dog, canine)           ->  (assert wigame:unl (equivalent dog canine))
icl(dog, mammal)           ->  (ingest wigame:unl (subclass dog mammal))
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import NamedTuple

from .unl_graph import UNLGraph

# Minimum tokens for an ingest/assert sexpr
_MIN_TOKENS = 4


# Mapping from UNL relation types to canonical Matrix relation IDs.
# Includes all 46 standard UNL relations from the official spec.
_UNL_TO_MATRIX_REL: dict[str, str] = {
    "agt": "agent",
    "and": "conjunction",
    "ant": "antonym",
    "aoj": "attribute",
    "bas": "basis",
    "ben": "beneficiary",
    "cag": "co-agent",
    "cnt": "content",
    "coa": "co-after",
    "cob": "co-before",
    "con": "condition",
    "coo": "co-occurrence",
    "dur": "duration",
    "equ": "equivalent",
    "exp": "experiencer",
    "fld": "field",
    "fmt": "format",
    "frm": "origin",
    "gol": "goal",
    "icl": "subclass",
    "ins": "instrument",
    "iof": "instance",
    "lpl": "logical-place",
    "man": "manner",
    "mat": "material",
    "met": "method",
    "mod": "modifier",
    "nam": "name",
    "obj": "patient",
    "opl": "objective-place",
    "or": "disjunction",
    "per": "proportion",
    "plc": "place",
    "plf": "plurality-form",
    "pof": "part-of",
    "pos": "possession",
    "ptn": "partner",
    "pur": "purpose",
    "qua": "quantity",
    "res": "result",
    "rsn": "reason",
    "scn": "scene",
    "seq": "consequence",
    "src": "source",
    "tim": "time",
    "tmf": "initial-time",
    "tmt": "final-time",
    "to": "destination",
    "via": "medium",
}

# UNL relations that map to sense/applicability (ingest) vs truth (assert).
# These correspond to the aoj subtree: ontological/classification relations.
_SENSE_RELATIONS: frozenset[str] = frozenset({
    "icl",  # inclusion / subclass
    "iof",  # instance-of
    "equ",  # equivalence
    "ant",  # antonym
    "fld",  # field
    "pof",  # part-of
    "aoj",  # attribute-of (predicative)
    "nam",  # name
})


class UNLConversionResult(NamedTuple):
    """Result of a UNL -> s-expression conversion.

    Attributes:
        sexprs: S-expression strings.
        wigame_id: Target WiGame ID.
        stats: Counts: words, relations, sexprs.
    """

    sexprs: list[str]
    wigame_id: str
    stats: dict[str, int]


class UNLConverter:
    """Convert between UNL semantic graphs and Matrix s-expressions."""

    def __init__(self, rel_map: dict[str, str] | None = None) -> None:
        self._rel_map = dict(_UNL_TO_MATRIX_REL)
        if rel_map:
            self._rel_map.update(rel_map)

    # ---- UNL -> s-expressions -----------------------------------------

    def unl_to_sexprs(
        self,
        graph: UNLGraph,
        wigame_id: str = "wigame:unl",
    ) -> UNLConversionResult:
        """Convert a UNLGraph into Matrix s-expressions.

        Produces ``create``, ``ingest``, and ``assert`` s-expressions
        that can be fed to ``SExpressionRuntime.evaluate()``.
        """
        sexprs: list[str] = []
        seen_symbols: set[str] = set()
        seen_relations: set[str] = set()
        stats = {"words": 0, "relations": 0, "sexprs": 0}

        self._emit_words(sexprs, seen_symbols, graph, stats)
        self._emit_relation_declarations(sexprs, seen_relations, graph)
        self._emit_propositions(sexprs, seen_symbols, graph, wigame_id, stats)
        self._emit_entry_marker(sexprs, graph, seen_symbols, wigame_id)
        self._emit_word_attributes(sexprs, graph, seen_symbols, wigame_id)

        stats["sexprs"] = len(sexprs)
        return UNLConversionResult(sexprs=sexprs, wigame_id=wigame_id, stats=stats)

    @staticmethod
    def _emit_words(
        sexprs: list[str],
        seen: set[str],
        graph: UNLGraph,
        stats: dict[str, int],
    ) -> None:
        for word in graph.words:
            cid = word.id if word.id != word.concept else word.concept
            if cid not in seen:
                sexprs.append(f"(create symbol {cid} {cid})")
                seen.add(cid)
                stats["words"] += 1

    @staticmethod
    def _emit_relation_declarations(
        sexprs: list[str],
        seen: set[str],
        graph: UNLGraph,
    ) -> None:
        matrix_rel_map = _UNL_TO_MATRIX_REL
        for rel in graph.relations:
            matrix_rel = matrix_rel_map.get(rel.type, rel.type)
            if matrix_rel not in seen:
                sexprs.append(f"(create relation {matrix_rel} {matrix_rel})")
                seen.add(matrix_rel)
            # also declare the parent relation if it exists
            parent_tag = rel.parent
            if parent_tag:
                parent_rel = matrix_rel_map.get(parent_tag, parent_tag)
                if parent_rel not in seen:
                    sexprs.append(f"(create relation {parent_rel} {parent_rel})")
                    seen.add(parent_rel)

    @staticmethod
    def _emit_propositions(
        sexprs: list[str],
        seen_symbols: set[str],
        graph: UNLGraph,
        wigame_id: str,
        stats: dict[str, int],
    ) -> None:
        matrix_rel_map = _UNL_TO_MATRIX_REL
        for rel in graph.relations:
            matrix_rel = matrix_rel_map.get(rel.type, rel.type)
            subj, obj = rel.source, rel.target

            for sid in (subj, obj):
                if sid not in seen_symbols:
                    sexprs.append(f"(create symbol {sid} {sid})")
                    seen_symbols.add(sid)

            if rel.type in _SENSE_RELATIONS:
                sexprs.append(f"(ingest {wigame_id} ({matrix_rel} {subj} {obj}))")
            else:
                sexprs.append(f"(assert {wigame_id} ({matrix_rel} {subj} {obj}))")
            stats["relations"] += 1

    @staticmethod
    def _emit_entry_marker(
        sexprs: list[str],
        graph: UNLGraph,
        seen_symbols: set[str],
        wigame_id: str,
    ) -> None:
        eid = graph.entry_word_id
        if eid and eid in seen_symbols:
            sexprs.append(f"(assert {wigame_id} (entry {eid}))")

    @staticmethod
    def _emit_word_attributes(
        sexprs: list[str],
        graph: UNLGraph,
        seen_symbols: set[str],
        wigame_id: str,
    ) -> None:
        for word in graph.words:
            if word.id not in seen_symbols:
                continue
            for attr in sorted(word.attributes):
                attr_clean = attr.lstrip("@")
                sexprs.append(
                    f"(assert {wigame_id} (attr {word.id} {attr_clean}))"
                )

    # ---- s-expressions -> UNL -----------------------------------------

    def sexprs_to_unl(self, sexprs: Sequence[str]) -> UNLGraph:
        """Convert Matrix s-expressions back to a UNL graph (best-effort).

        Only ``ingest`` and ``assert`` forms that look like propositions
        are converted.
        """
        triples: list[tuple[str, str, str]] = []

        for sexpr in sexprs:
            tokens = sexpr.replace("(", " ").replace(")", " ").split()
            if len(tokens) < _MIN_TOKENS:
                continue
            cmd = tokens[0]
            if cmd not in ("ingest", "assert"):
                continue

            rel = tokens[2]
            subj = tokens[3]
            obj = tokens[4] if len(tokens) > _MIN_TOKENS else ""
            triples.append((rel, subj, obj))

        return UNLGraph.from_triples(triples)
