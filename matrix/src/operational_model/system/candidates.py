"""Curation queue for statistical and LLM-proposed knowledge."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from .._ids import new_id
from ..core.evidence import TIERS, append_history, make_evidence, validate_evidence
from ..core.fact import Fact
from ..core.li_space import LiSpace
from ..core.name import Name
from ..core.proposition import Proposition
from ..core.sense_value import SenseValue
from ..core.symbol import Symbol
from ..core.thing import Thing
from ..core.truth_value import TruthValue
from ..kernel.formulas import IfFormula, RelationAtom, parse_formula
from ..routing.routing_projection import RoutingProjection
from .deduction import deduce
from .operation_results import OperationResult
from .wigame import WiGame

if TYPE_CHECKING:
    from .logical_system import LogicalSystem
    from .wigame import WiGame

KINDS = ("fact", "symbol", "nonsense", "rule", "class")


@dataclass
class Candidate:
    """One proposed piece of knowledge awaiting curation."""

    candidate_id: str
    kind: str
    wigame_id: str | None
    payload: dict[str, Any]
    evidence: dict[str, Any] = field(default_factory=dict)


def register_candidate(
    system: "LogicalSystem",
    kind: str,
    wigame_id: str | None,
    payload: dict[str, Any],
    evidence: dict[str, Any] | None = None,
) -> Candidate:
    """Registers a proposed candidate in the curation queue."""

    if kind not in KINDS:
        raise ValueError(f"unsupported candidate kind: {kind}")
    entry = dict(evidence or {})
    entry.setdefault("tier", "statistical")
    entry.setdefault("curation", "proposed")
    entry.setdefault("history", [])
    validate_evidence(entry)
    candidate = Candidate(
        candidate_id=new_id("cand"),
        kind=kind,
        wigame_id=wigame_id,
        payload=dict(payload),
        evidence=entry,
    )
    system.candidates[candidate.candidate_id] = candidate
    return candidate


def promote_candidate(
    system: "LogicalSystem",
    candidate_id: str,
    tier: str = "confirmed",
) -> OperationResult:
    """Applies a candidate to the operational model and confirms it."""

    candidate = system.candidates.get(candidate_id)
    if candidate is None:
        return OperationResult(status="reject", sinn="unsinnig", reason=f"unknown candidate: {candidate_id}")
    if tier not in TIERS:
        raise ValueError(f"unknown evidence tier: {tier!r}")
    result = _apply_candidate(system, candidate, tier)
    if result.status == "accept":
        candidate.evidence["tier"] = tier
        candidate.evidence["curation"] = "confirmed"
        append_history(candidate.evidence, "promote", note=tier)
    return result


def reject_candidate(system: "LogicalSystem", candidate_id: str, reason: str) -> OperationResult:
    """Marks a candidate as rejected while keeping it in the queue."""

    candidate = system.candidates.get(candidate_id)
    if candidate is None:
        return OperationResult(status="reject", sinn="unsinnig", reason=f"unknown candidate: {candidate_id}")
    candidate.evidence["curation"] = "rejected"
    append_history(candidate.evidence, "reject", note=reason)
    return OperationResult(
        status="accept",
        payload={"candidate_id": candidate_id, "curation": "rejected"},
    )


def _apply_candidate(system: "LogicalSystem", candidate: Candidate, tier: str) -> OperationResult:
    if candidate.kind == "fact":
        return _promote_fact(system, candidate, tier)
    if candidate.kind == "symbol":
        return _promote_symbol(system, candidate)
    if candidate.kind == "nonsense":
        return _promote_nonsense(system, candidate)
    if candidate.kind == "rule":
        return _promote_rule(system, candidate, tier)
    if candidate.kind == "class":
        return _promote_class(system, candidate)
    return OperationResult(status="reject", sinn="unsinnig", reason=f"unsupported kind: {candidate.kind}")


def _promote_fact(system: "LogicalSystem", candidate: Candidate, tier: str) -> OperationResult:
    formula = parse_formula(candidate.payload["proposition"])
    if not isinstance(formula, RelationAtom):
        return OperationResult(status="reject", sinn="unsinnig", reason="fact payload must be a relation atom")
    wigame = _resolve_wigame(system, candidate.wigame_id, formula)
    if isinstance(wigame, OperationResult):
        return wigame
    proposition = _proposition(formula, wigame.wigame_id)
    current = wigame.Vi.get(proposition.subject_symbol_id, proposition.object_symbol_id)
    if current == TruthValue.FALSE.value:
        return OperationResult(
            status="reject",
            sinn="widerspruechlich",
            reason="candidate contradicts an existing false cell",
        )
    action = "noop" if current == TruthValue.TRUE.value else "asserted"
    if action == "asserted":
        evidence = dict(candidate.evidence)
        evidence["tier"] = tier
        evidence["curation"] = "confirmed"
        system.add_fact(Fact(proposition=proposition, truth=TruthValue.TRUE, evidence=evidence))
    return OperationResult(
        status="accept",
        payload={"candidate_id": candidate.candidate_id, "kind": candidate.kind, "action": action},
    )


def _promote_symbol(system: "LogicalSystem", candidate: Candidate) -> OperationResult:
    symbol_id = candidate.payload["symbol_id"]
    if symbol_id in system.symbols:
        return OperationResult(
            status="accept",
            payload={"candidate_id": candidate.candidate_id, "kind": candidate.kind, "action": "noop"},
        )
    system.register_thing(Thing(Symbol(symbol_id), Name(candidate.payload["sign"])))
    return OperationResult(
        status="accept",
        payload={"candidate_id": candidate.candidate_id, "kind": candidate.kind, "action": "created"},
    )


def _promote_nonsense(system: "LogicalSystem", candidate: Candidate) -> OperationResult:
    formula = parse_formula(candidate.payload["proposition"])
    if not isinstance(formula, RelationAtom):
        return OperationResult(status="reject", sinn="unsinnig", reason="nonsense payload must be a relation atom")
    wigame = _resolve_wigame(system, candidate.wigame_id, formula)
    if isinstance(wigame, OperationResult):
        return wigame
    subject, obj = formula.subject_symbol_id, formula.object_symbol_id
    if subject not in wigame.axis_a or obj not in wigame.axis_b:
        return OperationResult(status="reject", sinn="unsinnig", reason="proposition is not addressable in the WiGame")
    wigame.set_sense(subject, obj, SenseValue.UNSINNIG)
    return OperationResult(
        status="accept",
        payload={"candidate_id": candidate.candidate_id, "kind": candidate.kind, "action": "unsinnig"},
    )


def _promote_rule(system: "LogicalSystem", candidate: Candidate, tier: str) -> OperationResult:
    antecedent = parse_formula(candidate.payload["if"])
    consequent = parse_formula(candidate.payload["then"])
    rule = IfFormula(antecedent, consequent)
    if rule.to_sexpr() not in system.rule_evidence:
        system.rules.append(rule)
        system.rule_evidence[rule.to_sexpr()] = make_evidence(
            tier=tier,
            curation="confirmed",
            derived_from=None,
            rule=rule.to_sexpr(),
        )
    derived: list[str] = []
    for wigame_id in _rule_targets(system, candidate.wigame_id, rule):
        derived.extend(fact.proposition.sexpr() for fact in deduce(system, wigame_id))
    return OperationResult(
        status="accept",
        payload={"candidate_id": candidate.candidate_id, "kind": candidate.kind, "rule": rule.to_sexpr(), "derived": derived},
    )


def _promote_class(system: "LogicalSystem", candidate: Candidate) -> OperationResult:
    if candidate.wigame_id is None or candidate.wigame_id not in system.wigames:
        return OperationResult(status="reject", sinn="unsinnig", reason="class candidate needs a parent WiGame")
    parent = system.wigames[candidate.wigame_id]
    class_id = candidate.payload["class_id"]
    symbols = list(candidate.payload["symbols"])
    wigame_id = f"wigame:{class_id}"
    if wigame_id in system.wigames:
        return OperationResult(
            status="accept",
            payload={"candidate_id": candidate.candidate_id, "kind": candidate.kind, "action": "noop"},
        )
    relation_id = candidate.payload.get("relation_id") or parent.relation_id
    li = LiSpace(li_id=f"li:{class_id}", axis_a=symbols, axis_b=list(parent.axis_b), relation_id=relation_id)
    system.register_wigame(WiGame(wigame_id=wigame_id, li=li, context_id=parent.wigame_id))
    projection = RoutingProjection.empty(
        source_wigame_id=parent.wigame_id,
        source_axis=list(parent.axis_a),
        target_wigame_id=wigame_id,
        target_axis=symbols,
        relation_id="projects_to",
    )
    for symbol in symbols:
        if symbol in parent.axis_a:
            projection.link(symbol, symbol)
    system.register_projection(projection)
    return OperationResult(
        status="accept",
        payload={
            "candidate_id": candidate.candidate_id,
            "kind": candidate.kind,
            "wigame_id": wigame_id,
            "projection_id": projection.matrix_id,
            "action": "created",
        },
    )


def _resolve_wigame(
    system: "LogicalSystem",
    wigame_id: str | None,
    formula: RelationAtom,
) -> "WiGame | OperationResult":
    if wigame_id is not None:
        wigame = system.wigames.get(wigame_id)
        if wigame is None:
            return OperationResult(status="reject", sinn="unsinnig", reason=f"unknown WiGame: {wigame_id}")
        return wigame
    candidates = [
        wigame
        for wigame in system.wigames.values()
        if wigame.accepts(_proposition(formula, wigame.wigame_id))
    ]
    if not candidates:
        return OperationResult(status="reject", sinn="unsinnig", reason="no WiGame accepts this proposition")
    if len(candidates) > 1:
        return OperationResult(
            status="ambiguous",
            sinn="unsinnig",
            payload={"candidates": sorted(wigame.wigame_id for wigame in candidates)},
            reason="multiple WiGames accept this proposition",
        )
    return candidates[0]


def _proposition(formula: RelationAtom, wigame_id: str) -> Proposition:
    return Proposition(
        relation_id=formula.relation_id,
        subject_symbol_id=formula.subject_symbol_id,
        object_symbol_id=formula.object_symbol_id,
        wigame_id=wigame_id,
    )


def _rule_targets(system: "LogicalSystem", wigame_id: str | None, rule: IfFormula) -> list[str]:
    if wigame_id is not None:
        return [wigame_id] if wigame_id in system.wigames else []
    if not isinstance(rule.antecedent, RelationAtom) or not isinstance(rule.consequent, RelationAtom):
        return []
    targets: list[str] = []
    for candidate_id, wigame in system.wigames.items():
        accepts_both = wigame.accepts(_proposition(rule.antecedent, candidate_id)) and wigame.accepts(
            _proposition(rule.consequent, candidate_id)
        )
        if accepts_both:
            targets.append(candidate_id)
    return targets
