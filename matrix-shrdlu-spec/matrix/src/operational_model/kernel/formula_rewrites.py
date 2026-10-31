"""Equivalence-preserving rewrites for kernel formulas."""

from __future__ import annotations

from .formulas import AndFormula, ConstantFormula, Formula, IfFormula, KernelAtom, NotFormula, OrFormula, RelationAtom


def simplify_formula(formula: Formula) -> Formula:
    """Applies local equivalence-preserving simplifications recursively."""

    if isinstance(formula, (KernelAtom, RelationAtom, ConstantFormula)):
        return formula
    if isinstance(formula, IfFormula):
        return simplify_formula(desugar_if(formula))
    if isinstance(formula, NotFormula):
        operand = simplify_formula(formula.operand)
        if isinstance(operand, ConstantFormula):
            return ConstantFormula("false" if operand.value == "true" else "true")
        if isinstance(operand, NotFormula):
            return simplify_formula(operand.operand)
        if isinstance(operand, AndFormula):
            return simplify_formula(OrFormula(tuple(NotFormula(item) for item in operand.operands)))
        if isinstance(operand, OrFormula):
            return simplify_formula(AndFormula(tuple(NotFormula(item) for item in operand.operands)))
        return NotFormula(operand)
    if isinstance(formula, AndFormula):
        return _simplify_and(formula)
    if isinstance(formula, OrFormula):
        return _simplify_or(formula)
    raise TypeError(f"unsupported formula type: {type(formula).__name__}")


def desugar_if(formula: Formula) -> Formula:
    """Rewrites implication as disjunction with negation."""

    if isinstance(formula, IfFormula):
        return OrFormula((NotFormula(formula.antecedent), formula.consequent))
    return formula


def sort_formula_operands(formula: Formula) -> Formula:
    """Canonicalizes child order for n-ary connectives."""

    if isinstance(formula, AndFormula):
        operands = tuple(sorted((sort_formula_operands(item) for item in formula.operands), key=lambda item: item.to_sexpr()))
        return AndFormula(operands)
    if isinstance(formula, OrFormula):
        operands = tuple(sorted((sort_formula_operands(item) for item in formula.operands), key=lambda item: item.to_sexpr()))
        return OrFormula(operands)
    if isinstance(formula, NotFormula):
        return NotFormula(sort_formula_operands(formula.operand))
    if isinstance(formula, IfFormula):
        return IfFormula(sort_formula_operands(formula.antecedent), sort_formula_operands(formula.consequent))
    return formula


def _simplify_and(formula: AndFormula) -> Formula:
    operands: list[Formula] = []
    for operand in formula.operands:
        simplified = simplify_formula(operand)
        if isinstance(simplified, ConstantFormula):
            if simplified.value == "false":
                return ConstantFormula("false")
            continue
        if isinstance(simplified, AndFormula):
            operands.extend(simplified.operands)
        else:
            operands.append(simplified)
    operands = _dedupe(operands)
    operands = [operand for operand in operands if not _absorbed_in_and(operand, operands)]
    if not operands:
        return ConstantFormula("true")
    if len(operands) == 1:
        return operands[0]
    return AndFormula(tuple(sorted(operands, key=lambda item: item.to_sexpr())))


def _simplify_or(formula: OrFormula) -> Formula:
    operands: list[Formula] = []
    for operand in formula.operands:
        simplified = simplify_formula(operand)
        if isinstance(simplified, ConstantFormula):
            if simplified.value == "true":
                return ConstantFormula("true")
            continue
        if isinstance(simplified, OrFormula):
            operands.extend(simplified.operands)
        else:
            operands.append(simplified)
    operands = _dedupe(operands)
    operands = [operand for operand in operands if not _absorbed_in_or(operand, operands)]
    if not operands:
        return ConstantFormula("false")
    if len(operands) == 1:
        return operands[0]
    return OrFormula(tuple(sorted(operands, key=lambda item: item.to_sexpr())))


def _dedupe(operands: list[Formula]) -> list[Formula]:
    seen: dict[str, Formula] = {}
    for operand in operands:
        seen[operand.to_sexpr()] = operand
    return list(seen.values())


def _absorbed_in_or(candidate: Formula, operands: list[Formula]) -> bool:
    if not isinstance(candidate, AndFormula):
        return False
    operand_set = {item.to_sexpr() for item in candidate.operands}
    return any(not isinstance(other, AndFormula) and other.to_sexpr() in operand_set for other in operands if other is not candidate)


def _absorbed_in_and(candidate: Formula, operands: list[Formula]) -> bool:
    if not isinstance(candidate, OrFormula):
        return False
    operand_set = {item.to_sexpr() for item in candidate.operands}
    return any(not isinstance(other, OrFormula) and other.to_sexpr() in operand_set for other in operands if other is not candidate)
