"""First explicit inference rules over kernel formulas."""

from __future__ import annotations

from .formula_rewrites import simplify_formula, sort_formula_operands
from .formulas import AndFormula, Formula, IfFormula, NotFormula, OrFormula


def modus_ponens(premises: list[Formula]) -> set[str]:
    """Returns conclusions derivable by modus ponens."""

    premise_set = {_normalize(premise).to_sexpr(): _normalize(premise) for premise in premises}
    conclusions: set[str] = set()
    for premise in premise_set.values():
        if isinstance(premise, IfFormula) and premise.antecedent.to_sexpr() in premise_set:
            conclusions.add(simplify_formula(premise.consequent).to_sexpr())
    return conclusions


def conjunction_elimination(premises: list[Formula]) -> set[str]:
    """Returns direct conjuncts derivable from conjunctions."""

    conclusions: set[str] = set()
    for premise in premises:
        simplified = _normalize(premise)
        if isinstance(simplified, AndFormula):
            conclusions.update(item.to_sexpr() for item in simplified.operands)
    return conclusions


def disjunctive_syllogism(premises: list[Formula]) -> set[str]:
    """Returns conclusions derivable from `P∨Q` and `¬P` or `¬Q`."""

    premise_set = {_normalize(premise).to_sexpr(): _normalize(premise) for premise in premises}
    conclusions: set[str] = set()
    for premise in premise_set.values():
        if isinstance(premise, OrFormula) and len(premise.operands) == 2:
            left, right = premise.operands
            if NotFormula(left).to_sexpr() in premise_set:
                conclusions.add(right.to_sexpr())
            if NotFormula(right).to_sexpr() in premise_set:
                conclusions.add(left.to_sexpr())
    return conclusions


def hypothetical_syllogism(premises: list[Formula]) -> set[str]:
    """Returns implications derivable from `P→Q` and `Q→R`."""

    implications = [normalized for premise in premises if isinstance((normalized := _normalize(premise)), IfFormula)]
    conclusions: set[str] = set()
    for left in implications:
        for right in implications:
            if left is right:
                continue
            if left.consequent.to_sexpr() == right.antecedent.to_sexpr():
                conclusions.add(IfFormula(left.antecedent, right.consequent).to_sexpr())
    return conclusions


def _normalize(formula: Formula) -> Formula:
    """Canonicalizes child order without desugaring implications away."""

    return sort_formula_operands(formula)
