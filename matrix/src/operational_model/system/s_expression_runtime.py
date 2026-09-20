"""Runtime evaluation for the first canonical s-expression slice.

The `evidence` argument is an atom `evidence:<json>` with no spaces, using
single quotes when a JSON string is needed, e.g.
`evidence:{'tier':'statistical','curation':'proposed'}`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..core.evidence import append_history, validate_evidence
from ..core.fact import Fact
from ..core.li_space import LiSpace
from ..core.name import Name
from ..core.proposition import Proposition
from ..core.relation import Relation
from ..core.symbol import Symbol
from ..core.thing import Thing
from ..core.truth_value import TruthValue
from ..kernel.formulas import IfFormula, RelationAtom, parse_formula
from ..routing.context import Context
from ..language.s_expressions import SExpression, parse_s_expression
from .candidates import KINDS, promote_candidate, projection_for, register_candidate, reject_candidate
from .deduction import deduce
from .operation_results import OperationResult

if TYPE_CHECKING:
    from .logical_system import LogicalSystem
    from .wigame import WiGame


@dataclass(frozen=True)
class Selector:
    """Typed selector used by `(return facts ...)`."""

    kind: str
    value: str


class SExpressionRuntime:
    """Evaluates a minimal set of canonical Matrix s-expressions."""

    def __init__(self, system: "LogicalSystem") -> None:
        self.system = system

    def evaluate(self, source: str | SExpression) -> OperationResult:
        """Evaluates one s-expression against the current system."""

        expr = parse_s_expression(source) if isinstance(source, str) else source
        if not isinstance(expr, list) or not expr:
            raise ValueError("top-level expression must be a non-empty list")
        head = self._require_atom(expr[0], "operator")
        if head == "check":
            return self._eval_check(expr[1:])
        if head == "assert":
            return self._eval_assert(expr[1:])
        if head == "create":
            return self._eval_create(expr[1:])
        if head == "ingest":
            return self._eval_ingest(expr[1:])
        if head == "return":
            return self._eval_return(expr[1:])
        if head == "candidate":
            return self._eval_candidate(expr[1:])
        if head == "promote":
            return self._eval_promote(expr[1:])
        if head == "reject":
            return self._eval_reject(expr[1:])
        if head == "retract":
            return self._eval_retract(expr[1:])
        if head == "why":
            return self._eval_why(expr[1:])
        if head == "define":
            return self._eval_define(expr[1:])
        if head == "project":
            return self._eval_project(expr[1:])
        raise ValueError(f"unsupported operation: {head}")

    def _eval_create(self, args: list[SExpression]) -> OperationResult:
        if not args:
            raise ValueError("create requires a target kind")
        kind = self._require_atom(args[0], "create target")
        if kind == "symbol":
            return self._create_symbol(args[1:])
        if kind == "relation":
            return self._create_relation(args[1:])
        if kind == "li":
            return self._create_li(args[1:])
        if kind == "wigame":
            return self._create_wigame(args[1:])
        if kind == "context":
            return self._create_context(args[1:])
        raise ValueError(f"unsupported create target: {kind}")

    def _eval_ingest(self, args: list[SExpression]) -> OperationResult:
        if len(args) != 2:
            raise ValueError("ingest expects `wigame:<id>` and canonical `(R a b)`")
        selector = self._parse_selector(args[0])
        if selector.kind != "wigame":
            raise ValueError("ingest requires a wigame selector")
        wigame_id = self._normalize_selector_value(selector)
        proposition = self._parse_proposition(args[1], wigame_id=wigame_id)
        wigame = self.system.wigames.get(wigame_id)
        if wigame is None:
            return OperationResult(status="reject", sinn="unsinnig", reason="target WiGame does not exist")
        if not wigame.accepts(proposition):
            return OperationResult(status="reject", sinn="unsinnig", reason="target WiGame does not accept this proposition")
        wigame.register_proposition(proposition)
        return OperationResult(
            status="accept",
            sinn=wigame.Si.get(proposition.subject_symbol_id, proposition.object_symbol_id),
            payload={"wigame_id": wigame_id, "proposition": proposition.sexpr(), "action": "registered"},
        )

    def _eval_check(self, args: list[SExpression]) -> OperationResult:
        wigame_id, proposition = self._resolve_targeted_proposition(args)
        if wigame_id is None:
            candidates = self._candidate_wigame_ids(proposition)
            if not candidates:
                return OperationResult(
                    status="reject",
                    sinn="unsinnig",
                    reason="no WiGame accepts this proposition",
                )
            if len(candidates) > 1:
                return OperationResult(
                    status="ambiguous",
                    sinn="unsinnig",
                    payload={"candidates": candidates, "proposition": proposition.sexpr()},
                    reason="multiple WiGames accept this proposition",
                )
            wigame_id = candidates[0]
        wigame = self.system.wigames[wigame_id]
        if not wigame.accepts(proposition):
            return OperationResult(
                status="reject",
                sinn="unsinnig",
                reason="target WiGame does not accept this proposition",
            )
        truth = wigame.Vi.get(proposition.subject_symbol_id, proposition.object_symbol_id)
        sense = wigame.Si.get(proposition.subject_symbol_id, proposition.object_symbol_id)
        return OperationResult(
            status="accept",
            sinn=sense,
            payload={
                "wigame_id": wigame_id,
                "proposition": proposition.sexpr(),
                "truth": truth,
                "exists": truth != TruthValue.UNKNOWN.value,
            },
        )

    def _eval_assert(self, args: list[SExpression]) -> OperationResult:
        args, evidence = self._extract_evidence(args)
        wigame_id, proposition = self._resolve_targeted_proposition(args)
        if wigame_id is None:
            candidates = self._candidate_wigame_ids(proposition)
            if not candidates:
                return OperationResult(
                    status="reject",
                    sinn="unsinnig",
                    reason="no WiGame accepts this proposition",
                )
            if len(candidates) > 1:
                return OperationResult(
                    status="ambiguous",
                    sinn="unsinnig",
                    payload={"candidates": candidates, "proposition": proposition.sexpr()},
                    reason="multiple WiGames accept this proposition",
                )
            wigame_id = candidates[0]
        wigame = self.system.wigames[wigame_id]
        if not wigame.accepts(proposition):
            return OperationResult(
                status="reject",
                sinn="unsinnig",
                reason="target WiGame does not accept this proposition",
            )
        current = wigame.Vi.get(proposition.subject_symbol_id, proposition.object_symbol_id)
        if current == TruthValue.FALSE.value:
            return OperationResult(
                status="reject",
                sinn="widerspruechlich",
                reason="cannot assert a true fact over an existing false cell",
            )
        if current == TruthValue.TRUE.value:
            return OperationResult(
                status="accept",
                sinn=wigame.Si.get(proposition.subject_symbol_id, proposition.object_symbol_id),
                payload={
                    "wigame_id": wigame_id,
                    "proposition": proposition.sexpr(),
                    "action": "noop",
                },
            )
        self.system.add_fact(Fact(proposition=proposition, truth=TruthValue.TRUE, evidence=evidence or {}))
        return OperationResult(
            status="accept",
            sinn=wigame.Si.get(proposition.subject_symbol_id, proposition.object_symbol_id),
            payload={
                "wigame_id": wigame_id,
                "proposition": proposition.sexpr(),
                "action": "added",
            },
        )

    def _eval_return(self, args: list[SExpression]) -> OperationResult:
        if not args:
            raise ValueError("return requires a target")
        target = self._require_atom(args[0], "return target")
        if target == "candidates":
            return OperationResult(status="accept", payload={"candidates": self._candidate_records(args[1:])})
        if target == "projections":
            return OperationResult(status="accept", payload={"projections": self._projection_records(args[1:])})
        if target != "facts":
            raise ValueError(f"unsupported return target: {target}")
        selectors = [self._parse_selector(arg) for arg in args[1:]]
        groups = [group for group in self._fact_groups(selectors) if group["facts"]]
        return OperationResult(status="accept", payload={"groups": groups})

    def _create_symbol(self, args: list[SExpression]) -> OperationResult:
        if len(args) != 2:
            raise ValueError("create symbol expects `<symbol-id> <sign>`")
        symbol_id = self._require_atom(args[0], "symbol id")
        sign = self._require_atom(args[1], "sign")
        if symbol_id in self.system.symbols:
            return OperationResult(status="accept", payload={"symbol_id": symbol_id, "action": "noop"})
        thing = Thing(Symbol(symbol_id), Name(sign))
        self.system.register_thing(thing)
        return OperationResult(status="accept", payload={"symbol_id": symbol_id, "sign": sign, "action": "created"})

    def _create_relation(self, args: list[SExpression]) -> OperationResult:
        if len(args) < 2:
            raise ValueError("create relation expects `<relation-id> <name>` plus optional flags")
        relation_id = self._require_atom(args[0], "relation id")
        name = self._require_atom(args[1], "relation name")
        if relation_id in self.system.relations:
            return OperationResult(status="accept", payload={"relation_id": relation_id, "action": "noop"})
        flags = {selector.kind: selector.value for selector in (self._parse_selector(arg) for arg in args[2:])}
        relation = Relation(
            relation_id,
            name,
            commutative=flags.get("commutative") == "true",
            transitive=flags.get("transitive") == "true",
            associative=flags.get("associative") == "true",
            distributive=flags.get("distributive") == "true",
        )
        self.system.register_relation(relation)
        return OperationResult(status="accept", payload={"relation_id": relation_id, "action": "created"})

    def _create_li(self, args: list[SExpression]) -> OperationResult:
        if len(args) != 4:
            raise ValueError("create li expects `<li-id> <relation-id> (axis-a ...) (axis-b ...)`")
        li_id = self._require_atom(args[0], "li id")
        relation_id = self._require_atom(args[1], "relation id")
        axis_a = self._parse_axis(args[2], "axis-a")
        axis_b = self._parse_axis(args[3], "axis-b")
        if li_id in self.system.li_spaces:
            return OperationResult(status="accept", payload={"li_id": li_id, "action": "noop"})
        li_space = LiSpace(li_id=li_id, axis_a=axis_a, axis_b=axis_b, relation_id=relation_id)
        self.system.register_li(li_space)
        return OperationResult(status="accept", payload={"li_id": li_id, "action": "created"})

    def _create_context(self, args: list[SExpression]) -> OperationResult:
        if not args:
            raise ValueError("create context expects `<ctx-id>` with an optional `parent:<ctx-id>`")
        context_id = self._require_atom(args[0], "context id")
        parent_id = None
        for arg in args[1:]:
            selector = self._parse_selector(arg)
            if selector.kind != "parent":
                raise ValueError("create context only accepts a `parent:` selector")
            parent_id = selector.value
        if context_id in self.system.contexts:
            return OperationResult(status="accept", payload={"context_id": context_id, "action": "noop"})
        if parent_id is not None:
            parent = self.system.contexts.get(parent_id)
            if parent is None:
                return OperationResult(
                    status="reject", sinn="unsinnig", reason="referenced parent context does not exist"
                )
            parent.route_to_context(context_id)
        self.system.register_context(Context(context_id))
        return OperationResult(status="accept", payload={"context_id": context_id, "action": "created"})

    def _create_wigame(self, args: list[SExpression]) -> OperationResult:
        if len(args) not in {2, 3}:
            raise ValueError("create wigame expects `<wigame-id> <li-id>` with optional `context:<id>`")
        wigame_id = self._require_atom(args[0], "wigame id")
        li_id = self._require_atom(args[1], "li id")
        context_id = None
        if len(args) == 3:
            selector = self._parse_selector(args[2])
            if selector.kind != "context":
                raise ValueError("optional wigame third argument must be `context:<id>`")
            context_id = selector.value
        if wigame_id in self.system.wigames:
            return OperationResult(status="accept", payload={"wigame_id": wigame_id, "action": "noop"})
        li_space = self.system.li_spaces.get(li_id)
        if li_space is None:
            return OperationResult(status="reject", sinn="unsinnig", reason="referenced LiSpace does not exist")
        from .wigame import WiGame

        self.system.register_wigame(WiGame(wigame_id=wigame_id, li=li_space, context_id=context_id))
        return OperationResult(status="accept", payload={"wigame_id": wigame_id, "li_id": li_id, "action": "created"})

    def _eval_candidate(self, args: list[SExpression]) -> OperationResult:
        if len(args) < 2:
            raise ValueError("candidate expects a kind and a payload expression")
        kind = self._require_atom(args[0], "candidate kind")
        if kind not in KINDS:
            raise ValueError(f"unsupported candidate kind: {kind}")
        rest = list(args[1:])
        wigame_id = None
        if rest and isinstance(rest[0], str) and rest[0].startswith("wigame:"):
            wigame_id = self._normalize_selector_value(self._parse_selector(rest.pop(0)))
        rest, evidence = self._extract_evidence(rest)
        if len(rest) != 1:
            raise ValueError("candidate expects exactly one payload expression")
        payload = self._candidate_payload(kind, rest[0], wigame_id)
        candidate = register_candidate(self.system, kind, wigame_id, payload, evidence)
        return OperationResult(
            status="accept",
            payload={"candidate_id": candidate.candidate_id, "kind": kind},
        )

    def _eval_promote(self, args: list[SExpression]) -> OperationResult:
        if not args:
            raise ValueError("promote requires a candidate id")
        candidate_id = self._require_atom(args[0], "candidate id")
        tier = "confirmed"
        for arg in args[1:]:
            selector = self._parse_selector(arg)
            if selector.kind != "tier":
                raise ValueError("promote only accepts an optional `tier:` selector")
            tier = selector.value
        return promote_candidate(self.system, candidate_id, tier)

    def _eval_reject(self, args: list[SExpression]) -> OperationResult:
        if not args:
            raise ValueError("reject requires a candidate id")
        candidate_id = self._require_atom(args[0], "candidate id")
        return reject_candidate(self.system, candidate_id, self._join_reason(args[1:]))

    def _eval_retract(self, args: list[SExpression]) -> OperationResult:
        to = "false"
        rest: list[SExpression] = []
        for arg in args:
            if isinstance(arg, str) and arg.startswith("to:"):
                to = arg.split(":", 1)[1]
            else:
                rest.append(arg)
        if to not in {"false", "unknown"}:
            raise ValueError("retract `to:` must be `false` or `unknown`")
        prefix, reason_atoms = self._split_payload_prefix(rest)
        wigame_id, proposition = self._resolve_targeted_proposition(prefix)
        found = self._find_fact(wigame_id, proposition)
        if found is None:
            return OperationResult(status="reject", sinn="unsinnig", reason="unknown fact")
        wigame, fact = found
        truth = TruthValue.FALSE if to == "false" else TruthValue.UNKNOWN
        fact.truth = truth
        wigame.Vi.set(fact.proposition.subject_symbol_id, fact.proposition.object_symbol_id, truth.value)
        append_history(fact.evidence, "retract", note=self._join_reason(reason_atoms))
        dependents: list[str] = []
        for other_wigame in self.system.wigames.values():
            for other in other_wigame.facts.values():
                if fact.fact_id not in other.evidence.get("derived_from", []):
                    continue
                other.truth = TruthValue.UNKNOWN
                other_wigame.Vi.set(
                    other.proposition.subject_symbol_id,
                    other.proposition.object_symbol_id,
                    TruthValue.UNKNOWN.value,
                )
                append_history(other.evidence, "retract", note=f"dependency of {fact.fact_id}")
                dependents.append(other.fact_id)
        return OperationResult(
            status="accept",
            payload={
                "wigame_id": wigame.wigame_id,
                "proposition": proposition.sexpr(),
                "truth": truth.value,
                "dependents": dependents,
            },
        )

    def _eval_why(self, args: list[SExpression]) -> OperationResult:
        wigame_id, proposition = self._resolve_targeted_proposition(args)
        found = self._find_fact(wigame_id, proposition)
        if found is None:
            return OperationResult(status="reject", sinn="unsinnig", reason="unknown fact")
        _, fact = found
        chain: list[dict[str, object]] = []
        self._append_why(fact, chain, set(), 0)
        return OperationResult(status="accept", payload={"chain": chain})

    def _eval_define(self, args: list[SExpression]) -> OperationResult:
        if len(args) != 1 or not isinstance(args[0], list):
            raise ValueError("define expects one `(if (R a b) (R c d))` rule")
        formula = parse_formula(args[0])
        if not isinstance(formula, IfFormula):
            raise ValueError("define expects an `if` formula")
        sexpr = formula.to_sexpr()
        if sexpr not in self.system.rule_evidence:
            self.system.rules.append(formula)
            self.system.rule_evidence[sexpr] = {
                "tier": "observed",
                "curation": "confirmed",
                "rule": sexpr,
                "history": [],
            }
        report: dict = {}
        derived = [fact.proposition.sexpr() for fact in deduce(self.system, None, report)]
        return OperationResult(
            status="accept",
            payload={
                "rule": sexpr,
                "derived": derived,
                "ambiguous": report["ambiguous"],
                "unplaced": report["unplaced"],
            },
        )

    def _eval_project(self, args: list[SExpression]) -> OperationResult:
        if len(args) < 3:
            raise ValueError("project expects `wigame:<src> wigame:<dst> (s t) ...`")
        source = self._normalize_selector_value(self._parse_selector(args[0]))
        target = self._normalize_selector_value(self._parse_selector(args[1]))
        if source not in self.system.wigames or target not in self.system.wigames:
            return OperationResult(status="reject", sinn="unsinnig", reason="project needs two existing WiGames")
        projection = projection_for(self.system, source, target)
        pairs = [self._parse_pair(item) for item in args[2:]]
        for source_symbol, target_symbol in pairs:
            if source_symbol in projection.row_axis and target_symbol in projection.column_axis:
                projection.link(source_symbol, target_symbol)
        self.system.projections[f"{source}->{target}"] = projection
        return OperationResult(
            status="accept",
            payload={"projection_id": projection.matrix_id, "source": source, "target": target, "pairs": pairs},
        )

    def _parse_pair(self, expr: SExpression) -> list[str]:
        if not isinstance(expr, list) or len(expr) != 2:
            raise ValueError("projection pairs use `(source target)` form")
        return [self._require_atom(expr[0], "source symbol"), self._require_atom(expr[1], "target symbol")]

    def _projection_records(self, args: list[SExpression]) -> list[dict[str, object]]:
        source_filter: str | None = None
        for arg in args:
            selector = self._parse_selector(arg)
            if selector.kind != "wigame":
                raise ValueError("return projections only accepts a `wigame:` selector")
            source_filter = self._normalize_selector_value(selector)
        records: list[dict[str, object]] = []
        for projection in self.system.projections.values():
            if source_filter is not None and projection.source_wigame_id != source_filter:
                continue
            pairs = [
                [row, column]
                for row in projection.row_axis
                for column in projection.column_axis
                if projection.get(row, column)
            ]
            records.append(
                {
                    "source": projection.source_wigame_id,
                    "target": projection.target_wigame_id,
                    "pairs": pairs,
                }
            )
        return records

    def _append_why(
        self,
        fact: Fact,
        chain: list[dict[str, object]],
        seen: set[str],
        depth: int,
    ) -> None:
        if fact.fact_id in seen or depth > 6:
            return
        seen.add(fact.fact_id)
        chain.append(
            {
                "fact_id": fact.fact_id,
                "proposition": fact.proposition.sexpr(),
                "tier": fact.evidence.get("tier"),
                "prov": fact.evidence.get("prov", []),
                "rule": fact.evidence.get("rule"),
                "derived_from": list(fact.evidence.get("derived_from", [])),
            }
        )
        for parent_id in fact.evidence.get("derived_from", []):
            parent = self._find_fact_by_id(parent_id)
            if parent is not None:
                self._append_why(parent, chain, seen, depth + 1)

    def _candidate_records(self, args: list[SExpression]) -> list[dict[str, object]]:
        wigame_filter: str | None = None
        tier_filter: str | None = None
        curation_filter: str | None = None
        min_phi: float | None = None
        for arg in args:
            selector = self._parse_selector(arg)
            if selector.kind == "wigame":
                wigame_filter = self._normalize_selector_value(selector)
            elif selector.kind == "tier":
                tier_filter = selector.value
            elif selector.kind == "curation":
                curation_filter = selector.value
            elif selector.kind == "min-phi":
                min_phi = float(selector.value)
            else:
                raise ValueError(f"unsupported candidate selector: {selector.kind}")
        records: list[dict[str, object]] = []
        for candidate in sorted(self.system.candidates.values(), key=lambda item: item.candidate_id):
            evidence = candidate.evidence
            if wigame_filter is not None and candidate.wigame_id != wigame_filter:
                continue
            if tier_filter is not None and evidence.get("tier") != tier_filter:
                continue
            if curation_filter is not None and evidence.get("curation") != curation_filter:
                continue
            phi = float(evidence.get("stats", {}).get("phi_entropic", 0.0))
            if min_phi is not None and phi < min_phi:
                continue
            records.append(
                {
                    "candidate_id": candidate.candidate_id,
                    "kind": candidate.kind,
                    "wigame_id": candidate.wigame_id,
                    "payload": dict(candidate.payload),
                    "evidence": dict(evidence),
                }
            )
        return records

    def _candidate_payload(self, kind: str, expr: SExpression, wigame_id: str | None) -> dict:
        if kind in {"fact", "nonsense"}:
            return {"proposition": self._parse_proposition(expr, wigame_id or "").sexpr()}
        if kind == "symbol":
            if not isinstance(expr, list) or len(expr) != 2:
                raise ValueError("symbol candidate payload must be `(<symbol-id> <sign>)`")
            return {
                "symbol_id": self._require_atom(expr[0], "symbol id"),
                "sign": self._require_atom(expr[1], "sign"),
            }
        if kind == "rule":
            formula = parse_formula(expr)
            if not isinstance(formula, IfFormula):
                raise ValueError("rule candidate payload must be `(if (R a b) (R c d))`")
            return {"if": formula.antecedent.to_sexpr(), "then": formula.consequent.to_sexpr()}
        if kind == "projection":
            if wigame_id is None:
                raise ValueError("projection candidate needs a `wigame:<src>` selector")
            if not isinstance(expr, list) or len(expr) < 2:
                raise ValueError("projection payload must be `(wigame:<dst> (s t) ...)`")
            target = self._normalize_selector_value(
                self._parse_selector(self._require_atom(expr[0], "target wigame"))
            )
            return {
                "source_wigame": wigame_id,
                "target_wigame": target,
                "pairs": [self._parse_pair(item) for item in expr[1:]],
            }
        if not isinstance(expr, list) or len(expr) < 2:
            raise ValueError("class candidate payload must be `(<class-id> symbol ...)`")
        relation_id = ""
        if wigame_id is not None and wigame_id in self.system.wigames:
            relation_id = self.system.wigames[wigame_id].relation_id
        return {
            "class_id": self._require_atom(expr[0], "class id"),
            "symbols": [self._require_atom(item, "class symbol") for item in expr[1:]],
            "relation_id": relation_id,
        }

    def _extract_evidence(
        self,
        args: list[SExpression],
    ) -> tuple[list[SExpression], dict | None]:
        rest: list[SExpression] = []
        evidence: dict | None = None
        for arg in args:
            if isinstance(arg, str) and arg.startswith("evidence:"):
                evidence = self._parse_evidence_atom(arg)
            else:
                rest.append(arg)
        return rest, evidence

    def _parse_evidence_atom(self, atom: str) -> dict:
        raw = atom.split(":", 1)[1]
        if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "'\"":
            raw = raw[1:-1]
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = json.loads(raw.replace("'", '"'))
        if not isinstance(payload, dict):
            raise ValueError("evidence must be a JSON object")
        validate_evidence(payload)
        return payload

    def _split_payload_prefix(
        self,
        args: list[SExpression],
    ) -> tuple[list[SExpression], list[SExpression]]:
        prefix: list[SExpression] = []
        for index, arg in enumerate(args):
            if isinstance(arg, list):
                return (prefix + [arg], args[index + 1 :])
            if isinstance(arg, str) and arg.startswith("wigame:"):
                prefix.append(arg)
                continue
            raise ValueError("expected `[wigame:<id>] (R a b)`")
        raise ValueError("expected a `(R a b)` proposition")

    def _find_fact(
        self,
        wigame_id: str | None,
        proposition: Proposition,
    ) -> tuple["WiGame", Fact] | None:
        if wigame_id is not None:
            wigames = [self.system.wigames[wigame_id]] if wigame_id in self.system.wigames else []
        else:
            wigames = list(self.system.wigames.values())
        sexpr = proposition.sexpr()
        for wigame in wigames:
            for fact in wigame.facts.values():
                if fact.proposition.sexpr() == sexpr:
                    return wigame, fact
        return None

    def _find_fact_by_id(self, fact_id: str) -> Fact | None:
        for wigame in self.system.wigames.values():
            if fact_id in wigame.facts:
                return wigame.facts[fact_id]
        return None

    def _join_reason(self, args: list[SExpression]) -> str:
        return " ".join(str(arg).strip("'\"") for arg in args).strip()

    def _resolve_targeted_proposition(
        self,
        args: list[SExpression],
    ) -> tuple[str | None, Proposition]:
        """Resolves `(assert ...)` and `(check ...)` arguments."""

        if len(args) == 1:
            return None, self._parse_proposition(args[0], wigame_id="")
        if len(args) == 2:
            selector = self._parse_selector(args[0])
            if selector.kind != "wigame":
                raise ValueError("targeted proposition requires a wigame selector")
            wigame_id = self._normalize_selector_value(selector)
            return wigame_id, self._parse_proposition(args[1], wigame_id=wigame_id)
        raise ValueError("operation expects `(R a b)` with optional `wigame:<id>` target")

    def _parse_proposition(self, expr: SExpression, wigame_id: str) -> Proposition:
        """Builds a proposition from canonical `(R a b)` form."""

        if not isinstance(expr, list) or len(expr) != 3:
            raise ValueError("proposition must use canonical `(R a b)` form")
        relation_id = self._require_atom(expr[0], "relation")
        subject_symbol_id = self._require_atom(expr[1], "subject symbol")
        object_symbol_id = self._require_atom(expr[2], "object symbol")
        return Proposition(relation_id, subject_symbol_id, object_symbol_id, wigame_id)

    def _candidate_wigame_ids(self, proposition: Proposition) -> list[str]:
        """Returns the WiGames that accept a proposition shape."""

        candidates: list[str] = []
        for wigame in self.system.wigames.values():
            probe = Proposition(
                proposition.relation_id,
                proposition.subject_symbol_id,
                proposition.object_symbol_id,
                wigame.wigame_id,
            )
            if wigame.accepts(probe):
                candidates.append(wigame.wigame_id)
        return sorted(candidates)

    def _fact_groups(self, selectors: list[Selector]) -> list[dict[str, object]]:
        """Builds fact payloads grouped by WiGame."""

        groups: list[dict[str, object]] = []
        for wigame in sorted(self.system.wigames.values(), key=lambda item: item.wigame_id):
            facts = []
            for fact in sorted(wigame.facts.values(), key=lambda item: item.proposition.sexpr()):
                if self._matches_selectors(wigame, fact, selectors):
                    proposition = fact.proposition
                    facts.append(
                        {
                            "fact_id": fact.fact_id,
                            "proposition": proposition.sexpr(),
                            "relation_id": proposition.relation_id,
                            "subject_symbol_id": proposition.subject_symbol_id,
                            "object_symbol_id": proposition.object_symbol_id,
                            "truth": fact.truth.value,
                            "sinn": wigame.Si.get(
                                proposition.subject_symbol_id, proposition.object_symbol_id
                            ),
                        }
                    )
            groups.append({"wigame_id": wigame.wigame_id, "facts": facts})
        return groups

    def _matches_selectors(self, wigame: "WiGame", fact: Fact, selectors: list[Selector]) -> bool:
        """Checks whether one fact matches all selectors."""

        proposition = fact.proposition
        for selector in selectors:
            if selector.kind == "symbol":
                value = selector.value
                if value not in {
                    proposition.subject_symbol_id,
                    proposition.object_symbol_id,
                } and not self._selector_matches_name(value, proposition):
                    return False
            elif selector.kind == "relation":
                if selector.value != proposition.relation_id:
                    return False
            elif selector.kind == "wigame":
                value = self._normalize_selector_value(selector)
                if value != wigame.wigame_id:
                    return False
            else:
                raise ValueError(f"unsupported selector kind: {selector.kind}")
        return True

    def _selector_matches_name(self, value: str, proposition: Proposition) -> bool:
        """Allows selectors to match registered thing names as well as symbol ids."""

        for symbol_id in (proposition.subject_symbol_id, proposition.object_symbol_id):
            thing = self.system.things.get(symbol_id)
            if thing and thing.name.sign == value:
                return True
            symbol = self.system.symbols.get(symbol_id)
            if symbol and value in symbol.signs:
                return True
        return False

    def _parse_selector(self, expr: SExpression) -> Selector:
        """Parses selectors such as `symbol:dog` or `wigame:wg1`."""

        atom = self._require_atom(expr, "selector")
        if ":" not in atom:
            raise ValueError("selector must use `kind:value` syntax")
        kind, value = atom.split(":", 1)
        if not value:
            raise ValueError("selector value cannot be empty")
        return Selector(kind=kind, value=value)

    def _normalize_selector_value(self, selector: Selector) -> str:
        """Normalizes selector values against the current system ids."""

        value = selector.value
        if selector.kind == "wigame":
            if value in self.system.wigames:
                return value
            prefixed = f"wigame:{value}"
            if prefixed in self.system.wigames:
                return prefixed
        return value

    def _parse_axis(self, expr: SExpression, expected_name: str) -> list[str]:
        if not isinstance(expr, list) or len(expr) < 2:
            raise ValueError(f"{expected_name} must use `({expected_name} item...)` form")
        axis_name = self._require_atom(expr[0], expected_name)
        if axis_name != expected_name:
            raise ValueError(f"expected `{expected_name}` axis declaration")
        return [self._require_atom(item, expected_name) for item in expr[1:]]

    def _require_atom(self, expr: SExpression, label: str) -> str:
        """Ensures a node is a single atom."""

        if isinstance(expr, list):
            raise ValueError(f"{label} must be an atom")
        return expr
