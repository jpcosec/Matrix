from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ._ids import new_id


@dataclass
class BooleanMatrix:
    row_axis: list[str]
    column_axis: list[str]
    values: list[list[Any]]
    matrix_id: str = field(default_factory=lambda: new_id("matrix"))
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if len(self.values) != len(self.row_axis):
            raise ValueError("row axis length and values height must match")
        for row in self.values:
            if len(row) != len(self.column_axis):
                raise ValueError("column axis length and row width must match")

    @classmethod
    def filled(
        cls,
        row_axis: list[str],
        column_axis: list[str],
        fill: Any,
        matrix_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "BooleanMatrix":
        return cls(
            row_axis=list(row_axis),
            column_axis=list(column_axis),
            values=[[fill for _ in column_axis] for _ in row_axis],
            matrix_id=matrix_id or new_id("matrix"),
            metadata=metadata or {},
        )

    def row_index(self, row_key: str) -> int:
        return self.row_axis.index(row_key)

    def column_index(self, column_key: str) -> int:
        return self.column_axis.index(column_key)

    def get(self, row_key: str, column_key: str) -> Any:
        return self.values[self.row_index(row_key)][self.column_index(column_key)]

    def set(self, row_key: str, column_key: str, value: Any) -> None:
        self.values[self.row_index(row_key)][self.column_index(column_key)] = value

    def row(self, row_key: str) -> dict[str, Any]:
        row_idx = self.row_index(row_key)
        return {
            column_key: self.values[row_idx][column_idx]
            for column_idx, column_key in enumerate(self.column_axis)
        }

    def column(self, column_key: str) -> dict[str, Any]:
        column_idx = self.column_index(column_key)
        return {
            row_key: self.values[row_idx][column_idx]
            for row_idx, row_key in enumerate(self.row_axis)
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "matrix_id": self.matrix_id,
            "rows": list(self.row_axis),
            "columns": list(self.column_axis),
            "values": [list(row) for row in self.values],
            "metadata": dict(self.metadata),
        }
