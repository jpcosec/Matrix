from src.operational_model import parse_formula, to_cnf, to_dnf, to_nnf


def test_to_nnf_desugars_if_and_pushes_negation() -> None:
    formula = parse_formula("(not (if kern:p kern:q))")

    assert to_nnf(formula).to_sexpr() == "(and (not kern:q) kern:p)"


def test_to_cnf_distributes_or_over_and() -> None:
    formula = parse_formula("(or kern:p (and kern:q kern:r))")

    assert to_cnf(formula).to_sexpr() == "(and (or kern:p kern:q) (or kern:p kern:r))"


def test_to_dnf_distributes_and_over_or() -> None:
    formula = parse_formula("(and kern:p (or kern:q kern:r))")

    assert to_dnf(formula).to_sexpr() == "(or (and kern:p kern:q) (and kern:p kern:r))"
