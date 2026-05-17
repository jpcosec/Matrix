"""Transitive inference logic."""

from __future__ import annotations

from .fact import Fact
from .proposition import Proposition


class TransitiveInference:
    """Handles transitive fact generation."""

    @staticmethod
    def infer(fact: Fact, others: list[Fact]) -> list[Fact]:
        """Returns facts inferred via (aRb and bRc -> aRc)."""
        p = fact.proposition
        f = [TransitiveInference._l(p, o.proposition, fact) for o in others if o.proposition.subject_symbol_id == p.object_symbol_id]
        b = [TransitiveInference._l(o.proposition, p, fact) for o in others if o.proposition.object_symbol_id == p.subject_symbol_id]
        return f + b

    @staticmethod
    def _l(p1: Proposition, p2: Proposition, sample: Fact) -> Fact:
        """Links two propositions transitively."""
        new_prop = Proposition(
            relation_id=p1.relation_id,
            subject_symbol_id=p1.subject_symbol_id,
            object_symbol_id=p2.object_symbol_id,
            wigame_id=p1.wigame_id,
        )
        return Fact(proposition=new_prop, truth=sample.truth)
