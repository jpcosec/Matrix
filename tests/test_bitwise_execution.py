from src.operational_model import (
    bit_not,
    build_truth_table_masks,
    constant_mask,
    evaluate_formula,
    evaluate_formula_mask,
    iter_valuations,
    mask_popcount,
    normalize_mask_family,
    parse_formula,
)


def test_build_truth_table_masks_returns_one_mask_per_atom() -> None:
    formula = parse_formula("(if kern:p kern:q)")

    atoms, masks, width = build_truth_table_masks(formula)

    assert atoms == ("kern:p", "kern:q")
    assert width == 4
    assert masks["kern:p"] == 0b1100
    assert masks["kern:q"] == 0b1010


def test_mask_evaluation_matches_scalar_truth_table() -> None:
    formula = parse_formula("(if (and kern:p kern:q) (or kern:r (not kern:q)))")
    atoms, masks, width = build_truth_table_masks(formula)

    mask_result = evaluate_formula_mask(formula, masks, width)
    valuations = iter_valuations(formula)
    scalar_bits = 0
    for index, valuation in enumerate(valuations):
        if evaluate_formula(formula, valuation):
            scalar_bits |= 1 << index

    assert atoms == ("kern:p", "kern:q", "kern:r")
    assert mask_result == scalar_bits


def test_constant_and_negation_masks_propagate_correctly() -> None:
    width = 4
    assert constant_mask(True, width) == 0b1111
    assert constant_mask(False, width) == 0b0000
    assert bit_not(0b1010, width) == 0b0101
    assert mask_popcount(0b1011) == 3


def test_normalize_mask_family_deduplicates_and_sorts() -> None:
    assert normalize_mask_family([0b0011, 0b1111, 0b0011, 0b0000]) == (0, 3, 15)
