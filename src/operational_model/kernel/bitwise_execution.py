"""Bitwise or mask-oriented execution for kernel formulas."""

from __future__ import annotations

from .formulas import AndFormula, ConstantFormula, Formula, IfFormula, KernelAtom, NotFormula, OrFormula, RelationAtom
from .formula_evaluation import collect_atoms, iter_valuations

MaskValuation = dict[str, int]


def build_truth_table_masks(formula: Formula) -> tuple[tuple[str, ...], MaskValuation, int]:
    """Builds one bit mask per atom over all valuations of the formula."""

    atoms = collect_atoms(formula)
    valuations = iter_valuations(formula)
    width = len(valuations)
    masks = {atom: 0 for atom in atoms}
    for index, valuation in enumerate(valuations):
        for atom, value in valuation.items():
            if value:
                masks[atom] |= 1 << index
    return atoms, masks, width


def evaluate_formula_mask(formula: Formula, valuation: MaskValuation, width: int) -> int:
    """Evaluates one formula over bit masks instead of scalar truth values."""

    if isinstance(formula, ConstantFormula):
        return constant_mask(formula.value == "true", width)
    if isinstance(formula, (KernelAtom, RelationAtom)):
        return _lookup_mask(formula.to_sexpr(), valuation)
    if isinstance(formula, NotFormula):
        return bit_not(evaluate_formula_mask(formula.operand, valuation, width), width)
    if isinstance(formula, AndFormula):
        return mask_reduce_and([evaluate_formula_mask(operand, valuation, width) for operand in formula.operands], width)
    if isinstance(formula, OrFormula):
        return mask_reduce_or([evaluate_formula_mask(operand, valuation, width) for operand in formula.operands])
    if isinstance(formula, IfFormula):
        left = evaluate_formula_mask(formula.antecedent, valuation, width)
        right = evaluate_formula_mask(formula.consequent, valuation, width)
        return mask_reduce_or([bit_not(left, width), right])
    raise TypeError(f"unsupported formula type: {type(formula).__name__}")


def constant_mask(value: bool, width: int) -> int:
    return ((1 << width) - 1) if value else 0


def bit_not(mask: int, width: int) -> int:
    return (~mask) & ((1 << width) - 1)


def mask_reduce_and(masks: list[int], width: int) -> int:
    if not masks:
        return constant_mask(True, width)
    current = constant_mask(True, width)
    for mask in masks:
        current &= mask
    return current


def mask_reduce_or(masks: list[int]) -> int:
    current = 0
    for mask in masks:
        current |= mask
    return current


def normalize_mask_family(masks: list[int]) -> tuple[int, ...]:
    return tuple(sorted(set(masks)))


def mask_popcount(mask: int) -> int:
    return mask.bit_count()


def _lookup_mask(atom: str, valuation: MaskValuation) -> int:
    if atom not in valuation:
        raise KeyError(f"missing mask valuation for atom: {atom}")
    return valuation[atom]
