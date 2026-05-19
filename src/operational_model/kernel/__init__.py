"""Kernel symbol policy for Matrix."""

from .boolean_functions import (
    FUNCTIONS_BY_ID,
    FUNCTIONS_BY_NAME,
    ROW_ORDER,
    BinaryBooleanFunction,
    get_boolean_function,
)
from .formulas import (
    AndFormula,
    ConstantFormula,
    Formula,
    IfFormula,
    KernelAtom,
    NotFormula,
    OrFormula,
    RelationAtom,
    formula_precedence,
    parse_formula,
)
from .formula_evaluation import (
    FormulaClassification,
    classify_formula,
    collect_atoms,
    evaluate_formula,
    iter_valuations,
)
from .formula_inference import conjunction_elimination, disjunctive_syllogism, hypothetical_syllogism, modus_ponens
from .formula_normal_forms import to_cnf, to_dnf, to_nnf
from .formula_rewrites import desugar_if, simplify_formula, sort_formula_operands
from .symbol_policy import (
    KERNEL_CONNECTIVES,
    KERNEL_META_RELATIONS,
    WI_RELATION_FAMILIES,
    SymbolPolicy,
    classify_symbol,
    is_kernel_symbol,
)

__all__ = [
    "AndFormula",
    "BinaryBooleanFunction",
    "ConstantFormula",
    "FUNCTIONS_BY_ID",
    "FUNCTIONS_BY_NAME",
    "Formula",
    "FormulaClassification",
    "IfFormula",
    "KERNEL_CONNECTIVES",
    "KERNEL_META_RELATIONS",
    "KernelAtom",
    "NotFormula",
    "OrFormula",
    "RelationAtom",
    "ROW_ORDER",
    "WI_RELATION_FAMILIES",
    "classify_formula",
    "collect_atoms",
    "conjunction_elimination",
    "desugar_if",
    "disjunctive_syllogism",
    "evaluate_formula",
    "formula_precedence",
    "hypothetical_syllogism",
    "iter_valuations",
    "modus_ponens",
    "get_boolean_function",
    "parse_formula",
    "simplify_formula",
    "sort_formula_operands",
    "SymbolPolicy",
    "to_cnf",
    "to_dnf",
    "to_nnf",
    "classify_symbol",
    "is_kernel_symbol",
]
