from src.operational_model import parse_formula, simplify_formula, sort_formula_operands


def test_double_negation_reduces() -> None:
    assert simplify_formula(parse_formula("(not (not kern:p))")).to_sexpr() == "kern:p"


def test_de_morgan_rewrites_not_over_and() -> None:
    assert simplify_formula(parse_formula("(not (and kern:p kern:q))")).to_sexpr() == "(or (not kern:p) (not kern:q))"


def test_idempotence_and_identity_reduce_nary_connectives() -> None:
    assert simplify_formula(parse_formula("(and kern:p kern:p true)")).to_sexpr() == "kern:p"
    assert simplify_formula(parse_formula("(or kern:p kern:p false)")).to_sexpr() == "kern:p"


def test_absorption_reduces_dominated_subformula() -> None:
    assert simplify_formula(parse_formula("(or kern:p (and kern:p kern:q))")).to_sexpr() == "kern:p"
    assert simplify_formula(parse_formula("(and kern:p (or kern:p kern:q))")).to_sexpr() == "kern:p"


def test_sort_formula_operands_canonicalizes_commutative_children() -> None:
    assert sort_formula_operands(parse_formula("(and kern:b kern:a)")).to_sexpr() == "(and kern:a kern:b)"
