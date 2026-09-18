"""Traced modus ponens over the compiled implication matrix."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..core.evidence import make_evidence
from ..core.fact import Fact
from ..core.proposition import Proposition
from ..core.truth_value import TruthValue
from ..kernel.formulas import AndFormula, Formula, IfFormula, KernelAtom, RelationAtom, parse_formula
from ..kernel.rule_matrix import RuleMatrixCompiler
from .logical_system_algebra import is_derivable_source

if TYPE_CHECKING:
    from .logical_system import LogicalSystem
    from .wigame import WiGame


def deduce(
    system: "LogicalSystem",
    wigame_id: str | None = None,
    report: dict | None = None,
) -> list[Fact]:
    """Derives new TRUE facts using ``v (x) I*``.

    With ``wigame_id`` set only that WiGame is considered; with ``None`` the
    premise vector gathers facts from every WiGame and each derived atom lands
    in the world that accepts it (ambiguous or unplaceable atoms are reported
    through ``report``). Conjunctive antecedents are introduced before each
    closure pass until a fixed point.
    """

    if report is not None:
        report.setdefault("ambiguous", [])
        report.setdefault("unplaced", [])
    wigames = _target_wigames(system, wigame_id)
    if not system.rules or not wigames:
        return []

    facts_by_atom: dict[str, list[Fact]] = {}
    for wigame in wigames:
        for fact in wigame.facts.values():
            if is_derivable_source(fact):
                facts_by_atom.setdefault(fact.proposition.sexpr(), []).append(fact)
    compiled = RuleMatrixCompiler.compile(_compilable_rules(system.rules))
    closure = compiled.implication_matrix.transitive_closure()
    compound_sources: dict[str, list[Fact]] = {}
    known = set(facts_by_atom)

    derived: list[Fact] = []
    while True:
        changed = _introduce_conjunctions(system.rules, known, facts_by_atom, compound_sources)
        for atom in compiled.atoms:
            if atom in known:
                continue
            support = [source for source in compiled.atoms if source in known and bool(closure.get(source, atom))]
            if not support:
                continue
            formula = parse_formula(atom)
            if not isinstance(formula, RelationAtom):
                continue
            targets = _accepting_wigames(system, wigame_id, formula)
            if not targets:
                if report is not None and atom not in report["unplaced"]:
                    report["unplaced"].append(atom)
                continue
            if len(targets) > 1:
                candidates = sorted(wigame.wigame_id for wigame in targets)
                if report is not None and not any(entry["atom"] == atom for entry in report["ambiguous"]):
                    report["ambiguous"].append({"atom": atom, "candidates": candidates})
                continue
            wigame = targets[0]
            proposition = _proposition(formula, wigame.wigame_id)
            current = wigame.Vi.get(proposition.subject_symbol_id, proposition.object_symbol_id)
            if current in {TruthValue.FALSE.value, TruthValue.TRUE.value}:
                continue
            fact = Fact(
                proposition=proposition,
                truth=TruthValue.TRUE,
                evidence=make_evidence(
                    tier="inferred",
                    curation="confirmed",
                    derived_from=_source_ids(support, facts_by_atom, compound_sources),
                    rule=_direct_rule(system.rules, support, atom),
                ),
            )
            system.add_fact(fact)
            facts_by_atom.setdefault(atom, []).append(fact)
            known.add(atom)
            derived.append(fact)
            changed = True
        if not changed:
            break
    return derived


def _compilable_rules(rules: list[Formula]) -> list[Formula]:
    """Rewrites non-atomic antecedents into single kernel atoms for the compiler."""

    prepared: list[Formula] = []
    for rule in rules:
        if isinstance(rule, IfFormula) and not isinstance(rule.antecedent, (KernelAtom, RelationAtom)):
            prepared.append(IfFormula(KernelAtom(rule.antecedent.to_sexpr()), rule.consequent))
        else:
            prepared.append(rule)
    return prepared


def _target_wigames(system: "LogicalSystem", wigame_id: str | None) -> list["WiGame"]:
    if wigame_id is None:
        return list(system.wigames.values())
    wigame = system.wigames.get(wigame_id)
    if wigame is None:
        raise KeyError(wigame_id)
    return [wigame]


def _accepting_wigames(
    system: "LogicalSystem",
    wigame_id: str | None,
    formula: RelationAtom,
) -> list["WiGame"]:
    if wigame_id is not None:
        wigame = system.wigames[wigame_id]
        return [wigame] if wigame.accepts(_proposition(formula, wigame_id)) else []
    return [
        wigame
        for wigame in system.wigames.values()
        if wigame.accepts(_proposition(formula, wigame.wigame_id))
    ]


def _proposition(formula: RelationAtom, wigame_id: str) -> Proposition:
    return Proposition(
        relation_id=formula.relation_id,
        subject_symbol_id=formula.subject_symbol_id,
        object_symbol_id=formula.object_symbol_id,
        wigame_id=wigame_id,
    )


def _introduce_conjunctions(
    rules: list[Formula],
    known: set[str],
    facts_by_atom: dict[str, list[Fact]],
    compound_sources: dict[str, list[Fact]],
) -> bool:
    """Adds compound antecedent atoms whose conjuncts are all known."""

    changed = False
    for rule in rules:
        if not isinstance(rule, IfFormula) or not isinstance(rule.antecedent, AndFormula):
            continue
        sexpr = rule.antecedent.to_sexpr()
        if sexpr in known:
            continue
        parts = [operand.to_sexpr() for operand in rule.antecedent.operands]
        if not all(part in known for part in parts):
            continue
        known.add(sexpr)
        compound_sources[sexpr] = [
            fact for part in parts for fact in facts_by_atom.get(part, []) + compound_sources.get(part, [])
        ]
        changed = True
    return changed


def _source_ids(
    support: list[str],
    facts_by_atom: dict[str, list[Fact]],
    compound_sources: dict[str, list[Fact]],
) -> list[str]:
    return sorted(
        {
            fact.fact_id
            for atom in support
            for fact in facts_by_atom.get(atom, []) + compound_sources.get(atom, [])
        }
    )


def _direct_rule(rules: list[Formula], support: list[str], atom: str) -> str | None:
    for rule in rules:
        if not isinstance(rule, IfFormula):
            continue
        if rule.consequent.to_sexpr() == atom and rule.antecedent.to_sexpr() in support:
            return rule.to_sexpr()
    return None
