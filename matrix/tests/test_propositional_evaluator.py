import pytest

from src.operational_model import classify_formula, collect_atoms, evaluate_formula, iter_valuations, parse_formula


def test_collect_atoms_distinguishes_kernel_and_relation_atoms() -> None:
    formula = parse_formula("(and (es perro mamifero) kern:ready)")

    assert collect_atoms(formula) == ("(es perro mamifero)", "kern:ready")


def test_evaluate_formula_implements_truth_functions() -> None:
    formula = parse_formula("(if (and kern:p kern:q) (or kern:r (not kern:q)))")

    assert evaluate_formula(
        formula,
        {"kern:p": True, "kern:q": True, "kern:r": False},
    ) is False
    assert evaluate_formula(
        formula,
        {"kern:p": False, "kern:q": True, "kern:r": False},
    ) is True


def test_iter_valuations_covers_boolean_space() -> None:
    formula = parse_formula("(or kern:p kern:q)")

    valuations = iter_valuations(formula)

    assert len(valuations) == 4
    assert {tuple(sorted(valuation.items())) for valuation in valuations} == {
        (("kern:p", False), ("kern:q", False)),
        (("kern:p", False), ("kern:q", True)),
        (("kern:p", True), ("kern:q", False)),
        (("kern:p", True), ("kern:q", True)),
    }


def test_formula_classification_detects_tautology() -> None:
    formula = parse_formula("(or kern:p (not kern:p))")

    classification = classify_formula(formula)

    assert classification.kind == "tautology"
    assert classification.satisfying_valuations == classification.total_valuations


def test_formula_classification_detects_contradiction() -> None:
    formula = parse_formula("(and kern:p (not kern:p))")

    classification = classify_formula(formula)

    assert classification.kind == "contradiction"
    assert classification.satisfying_valuations == 0


def test_formula_classification_detects_contingency() -> None:
    formula = parse_formula("(if kern:p kern:q)")

    classification = classify_formula(formula)

    assert classification.kind == "contingency"
    assert 0 < classification.satisfying_valuations < classification.total_valuations


def test_missing_atom_in_valuation_raises_keyerror() -> None:
    formula = parse_formula("(and kern:p kern:q)")

    with pytest.raises(KeyError):
        evaluate_formula(formula, {"kern:p": True})
