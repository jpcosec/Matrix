from src.operational_model import canonicalize_formula, dual_formula, parse_formula


def test_canonicalize_formula_sorts_and_simplifies() -> None:
    formula = parse_formula("(or false kern:b kern:a kern:a)")

    assert canonicalize_formula(formula).to_sexpr() == "(or kern:a kern:b)"


def test_dual_formula_swaps_and_or_and_constants() -> None:
    formula = parse_formula("(and kern:p (or kern:q true))")

    assert dual_formula(formula).to_sexpr() == "(or kern:p (and kern:q false))"
