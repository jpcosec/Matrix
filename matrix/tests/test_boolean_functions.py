from src.operational_model import FUNCTIONS_BY_ID, ROW_ORDER, get_boolean_function


def test_sixteen_binary_boolean_functions_are_registered() -> None:
    assert tuple(sorted(FUNCTIONS_BY_ID, key=lambda item: int(item[1:]))) == tuple(
        f"f{i}" for i in range(1, 17)
    )


def test_named_core_connectives_map_to_expected_bit_patterns() -> None:
    assert get_boolean_function("and").bits == "1000"
    assert get_boolean_function("or").bits == "1110"
    assert get_boolean_function("if").bits == "1011"
    assert get_boolean_function("iff").bits == "1001"
    assert get_boolean_function("nand").bits == "0111"
    assert get_boolean_function("nor").bits == "0001"
    assert get_boolean_function("xor").bits == "0110"


def test_row_order_is_explicit_and_stable() -> None:
    assert ROW_ORDER == ((True, True), (True, False), (False, True), (False, False))


def test_table_driven_evaluation_matches_truth_rows() -> None:
    implication = get_boolean_function("if")

    assert implication.evaluate(True, True) is True
    assert implication.evaluate(True, False) is False
    assert implication.evaluate(False, True) is True
    assert implication.evaluate(False, False) is True


def test_alias_lookup_supports_common_names() -> None:
    assert get_boolean_function("conditional") is get_boolean_function("if")
    assert get_boolean_function("equivalence") is get_boolean_function("iff")
    assert get_boolean_function("peirce") is get_boolean_function("nor")
