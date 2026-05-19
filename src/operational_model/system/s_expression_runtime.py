"""Runtime evaluation for the first canonical s-expression slice."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..core.fact import Fact
from ..core.proposition import Proposition
from ..core.truth_value import TruthValue
from ..language.s_expressions import SExpression, parse_s_expression
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
        if head == "return":
            return self._eval_return(expr[1:])
        raise ValueError(f"unsupported operation: {head}")

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
        self.system.add_fact(Fact(proposition=proposition, truth=TruthValue.TRUE))
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
        if target != "facts":
            raise ValueError(f"unsupported return target: {target}")
        selectors = [self._parse_selector(arg) for arg in args[1:]]
        groups = [group for group in self._fact_groups(selectors) if group["facts"]]
        return OperationResult(status="accept", payload={"groups": groups})

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

    def _require_atom(self, expr: SExpression, label: str) -> str:
        """Ensures a node is a single atom."""

        if isinstance(expr, list):
            raise ValueError(f"{label} must be an atom")
        return expr
