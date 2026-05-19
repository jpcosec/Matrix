"""Runtime evaluation for the first canonical s-expression slice."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..core.fact import Fact
from ..core.li_space import LiSpace
from ..core.name import Name
from ..core.proposition import Proposition
from ..core.relation import Relation
from ..core.symbol import Symbol
from ..core.thing import Thing
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
        if head == "create":
            return self._eval_create(expr[1:])
        if head == "ingest":
            return self._eval_ingest(expr[1:])
        if head == "return":
            return self._eval_return(expr[1:])
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
