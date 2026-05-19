"""Truth-functional evaluation for kernel propositional formulas."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product

from .formulas import AndFormula, ConstantFormula, Formula, IfFormula, KernelAtom, NotFormula, OrFormula, RelationAtom

FormulaValuation = dict[str, bool]


@dataclass(frozen=True)
class FormulaClassification:
    """Global semantic classification of one formula."""

    kind: str
    satisfying_valuations: int
    total_valuations: int


def evaluate_formula(formula: Formula, valuation: FormulaValuation) -> bool:
    """Evaluates one formula from a propositional valuation."""

    if isinstance(formula, ConstantFormula):
        return formula.value == "true"
    if isinstance(formula, (KernelAtom, RelationAtom)):
        return _lookup_atom(formula.to_sexpr(), valuation)
    if isinstance(formula, NotFormula):
        return not evaluate_formula(formula.operand, valuation)
    if isinstance(formula, AndFormula):
        return all(evaluate_formula(operand, valuation) for operand in formula.operands)
    if isinstance(formula, OrFormula):
        return any(evaluate_formula(operand, valuation) for operand in formula.operands)
    if isinstance(formula, IfFormula):
        return (not evaluate_formula(formula.antecedent, valuation)) or evaluate_formula(
            formula.consequent, valuation
        )
    raise TypeError(f"unsupported formula type: {type(formula).__name__}")


def collect_atoms(formula: Formula) -> tuple[str, ...]:
    """Collects the atomic proposition keys referenced by a formula."""

    atoms: set[str] = set()
    _collect_atoms(formula, atoms)
    return tuple(sorted(atoms))


def iter_valuations(formula: Formula) -> list[FormulaValuation]:
    """Enumerates all propositional valuations for the atoms of a formula."""

    atoms = collect_atoms(formula)
    if not atoms:
        return [{}]
    return [dict(zip(atoms, assignment, strict=True)) for assignment in product([False, True], repeat=len(atoms))]


def classify_formula(formula: Formula) -> FormulaClassification:
    """Classifies a formula as tautology, contradiction, or contingency."""

    valuations = iter_valuations(formula)
    satisfying = sum(1 for valuation in valuations if evaluate_formula(formula, valuation))
    if satisfying == len(valuations):
        kind = "tautology"
    elif satisfying == 0:
        kind = "contradiction"
    else:
        kind = "contingency"
    return FormulaClassification(kind, satisfying, len(valuations))


def _collect_atoms(formula: Formula, atoms: set[str]) -> None:
    if isinstance(formula, (KernelAtom, RelationAtom)):
        atoms.add(formula.to_sexpr())
        return
    if isinstance(formula, ConstantFormula):
        return
    if isinstance(formula, NotFormula):
        _collect_atoms(formula.operand, atoms)
        return
    if isinstance(formula, (AndFormula, OrFormula)):
        for operand in formula.operands:
            _collect_atoms(operand, atoms)
        return
    if isinstance(formula, IfFormula):
        _collect_atoms(formula.antecedent, atoms)
        _collect_atoms(formula.consequent, atoms)
        return
    raise TypeError(f"unsupported formula type: {type(formula).__name__}")


def _lookup_atom(atom: str, valuation: FormulaValuation) -> bool:
    if atom not in valuation:
        raise KeyError(f"missing valuation for atom: {atom}")
    return valuation[atom]
