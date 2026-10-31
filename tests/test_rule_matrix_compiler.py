"""Tests for RuleMatrixCompiler."""

from src.operational_model.kernel.rule_matrix import RuleMatrixCompiler
from src.operational_model.kernel.formulas import IfFormula, KernelAtom, NotFormula, OrFormula, RelationAtom


def test_compile_implications():
    p = KernelAtom("p")
    q = KernelAtom("q")
    r = KernelAtom("r")

    premises = [
        IfFormula(p, q),
        IfFormula(q, r),
    ]

    compiled = RuleMatrixCompiler.compile(premises)
    assert compiled.atoms == ("p", "q", "r")
    assert compiled.implication_matrix.get("p", "q") is True
    assert compiled.implication_matrix.get("q", "r") is True
    assert compiled.implication_matrix.get("p", "r") is False


def test_compile_clause_matrices():
    p = KernelAtom("p")
    q = KernelAtom("q")

    # Clause: (~p v q)
    clause1 = OrFormula((NotFormula(p), q))

    compiled = RuleMatrixCompiler.compile([clause1])
    assert compiled.positive_clause_matrix.get("clause_0", "q") is True
    assert compiled.negative_clause_matrix.get("clause_0", "p") is True
