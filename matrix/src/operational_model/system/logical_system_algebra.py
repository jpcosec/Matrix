"""System-level algebraic inference orchestration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..core.commutative_inference import CommutativeInference
from ..core.transitive_inference import TransitiveInference

if TYPE_CHECKING:
    from ..core.fact import Fact
    from .logical_system import LogicalSystem


def apply_algebra(system: "LogicalSystem", fact: "Fact") -> None:
    """Applies algebraic properties of the relation to the system."""
    relation = system.relations.get(fact.proposition.relation_id)
    if not relation:
        return
    semantics = relation.semantics
    if semantics.supports_commutative_equivalence():
        _apply_commutative(system, fact)
    if semantics.supports_transitive_closure():
        _apply_transitive(system, fact)


def _apply_commutative(system: "LogicalSystem", fact: "Fact") -> None:
    """Infers and adds symmetric facts."""
    sym_fact = CommutativeInference.infer(fact)
    _safe_add(system, sym_fact)


def _apply_transitive(system: "LogicalSystem", fact: "Fact") -> None:
    """Infers and adds transitive closure facts."""
    wigame = system.wigames[fact.proposition.wigame_id]
    others = list(wigame.facts.values())
    inferred = TransitiveInference.infer(fact, others)
    for inf in inferred:
        _safe_add(system, inf)


def _safe_add(system: "LogicalSystem", fact: "Fact") -> None:
    """Adds a fact only if it fits the game and adds new information."""
    wigame = system.wigames.get(fact.proposition.wigame_id)
    if not (wigame and wigame.accepts(fact.proposition)):
        return
    s, o = fact.proposition.subject_symbol_id, fact.proposition.object_symbol_id
    if wigame.Vi.get(s, o) != fact.truth.value:
        system.add_fact(fact)
