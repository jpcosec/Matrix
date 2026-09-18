"""Normal-form derivation for kernel formulas."""

from __future__ import annotations

from .formula_rewrites import desugar_if, simplify_formula
from .formulas import AndFormula, ConstantFormula, Formula, IfFormula, NotFormula, OrFormula


def to_nnf(formula: Formula) -> Formula:
    """Converts a formula to negation normal form."""

    if isinstance(formula, IfFormula):
        return to_nnf(desugar_if(formula))
    if isinstance(formula, NotFormula):
        operand = formula.operand
        if isinstance(operand, IfFormula):
            return to_nnf(NotFormula(desugar_if(operand)))
        if isinstance(operand, ConstantFormula):
            return ConstantFormula("false" if operand.value == "true" else "true")
        if isinstance(operand, NotFormula):
            return to_nnf(operand.operand)
        if isinstance(operand, AndFormula):
            return AndOrFactory.or_(*(to_nnf(NotFormula(item)) for item in operand.operands))
        if isinstance(operand, OrFormula):
            return AndOrFactory.and_(*(to_nnf(NotFormula(item)) for item in operand.operands))
        return NotFormula(to_nnf(operand))
    if isinstance(formula, AndFormula):
        return AndOrFactory.and_(*(to_nnf(item) for item in formula.operands))
    if isinstance(formula, OrFormula):
        return AndOrFactory.or_(*(to_nnf(item) for item in formula.operands))
    return formula


def to_cnf(formula: Formula) -> Formula:
    """Converts a formula to conjunctive normal form."""

    return simplify_formula(_cnf_from_nnf(to_nnf(formula)))


def to_dnf(formula: Formula) -> Formula:
    """Converts a formula to disjunctive normal form."""

    return simplify_formula(_dnf_from_nnf(to_nnf(formula)))


def _cnf_from_nnf(formula: Formula) -> Formula:
    if isinstance(formula, AndFormula):
        return AndOrFactory.and_(*(_cnf_from_nnf(item) for item in formula.operands))
    if isinstance(formula, OrFormula):
        operands = [_cnf_from_nnf(item) for item in formula.operands]
        current = operands[0]
        for operand in operands[1:]:
            current = _distribute_or_over_and(current, operand)
        return current
    return formula


def _dnf_from_nnf(formula: Formula) -> Formula:
    if isinstance(formula, OrFormula):
        return AndOrFactory.or_(*(_dnf_from_nnf(item) for item in formula.operands))
    if isinstance(formula, AndFormula):
        operands = [_dnf_from_nnf(item) for item in formula.operands]
        current = operands[0]
        for operand in operands[1:]:
            current = _distribute_and_over_or(current, operand)
        return current
    return formula


def _distribute_or_over_and(left: Formula, right: Formula) -> Formula:
    if isinstance(left, AndFormula):
        return AndOrFactory.and_(*(_distribute_or_over_and(item, right) for item in left.operands))
    if isinstance(right, AndFormula):
        return AndOrFactory.and_(*(_distribute_or_over_and(left, item) for item in right.operands))
    return AndOrFactory.or_(left, right)


def _distribute_and_over_or(left: Formula, right: Formula) -> Formula:
    if isinstance(left, OrFormula):
        return AndOrFactory.or_(*(_distribute_and_over_or(item, right) for item in left.operands))
    if isinstance(right, OrFormula):
        return AndOrFactory.or_(*(_distribute_and_over_or(left, item) for item in right.operands))
    return AndOrFactory.and_(left, right)


class AndOrFactory:
    """Small helper for normalized connective construction."""

    @staticmethod
    def and_(*operands: Formula) -> Formula:
        return simplify_formula(AndFormula(tuple(operands)))

    @staticmethod
    def or_(*operands: Formula) -> Formula:
        return simplify_formula(OrFormula(tuple(operands)))
