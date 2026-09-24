"""Quantified rule schemas: `(if (es ?x verdura) (es ?x comestible))`.

Rules used to be **ground**. `tests/test_deduction.py` says so in its own
comment: the rule `(if (es x verdura) (es x comestible))` has `x` as the literal
symbol `"x"`, with a `Thing(Symbol("x"))` registered to make it work. That is not
a schema, it is one concrete fact-shaped rule, so "every vegetable is edible"
needed one rule per symbol.

This module adds the missing quantification as a **source transformation**: a
schema carries variables, `expand()` grounds it against the symbols actually
present in the worlds, and the existing ground engine
(`RuleMatrixCompiler` + `system.deduction`) runs unchanged. Nothing downstream
learns about variables, which is what keeps the matrix semantics intact.

A variable is any atom starting with `?`. The `kern:` namespace stays reserved
for kernel atoms and is never treated as a variable.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import TYPE_CHECKING, Iterable, Iterator

from ..language.s_expressions import SExpression, parse_s_expression
from .formulas import (
    AndFormula,
    ConstantFormula,
    Formula,
    IfFormula,
    KernelAtom,
    NotFormula,
    OrFormula,
    RelationAtom,
)

if TYPE_CHECKING:
    from ..system.logical_system import LogicalSystem

VARIABLE_PREFIX = "?"


def is_variable(token: str) -> bool:
    """Reports whether an atom is a rule variable such as `?x`."""

    return token.startswith(VARIABLE_PREFIX) and len(token) > 1


def variables_of(formula: Formula) -> tuple[str, ...]:
    """Returns the variables occurring in `formula`, in first-seen order."""

    seen: list[str] = []
    for token in _atoms_of(formula):
        if is_variable(token) and token not in seen:
            seen.append(token)
    return tuple(seen)


def _atoms_of(formula: Formula) -> Iterator[str]:
    """Yields every symbol-like token inside a formula."""

    if isinstance(formula, RelationAtom):
        yield formula.relation_id
        yield formula.subject_symbol_id
        yield formula.object_symbol_id
    elif isinstance(formula, NotFormula):
        yield from _atoms_of(formula.operand)
    elif isinstance(formula, (AndFormula, OrFormula)):
        for operand in formula.operands:
            yield from _atoms_of(operand)
    elif isinstance(formula, IfFormula):
        yield from _atoms_of(formula.antecedent)
        yield from _atoms_of(formula.consequent)
    elif isinstance(formula, (KernelAtom, ConstantFormula)):
        return


def substitute(formula: Formula, binding: dict[str, str]) -> Formula:
    """Returns `formula` with every bound variable replaced by its symbol."""

    if isinstance(formula, RelationAtom):
        return RelationAtom(
            relation_id=binding.get(formula.relation_id, formula.relation_id),
            subject_symbol_id=binding.get(
                formula.subject_symbol_id, formula.subject_symbol_id
            ),
            object_symbol_id=binding.get(
                formula.object_symbol_id, formula.object_symbol_id
            ),
        )
    if isinstance(formula, NotFormula):
        return NotFormula(substitute(formula.operand, binding))
    if isinstance(formula, AndFormula):
        return AndFormula(tuple(substitute(o, binding) for o in formula.operands))
    if isinstance(formula, OrFormula):
        return OrFormula(tuple(substitute(o, binding) for o in formula.operands))
    if isinstance(formula, IfFormula):
        return IfFormula(
            substitute(formula.antecedent, binding),
            substitute(formula.consequent, binding),
        )
    return formula


@dataclass(frozen=True)
class RuleSchema:
    """A rule with variables, plus the ground rules it expands into."""

    formula: Formula

    @property
    def variables(self) -> tuple[str, ...]:
        """Returns the variables this schema quantifies over."""

        return variables_of(self.formula)

    @property
    def is_ground(self) -> bool:
        """Reports whether the schema has no variables left."""

        return not self.variables

    def to_sexpr(self) -> str:
        """Returns the schema in canonical s-expression form."""

        return self.formula.to_sexpr()

    def bind(self, binding: dict[str, str]) -> Formula:
        """Grounds the schema with one explicit binding."""

        missing = [v for v in self.variables if v not in binding]
        if missing:
            raise ValueError(f"binding leaves {', '.join(missing)} unbound")
        return substitute(self.formula, binding)

    def expand(self, universe: Iterable[str]) -> list[Formula]:
        """Grounds the schema over every combination of `universe`.

        Deterministic: bindings follow the order of `universe` and the
        first-seen order of the variables. A ground schema expands to itself.
        """

        variables = self.variables
        if not variables:
            return [self.formula]
        symbols = list(dict.fromkeys(universe))
        if not symbols:
            return []
        grounded: list[Formula] = []
        seen: set[str] = set()
        for combination in product(symbols, repeat=len(variables)):
            binding = dict(zip(variables, combination))
            formula = substitute(self.formula, binding)
            sexpr = formula.to_sexpr()
            if sexpr in seen:
                continue
            seen.add(sexpr)
            grounded.append(formula)
        return grounded


def parse_schema(source: str | SExpression) -> RuleSchema:
    """Parses a rule that may carry `?variables`.

    `formulas.parse_formula` rejects bare atoms outside the `kern:` namespace, so
    variables are parsed here: each `?x` is read as a symbol position and only
    recognised as a variable by `is_variable`.
    """

    expr = parse_s_expression(source) if isinstance(source, str) else source
    return RuleSchema(_parse(expr))


def _parse(expr: SExpression) -> Formula:
    """Parses a formula allowing variables in symbol positions."""

    if isinstance(expr, list):
        if not expr:
            raise ValueError("empty list is not a well-formed schema")
        head = _atom(expr[0])
        if head == "not":
            if len(expr) != 2:
                raise ValueError("`not` expects exactly one operand")
            return NotFormula(_parse(expr[1]))
        if head in {"and", "or"}:
            if len(expr) < 3:
                raise ValueError(f"`{head}` expects at least two operands")
            operands = tuple(_parse(item) for item in expr[1:])
            return AndFormula(operands) if head == "and" else OrFormula(operands)
        if head == "if":
            if len(expr) != 3:
                raise ValueError("`if` expects exactly two operands")
            return IfFormula(_parse(expr[1]), _parse(expr[2]))
        if len(expr) == 3:
            return RelationAtom(
                relation_id=_atom(expr[0]),
                subject_symbol_id=_atom(expr[1]),
                object_symbol_id=_atom(expr[2]),
            )
        raise ValueError("unknown list shape for a rule schema")

    if expr in {"true", "false", "kern:true", "kern:false"}:
        return ConstantFormula("true" if expr.endswith("true") else "false")
    if expr.startswith("kern:"):
        return KernelAtom(expr)
    if is_variable(expr):
        raise ValueError("a bare variable is not a formula")
    raise ValueError(
        "bare atoms must use the `kern:` namespace; symbol atoms must use `(R a b)`"
    )


def _atom(expr: SExpression) -> str:
    """Requires an atom, not a nested list."""

    if isinstance(expr, list):
        raise ValueError("expected an atom, found a list")
    return expr


def system_universe(system: "LogicalSystem") -> list[str]:
    """Returns the symbols a schema may be grounded over, sorted."""

    universe: set[str] = set()
    for wigame in system.wigames.values():
        universe.update(wigame.axis_a)
        universe.update(wigame.axis_b)
    return sorted(universe)


def expand_for_system(schema: RuleSchema, system: "LogicalSystem") -> list[Formula]:
    """Grounds a schema over the symbols present in a system's worlds."""

    return schema.expand(system_universe(system))
