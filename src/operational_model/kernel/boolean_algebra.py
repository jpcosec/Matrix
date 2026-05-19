"""Boolean-algebra helpers for canonicalization and reduction."""

from __future__ import annotations

from .formula_rewrites import simplify_formula, sort_formula_operands
from .formulas import AndFormula, ConstantFormula, Formula, NotFormula, OrFormula


def canonicalize_formula(formula: Formula) -> Formula:
    """Returns a stable simplified canonical form."""

    return sort_formula_operands(simplify_formula(formula))


def dual_formula(formula: Formula) -> Formula:
    """Builds the Boolean dual of a formula."""

    if isinstance(formula, ConstantFormula):
        return ConstantFormula("false" if formula.value == "true" else "true")
    if isinstance(formula, NotFormula):
        return NotFormula(dual_formula(formula.operand))
    if isinstance(formula, AndFormula):
        return OrFormula(tuple(dual_formula(item) for item in formula.operands))
    if isinstance(formula, OrFormula):
        return AndFormula(tuple(dual_formula(item) for item in formula.operands))
    return formula


def clause_subsumes(left: Formula, right: Formula) -> bool:
    """Checks subsumption between disjunctive clauses or conjunctive terms."""

    left = canonicalize_formula(left)
    right = canonicalize_formula(right)
    if isinstance(left, OrFormula) and isinstance(right, OrFormula):
        return _sexpr_set(left.operands) <= _sexpr_set(right.operands)
    if isinstance(left, AndFormula) and isinstance(right, AndFormula):
        return _sexpr_set(left.operands) <= _sexpr_set(right.operands)
    return left.to_sexpr() == right.to_sexpr()


def reduce_cnf_subsumption(formula: Formula) -> Formula:
    """Removes subsumed clauses from a CNF-like conjunction of clauses."""

    formula = canonicalize_formula(formula)
    if not isinstance(formula, AndFormula):
        return formula
    clauses = list(formula.operands)
    kept = [
        clause
        for clause in clauses
        if not any(other is not clause and clause_subsumes(other, clause) for other in clauses)
    ]
    return canonicalize_formula(AndFormula(tuple(kept)))


def reduce_dnf_subsumption(formula: Formula) -> Formula:
    """Removes subsumed terms from a DNF-like disjunction of conjunctions."""

    formula = canonicalize_formula(formula)
    if not isinstance(formula, OrFormula):
        return formula
    terms = list(formula.operands)
    kept = [
        term
        for term in terms
        if not any(other is not term and clause_subsumes(other, term) for other in terms)
    ]
    return canonicalize_formula(OrFormula(tuple(kept)))


def _sexpr_set(items: tuple[Formula, ...]) -> set[str]:
    return {item.to_sexpr() for item in items}
