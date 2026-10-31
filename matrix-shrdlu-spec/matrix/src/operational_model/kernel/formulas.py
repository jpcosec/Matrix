"""Kernel-level propositional formulas over canonical s-expressions."""

from __future__ import annotations

from dataclasses import dataclass

from ..language.s_expressions import SExpression, parse_s_expression


@dataclass(frozen=True)
class Formula:
    """Base propositional formula."""

    def to_sexpr(self) -> str:
        raise NotImplementedError


@dataclass(frozen=True)
class RelationAtom(Formula):
    """Atomic proposition grounded in a symbolic relation `(R a b)`."""

    relation_id: str
    subject_symbol_id: str
    object_symbol_id: str

    def to_sexpr(self) -> str:
        return f"({self.relation_id} {self.subject_symbol_id} {self.object_symbol_id})"


@dataclass(frozen=True)
class KernelAtom(Formula):
    """Atomic proposition internal to the kernel namespace."""

    name: str

    def to_sexpr(self) -> str:
        return self.name


@dataclass(frozen=True)
class ConstantFormula(Formula):
    """Kernel constant formula."""

    value: str

    def to_sexpr(self) -> str:
        return self.value


@dataclass(frozen=True)
class NotFormula(Formula):
    """Unary negation formula."""

    operand: Formula

    def to_sexpr(self) -> str:
        return f"(not {self.operand.to_sexpr()})"


@dataclass(frozen=True)
class AndFormula(Formula):
    """N-ary conjunction."""

    operands: tuple[Formula, ...]

    def to_sexpr(self) -> str:
        return f"(and {' '.join(operand.to_sexpr() for operand in self.operands)})"


@dataclass(frozen=True)
class OrFormula(Formula):
    """N-ary disjunction."""

    operands: tuple[Formula, ...]

    def to_sexpr(self) -> str:
        return f"(or {' '.join(operand.to_sexpr() for operand in self.operands)})"


@dataclass(frozen=True)
class IfFormula(Formula):
    """Binary implication formula."""

    antecedent: Formula
    consequent: Formula

    def to_sexpr(self) -> str:
        return f"(if {self.antecedent.to_sexpr()} {self.consequent.to_sexpr()})"


def parse_formula(source: str | SExpression) -> Formula:
    """Parses one kernel propositional formula from s-expression input."""

    expr = parse_s_expression(source) if isinstance(source, str) else source
    return _parse_formula(expr)


def formula_precedence() -> dict[str, int]:
    """Returns the documented precedence order for non fully-parenthesized views."""

    return {"not": 3, "and": 2, "or": 1, "if": 0}


def _parse_formula(expr: SExpression) -> Formula:
    if isinstance(expr, list):
        if not expr:
            raise ValueError("empty list is not a well-formed formula")
        head = _require_atom(expr[0], "operator")
        if head == "not":
            if len(expr) != 2:
                raise ValueError("`not` expects exactly one operand")
            return NotFormula(_parse_formula(expr[1]))
        if head == "and":
            if len(expr) < 3:
                raise ValueError("`and` expects at least two operands")
            return AndFormula(tuple(_parse_formula(item) for item in expr[1:]))
        if head == "or":
            if len(expr) < 3:
                raise ValueError("`or` expects at least two operands")
            return OrFormula(tuple(_parse_formula(item) for item in expr[1:]))
        if head == "if":
            if len(expr) != 3:
                raise ValueError("`if` expects exactly two operands")
            return IfFormula(_parse_formula(expr[1]), _parse_formula(expr[2]))
        if len(expr) == 3:
            return RelationAtom(
                relation_id=_require_atom(expr[0], "relation id"),
                subject_symbol_id=_require_atom(expr[1], "subject symbol id"),
                object_symbol_id=_require_atom(expr[2], "object symbol id"),
            )
        raise ValueError("unknown list shape for propositional formula")

    if expr in {"true", "false", "kern:true", "kern:false"}:
        return ConstantFormula("true" if expr.endswith("true") else "false")
    if expr.startswith("kern:"):
        return KernelAtom(expr)
    raise ValueError(
        "bare atoms must use the `kern:` namespace; symbol-to-symbol atoms must use canonical `(R a b)` form"
    )


def _require_atom(expr: SExpression, label: str) -> str:
    if isinstance(expr, list):
        raise ValueError(f"{label} must be an atom")
    return expr
