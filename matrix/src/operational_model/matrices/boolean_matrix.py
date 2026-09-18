"""Shared base class for indexed matrices."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .._ids import new_id


@dataclass
class BooleanMatrix:
    """Provides indexed matrix access and serialization helpers."""

    row_axis: list[str]
    column_axis: list[str]
    values: list[list[Any]]
    matrix_id: str = field(default_factory=lambda: new_id("matrix"))
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validates matrix dimensions against both axes."""
        if len(self.values) != len(self.row_axis):
            raise ValueError("row axis length and values height mismatch")
        for row in self.values:
            if len(row) != len(self.column_axis):
                raise ValueError("column axis length and row width mismatch")

    @classmethod
    def filled(
        cls,
        row_axis: list[str],
        column_axis: list[str],
        fill: Any,
        matrix_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "BooleanMatrix":
        """Builds a matrix filled with a single repeated value."""
        vals = [[fill for _ in column_axis] for _ in row_axis]
        return cls(
            row_axis=list(row_axis),
            column_axis=list(column_axis),
            values=vals,
            matrix_id=matrix_id or new_id("matrix"),
            metadata=metadata or {},
        )

    def row_index(self, row_key: str) -> int:
        """Returns the numeric index for a row key."""
        return self.row_axis.index(row_key)

    def column_index(self, column_key: str) -> int:
        """Returns the numeric index for a column key."""
        return self.column_axis.index(column_key)

    def get(self, row_key: str, column_key: str) -> Any:
        """Reads a matrix cell by logical coordinates."""
        return self.values[self.row_index(row_key)][self.column_index(column_key)]

    def set(self, row_key: str, column_key: str, value: Any) -> None:
        """Writes a matrix cell by logical coordinates."""
        self.values[self.row_index(row_key)][self.column_index(column_key)] = value

    def row(self, row_key: str) -> dict[str, Any]:
        """Returns a row as a keyed dictionary."""
        r_idx = self.row_index(row_key)
        return {k: self.values[r_idx][i] for i, k in enumerate(self.column_axis)}

    def column(self, column_key: str) -> dict[str, Any]:
        """Returns a column as a keyed dictionary."""
        c_idx = self.column_index(column_key)
        return {k: self.values[i][c_idx] for i, k in enumerate(self.row_axis)}

    def to_dict(self) -> dict[str, Any]:
        """Serializes the matrix to a plain dictionary."""
        return {
            "matrix_id": self.matrix_id,
            "rows": list(self.row_axis),
            "columns": list(self.column_axis),
            "values": [list(row) for row in self.values],
            "metadata": dict(self.metadata),
        }

    def to_row_bitmasks(self) -> list[int]:
        """Converts matrix rows into integer bitmasks."""
        masks: list[int] = []
        for row in self.values:
            m = 0
            for idx, val in enumerate(row):
                if val and val != "0" and val != "U":
                    m |= 1 << idx
            masks.append(m)
        return masks

    def to_col_bitmasks(self) -> list[int]:
        """Converts matrix columns into integer bitmasks."""
        num_cols = len(self.column_axis)
        masks: list[int] = [0] * num_cols
        for r_idx, row in enumerate(self.values):
            for c_idx, val in enumerate(row):
                if val and val != "0" and val != "U":
                    masks[c_idx] |= 1 << r_idx
        return masks

    @classmethod
    def from_row_bitmasks(
        cls,
        row_axis: list[str],
        column_axis: list[str],
        masks: list[int],
        true_value: Any = True,
        false_value: Any = False,
    ) -> "BooleanMatrix":
        """Reconstructs a BooleanMatrix from integer row bitmasks."""
        vals: list[list[Any]] = []
        for mask in masks:
            row = [
                true_value if (mask & (1 << c_idx)) != 0 else false_value
                for c_idx in range(len(column_axis))
            ]
            vals.append(row)
        return cls(row_axis=list(row_axis), column_axis=list(column_axis), values=vals)

    def elementwise_and(self, other: "BooleanMatrix") -> "BooleanMatrix":
        """Computes Hadamard (elementwise AND) product of two matrices."""
        if self.row_axis != other.row_axis or self.column_axis != other.column_axis:
            raise ValueError("matrix dimensions mismatch for elementwise AND")
        vals = [
            [
                bool(a and b and a != "0" and b != "0")
                for a, b in zip(r1, r2)
            ]
            for r1, r2 in zip(self.values, other.values)
        ]
        return BooleanMatrix(list(self.row_axis), list(self.column_axis), vals)

    def elementwise_or(self, other: "BooleanMatrix") -> "BooleanMatrix":
        """Computes Hadamard (elementwise OR) disjunction of two matrices."""
        if self.row_axis != other.row_axis or self.column_axis != other.column_axis:
            raise ValueError("matrix dimensions mismatch for elementwise OR")
        vals = [
            [
                bool((a and a != "0") or (b and b != "0"))
                for a, b in zip(r1, r2)
            ]
            for r1, r2 in zip(self.values, other.values)
        ]
        return BooleanMatrix(list(self.row_axis), list(self.column_axis), vals)

    def bool_mult(self, other: "BooleanMatrix") -> "BooleanMatrix":
        """Returns the boolean matrix product using bitwise integer operations."""
        if self.column_axis != other.row_axis:
            raise ValueError("inner axes mismatch")
        row_masks = self.to_row_bitmasks()
        col_masks = other.to_col_bitmasks()
        vals = [
            [bool(r_mask & c_mask) for c_mask in col_masks]
            for r_mask in row_masks
        ]
        return BooleanMatrix(list(self.row_axis), list(other.column_axis), vals)

    def transpose(self) -> "BooleanMatrix":
        """Returns the transpose of the matrix."""
        vals = [list(col) for col in zip(*self.values)]
        return BooleanMatrix(list(self.column_axis), list(self.row_axis), vals)

    def collapse_similarity(self) -> "BooleanMatrix":
        """Computes self * self.transpose()."""
        return self.bool_mult(self.transpose())

    def recursive_power(self, steps: int = 3) -> "BooleanMatrix":
        """Computes the matrix power recursively."""
        res = self
        for _ in range(steps):
            res = res.bool_mult(res)
        return res

    def transitive_closure(self) -> "BooleanMatrix":
        """Computes the reflexive-transitive closure (self v self^2 v ... v self^N)."""
        if self.row_axis != self.column_axis:
            raise ValueError("transitive closure requires a square matrix")
        n = len(self.row_axis)
        identity_vals = [
            [
                True if r == c or bool(self.values[r][c]) else False
                for c in range(n)
            ]
            for r in range(n)
        ]
        res = BooleanMatrix(list(self.row_axis), list(self.column_axis), identity_vals)
        for _ in range(n.bit_length()):
            res = res.bool_mult(res)
        return res


