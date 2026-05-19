from src.operational_model import clause_subsumes, parse_formula, reduce_cnf_subsumption, reduce_dnf_subsumption


def test_clause_subsumption_detects_stronger_or_clause() -> None:
    assert clause_subsumes(parse_formula("(or kern:p kern:q)"), parse_formula("(or kern:p kern:q kern:r)")) is True


def test_reduce_cnf_subsumption_removes_redundant_clause() -> None:
    formula = parse_formula("(and (or kern:p kern:q) (or kern:p kern:q kern:r))")

    assert reduce_cnf_subsumption(formula).to_sexpr() == "(or kern:p kern:q)"


def test_reduce_dnf_subsumption_removes_redundant_term() -> None:
    formula = parse_formula("(or (and kern:p kern:q) (and kern:p kern:q kern:r))")

    assert reduce_dnf_subsumption(formula).to_sexpr() == "(and kern:p kern:q)"
