"""System-level algebraic inference orchestration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..core.commutative_inference import CommutativeInference
from ..core.evidence import DERIVABLE_TIERS, make_evidence
from ..core.transitive_inference import TransitiveInference
from ..core.truth_value import TruthValue

if TYPE_CHECKING:
    from ..core.fact import Fact
    from .logical_system import LogicalSystem


def is_derivable_source(fact: "Fact") -> bool:
    """Reports whether a fact may feed matrix derivation."""

    return (
        fact.truth == TruthValue.TRUE
        and fact.evidence.get("tier") in DERIVABLE_TIERS
    )


def apply_algebra(system: "LogicalSystem", fact: "Fact") -> None:
    """Applies algebraic properties of the relation to the system."""

    relation = system.relations.get(fact.proposition.relation_id)
    if not relation:
        return
    if not is_derivable_source(fact):
        return
    semantics = relation.semantics
    if semantics.supports_commutative_equivalence():
        _apply_commutative(system, fact)
    if semantics.supports_transitive_closure():
        _apply_transitive(system, fact)


def _apply_commutative(system: "LogicalSystem", fact: "Fact") -> None:
    """Infers and adds symmetric facts."""

    sym_fact = CommutativeInference.infer(fact)
    sym_fact.evidence = make_evidence(
        tier="inferred",
        curation="confirmed",
        prov=fact.evidence.get("prov"),
        derived_from=[fact.fact_id],
        rule="commutative",
    )
    _safe_add(system, sym_fact)


def _apply_transitive(system: "LogicalSystem", fact: "Fact") -> None:
    """Infers and adds transitive closure facts."""

    wigame = system.wigames[fact.proposition.wigame_id]
    relation_id = fact.proposition.relation_id
    others = [
        other
        for other in wigame.facts.values()
        if is_derivable_source(other) and other.proposition.relation_id == relation_id
    ]
    if fact not in others:
        others = [fact] + others
    sources = sorted({source.fact_id for source in others})
    inferred = TransitiveInference.infer(fact, others)
    for candidate in inferred:
        candidate.evidence = make_evidence(
            tier="inferred",
            curation="confirmed",
            derived_from=sources,
            rule="transitive",
        )
        _safe_add(system, candidate)


def _safe_add(system: "LogicalSystem", fact: "Fact") -> None:
    """Adds a fact only if it fits the game and adds new information."""
    wigame = system.wigames.get(fact.proposition.wigame_id)
    if not (wigame and wigame.accepts(fact.proposition)):
        return
    s, o = fact.proposition.subject_symbol_id, fact.proposition.object_symbol_id
    if wigame.Vi.get(s, o) != fact.truth.value:
        system.add_fact(fact)
