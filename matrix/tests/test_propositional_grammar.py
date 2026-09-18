import pytest

from src.operational_model import (
    AndFormula,
    ConstantFormula,
    IfFormula,
    KernelAtom,
    NotFormula,
    OrFormula,
    RelationAtom,
    formula_precedence,
    parse_formula,
)


def test_parse_relation_atom_formula() -> None:
    formula = parse_formula("(es perro mamifero)")

    assert formula == RelationAtom("es", "perro", "mamifero")
    assert formula.to_sexpr() == "(es perro mamifero)"


def test_parse_kernel_atom_formula() -> None:
    formula = parse_formula("kern:dog-known")

    assert formula == KernelAtom("kern:dog-known")
    assert formula.to_sexpr() == "kern:dog-known"


def test_parse_constant_formula() -> None:
    assert parse_formula("true") == ConstantFormula("true")
    assert parse_formula("kern:false") == ConstantFormula("false")


def test_parse_nested_formula() -> None:
    formula = parse_formula("(if (and (es perro mamifero) kern:ready) (not kern:false))")

    assert formula == IfFormula(
        antecedent=AndFormula(
            (
                RelationAtom("es", "perro", "mamifero"),
                KernelAtom("kern:ready"),
            )
        ),
        consequent=NotFormula(ConstantFormula("false")),
    )


def test_parse_or_formula_is_nary() -> None:
    formula = parse_formula("(or kern:a kern:b kern:c)")

    assert formula == OrFormula(
        (
            KernelAtom("kern:a"),
            KernelAtom("kern:b"),
            KernelAtom("kern:c"),
        )
    )


def test_invalid_operator_arity_fails() -> None:
    with pytest.raises(ValueError, match="`and` expects at least two operands"):
        parse_formula("(and kern:a)")
    with pytest.raises(ValueError, match="`if` expects exactly two operands"):
        parse_formula("(if kern:a kern:b kern:c)")
    with pytest.raises(ValueError, match="`not` expects exactly one operand"):
        parse_formula("(not kern:a kern:b)")


def test_bare_atom_without_namespace_fails() -> None:
    with pytest.raises(ValueError, match="bare atoms must use the `kern:` namespace"):
        parse_formula("foo")


def test_precedence_policy_is_explicit() -> None:
    assert formula_precedence() == {"not": 3, "and": 2, "or": 1, "if": 0}
