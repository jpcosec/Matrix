"""Binary Boolean function basis for the kernel."""

from __future__ import annotations

from dataclasses import dataclass


ROW_ORDER = ((True, True), (True, False), (False, True), (False, False))


@dataclass(frozen=True)
class BinaryBooleanFunction:
    """One binary Boolean function with named and bitwise identity."""

    function_id: str
    canonical_name: str
    aliases: tuple[str, ...]
    bits: str
    truth_rows: tuple[bool, bool, bool, bool]

    def evaluate(self, left: bool, right: bool) -> bool:
        """Evaluates the function on one Boolean pair."""

        index = ROW_ORDER.index((left, right))
        return self.truth_rows[index]


FUNCTIONS_BY_ID = {
    function.function_id: function
    for function in (
        BinaryBooleanFunction("f1", "top", ("true", "tautology"), "1111", (True, True, True, True)),
        BinaryBooleanFunction("f2", "or", ("disjunction",), "1110", (True, True, True, False)),
        BinaryBooleanFunction("f3", "left-implied-by-right", ("reverse-implies", "b-implies-a"), "1101", (True, True, False, True)),
        BinaryBooleanFunction("f4", "left", ("left-projection",), "1100", (True, True, False, False)),
        BinaryBooleanFunction("f5", "if", ("implies", "conditional"), "1011", (True, False, True, True)),
        BinaryBooleanFunction("f6", "right", ("right-projection",), "1010", (True, False, True, False)),
        BinaryBooleanFunction("f7", "iff", ("biconditional", "equivalence"), "1001", (True, False, False, True)),
        BinaryBooleanFunction("f8", "and", ("conjunction",), "1000", (True, False, False, False)),
        BinaryBooleanFunction("f9", "nand", ("sheffer",), "0111", (False, True, True, True)),
        BinaryBooleanFunction("f10", "xor", ("exclusive-or",), "0110", (False, True, True, False)),
        BinaryBooleanFunction("f11", "not-right", ("neg-right",), "0101", (False, True, False, True)),
        BinaryBooleanFunction("f12", "not-implies", ("and-not-right", "a-and-not-b"), "0100", (False, True, False, False)),
        BinaryBooleanFunction("f13", "not-left", ("neg-left",), "0011", (False, False, True, True)),
        BinaryBooleanFunction("f14", "not-left-implied-by-right", ("not-reverse-implies", "not-a-and-b"), "0010", (False, False, True, False)),
        BinaryBooleanFunction("f15", "nor", ("peirce",), "0001", (False, False, False, True)),
        BinaryBooleanFunction("f16", "bottom", ("false", "contradiction"), "0000", (False, False, False, False)),
    )
}

FUNCTIONS_BY_NAME = {
    name: function
    for function in FUNCTIONS_BY_ID.values()
    for name in (function.canonical_name, *function.aliases)
}


def get_boolean_function(name_or_id: str) -> BinaryBooleanFunction:
    """Returns one binary Boolean function by id or alias."""

    if name_or_id in FUNCTIONS_BY_ID:
        return FUNCTIONS_BY_ID[name_or_id]
    if name_or_id in FUNCTIONS_BY_NAME:
        return FUNCTIONS_BY_NAME[name_or_id]
    raise KeyError(f"unknown Boolean function: {name_or_id}")
