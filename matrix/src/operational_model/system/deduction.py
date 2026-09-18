"""Traced modus ponens over the compiled implication matrix."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..core.evidence import make_evidence
from ..core.fact import Fact
from ..core.proposition import Proposition
from ..core.truth_value import TruthValue
from ..kernel.formulas import Formula, IfFormula, RelationAtom, parse_formula
from ..kernel.rule_matrix import RuleMatrixCompiler
from .logical_system_algebra import is_derivable_source

if TYPE_CHECKING:
    from .logical_system import LogicalSystem


def deduce(system: "LogicalSystem", wigame_id: str) -> list[Fact]:
    """Derives new TRUE facts inside one WiGame using ``v (x) I*``."""

    wigame = system.wigames.get(wigame_id)
    if wigame is None:
        raise KeyError(wigame_id)
    if not system.rules:
        return []

    facts_by_atom: dict[str, list[Fact]] = {}
    for fact in wigame.facts.values():
        if is_derivable_source(fact):
            facts_by_atom.setdefault(fact.proposition.sexpr(), []).append(fact)
    compiled = RuleMatrixCompiler.compile(list(system.rules))
    closure = compiled.implication_matrix.transitive_closure()
    known = {atom for atom in compiled.atoms if atom in facts_by_atom}

    derived: list[Fact] = []
    for atom in compiled.atoms:
        if atom in known:
            continue
        support = [source for source in compiled.atoms if source in known and bool(closure.get(source, atom))]
        if not support:
            continue
        proposition = _atom_proposition(atom, wigame_id)
        if proposition is None or not wigame.accepts(proposition):
            continue
        current = wigame.Vi.get(proposition.subject_symbol_id, proposition.object_symbol_id)
        if current in {TruthValue.FALSE.value, TruthValue.TRUE.value}:
            continue
        fact = Fact(
            proposition=proposition,
            truth=TruthValue.TRUE,
            evidence=make_evidence(
                tier="inferred",
                curation="confirmed",
                derived_from=_source_ids(support, facts_by_atom),
                rule=_direct_rule(system.rules, support, atom),
            ),
        )
        system.add_fact(fact)
        derived.append(fact)
    return derived


def _atom_proposition(atom: str, wigame_id: str) -> Proposition | None:
    formula = parse_formula(atom)
    if not isinstance(formula, RelationAtom):
        return None
    return Proposition(
        relation_id=formula.relation_id,
        subject_symbol_id=formula.subject_symbol_id,
        object_symbol_id=formula.object_symbol_id,
        wigame_id=wigame_id,
    )


def _source_ids(
    support: list[str],
    facts_by_atom: dict[str, list[Fact]],
) -> list[str]:
    return sorted({fact.fact_id for atom in support for fact in facts_by_atom[atom]})


def _direct_rule(rules: list[Formula], support: list[str], atom: str) -> str | None:
    for rule in rules:
        if not isinstance(rule, IfFormula):
            continue
        if rule.consequent.to_sexpr() == atom and rule.antecedent.to_sexpr() in support:
            return rule.to_sexpr()
    return None
