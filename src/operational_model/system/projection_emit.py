"""Inverse projection: WiGame and matrix state back into canonical s-expressions.

The forward arrow already exists: `RuleMatrixCompiler.compile()` and
`parse_formula()` go s-expression -> matrix/formula, and `SExpressionRuntime`
goes s-expression -> system. This module is the missing inverse: it recovers
labelled `(R a b)` cells from Vi/Si using the row/column axes they already
carry, and emits the ordered s-expression stream that rebuilds a WiGame (or a
whole LogicalSystem) when fed to `SExpressionRuntime.evaluate()` one by one.
"""

from __future__ import annotations

from ..core.sense_value import SenseValue
from ..core.truth_value import TruthValue


def matrix_to_s_expressions(vi, si, relation_id: str) -> list[str]:
    """Recovers every TRUE-and-sinnvoll cell as an `(R a b)` s-expression.

    Walks `vi.row_axis` (outer) by `vi.column_axis` (inner); a cell is emitted
    only when `vi.values[i][j]` is TRUE and `si.values[i][j]` is SINNVOLL.
    Output is deterministic (row-major order) with no duplicates.
    """

    vi_shape = (len(vi.row_axis), len(vi.column_axis))
    si_shape = (len(si.row_axis), len(si.column_axis))
    if (
        vi.row_axis != si.row_axis
        or vi.column_axis != si.column_axis
        or vi_shape != si_shape
    ):
        raise ValueError(
            f"matrix shape mismatch: vi {vi_shape}, si {si_shape}"
        )
    emitted: list[str] = []
    for i, subject in enumerate(vi.row_axis):
        for j, obj in enumerate(vi.column_axis):
            if (
                vi.values[i][j] == TruthValue.TRUE.value
                and si.values[i][j] == SenseValue.SINNVOLL.value
            ):
                emitted.append(f"({relation_id} {subject} {obj})")
    return emitted


def wigame_to_s_expressions(wigame, *, sequence: list[str] | None = None) -> list[str]:
    """Emits the ordered s-expressions that rebuild one WiGame.

    Order: one `(create relation <R> <R>)` per relation, one
    `(create symbol <s> <s>)` per axis symbol, `(create li ...)` with the axes
    in their Li-space order (never sorted), `(create wigame ...)`, then one
    `(assert ...)` per TRUE fact. Relations and symbols are sorted
    lexicographically; asserts are sorted by subject then object, unless
    `sequence` is given, in which case the stable sort only uses each fact's
    subject position inside `sequence` (absent subjects go last).
    """

    relation_id = wigame.li.relation_id
    lines = [f"(create relation {relation_id} {relation_id})"]
    for symbol in sorted(set(wigame.li.axis_a) | set(wigame.li.axis_b)):
        lines.append(f"(create symbol {symbol} {symbol})")
    axis_a = " ".join(wigame.li.axis_a)
    axis_b = " ".join(wigame.li.axis_b)
    lines.append(
        f"(create li {wigame.li.li_id} {relation_id} (axis-a {axis_a}) (axis-b {axis_b}))"
    )
    lines.append(f"(create wigame {wigame.wigame_id} {wigame.li.li_id})")
    facts = [fact for fact in wigame.facts.values() if fact.truth == TruthValue.TRUE]
    facts.sort(
        key=lambda fact: (
            fact.proposition.subject_symbol_id,
            fact.proposition.object_symbol_id,
        )
    )
    if sequence:
        positions = {symbol: index for index, symbol in enumerate(sequence)}
        facts.sort(
            key=lambda fact: positions.get(
                fact.proposition.subject_symbol_id, len(sequence)
            )
        )
    lines.extend(
        f"(assert {wigame.wigame_id} {fact.proposition.sexpr()})" for fact in facts
    )
    return lines


def system_to_s_expressions(system) -> list[str]:
    """Concatenates the projection of every WiGame ordered by wigame_id."""

    lines: list[str] = []
    for wigame in sorted(system.wigames.values(), key=lambda item: item.wigame_id):
        lines.extend(wigame_to_s_expressions(wigame))
    return lines
