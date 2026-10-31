"""Commutative inference logic."""

from __future__ import annotations

from .fact import Fact
from .proposition import Proposition


class CommutativeInference:
    """Handles symmetric fact generation."""

    @staticmethod
    def infer(fact: Fact) -> Fact:
        """Returns the symmetric fact for a given fact."""
        prop = fact.proposition
        new_prop = Proposition(
            relation_id=prop.relation_id,
            subject_symbol_id=prop.object_symbol_id,
            object_symbol_id=prop.subject_symbol_id,
            wigame_id=prop.wigame_id,
        )
        return Fact(proposition=new_prop, truth=fact.truth)
