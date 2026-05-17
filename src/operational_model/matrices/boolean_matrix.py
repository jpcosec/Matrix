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

        self._validate_height()
        self._validate_width()

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

        return cls(
            row_axis=list(row_axis),
            column_axis=list(column_axis),
            values=[[fill for _ in column_axis] for _ in row_axis],
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

        row_idx = self.row_index(row_key)
        return {
            column_key: self.values[row_idx][column_idx]
            for column_idx, column_key in enumerate(self.column_axis)
        }

    def column(self, column_key: str) -> dict[str, Any]:
        """Returns a column as a keyed dictionary."""

        column_idx = self.column_index(column_key)
        return {
            row_key: self.values[row_idx][column_idx]
            for row_idx, row_key in enumerate(self.row_axis)
        }

    def to_dict(self) -> dict[str, Any]:
        """Serializes the matrix to a plain dictionary."""

        return {
            "matrix_id": self.matrix_id,
            "rows": list(self.row_axis),
            "columns": list(self.column_axis),
            "values": [list(row) for row in self.values],
            "metadata": dict(self.metadata),
        }

    def bool_mult(self, other: "BooleanMatrix") -> "BooleanMatrix":
        if self.column_axis != other.row_axis:
            raise ValueError(
                f"inner axes mismatch: {self.column_axis} vs {other.row_axis}"
            )
        result = []
        for i in range(len(self.row_axis)):
            row = []
            for k in range(len(other.column_axis)):
                acc = False
                for j in range(len(self.column_axis)):
                    if self.values[i][j] and other.values[j][k]:
                        acc = True
                        break
                row.append(acc)
            result.append(row)
        return BooleanMatrix(
            row_axis=list(self.row_axis),
            column_axis=list(other.column_axis),
            values=result,
            matrix_id=new_id("matrix"),
        )

    def transpose(self) -> "BooleanMatrix":
        return BooleanMatrix(
            row_axis=list(self.column_axis),
            column_axis=list(self.row_axis),
            values=[list(col) for col in zip(*self.values)],
            matrix_id=new_id("matrix"),
        )

    def _validate_height(self) -> None:
        """Ensures matrix height matches the row axis length."""

        if len(self.values) != len(self.row_axis):
            raise ValueError("row axis length and values height must match")

    def _validate_width(self) -> None:
        """Ensures every row matches the column axis length."""

        for row in self.values:
            if len(row) != len(self.column_axis):
                raise ValueError("column axis length and row width must match")
