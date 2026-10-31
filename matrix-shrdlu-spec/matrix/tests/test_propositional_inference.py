from src.operational_model import (
    conjunction_elimination,
    disjunctive_syllogism,
    hypothetical_syllogism,
    modus_ponens,
    parse_formula,
)


def test_modus_ponens_derives_consequent() -> None:
    premises = [parse_formula("(if kern:p kern:q)"), parse_formula("kern:p")]

    assert modus_ponens(premises) == {"kern:q"}


def test_conjunction_elimination_returns_conjuncts() -> None:
    premises = [parse_formula("(and kern:p kern:q)")]

    assert conjunction_elimination(premises) == {"kern:p", "kern:q"}


def test_disjunctive_syllogism_derives_remaining_disjunct() -> None:
    premises = [parse_formula("(or kern:p kern:q)"), parse_formula("(not kern:p)")]

    assert disjunctive_syllogism(premises) == {"kern:q"}


def test_hypothetical_syllogism_composes_implications() -> None:
    premises = [parse_formula("(if kern:p kern:q)"), parse_formula("(if kern:q kern:r)")]

    assert hypothetical_syllogism(premises) == {"(if kern:p kern:r)"}
