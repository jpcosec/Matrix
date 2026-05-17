from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ._ids import new_id
from .boolean_matrix import BooleanMatrix
from .truth_value import TruthValue


@dataclass
class ViMatrix(BooleanMatrix):
    @classmethod
    def empty(cls, row_axis: list[str], column_axis: list[str]) -> "ViMatrix":
        return cls.filled(
            row_axis=row_axis,
            column_axis=column_axis,
            fill=TruthValue.UNKNOWN.value,
            matrix_id=new_id("vi"),
        )

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ViMatrix":
        return cls(
            row_axis=payload["rows"],
            column_axis=payload["columns"],
            values=payload["values"],
            matrix_id=payload.get("matrix_id", new_id("vi")),
            metadata=payload.get("metadata", {}),
        )

    def subjects_matching(self, search_vector: "SearchVector") -> list[str]:
        requested = search_vector.active_terms(self.column_axis)
        matches: list[str] = []
        for row_key in self.row_axis:
            row = self.row(row_key)
            if all(row[column] == TruthValue.TRUE.value for column in requested):
                matches.append(row_key)
        return matches

    def tautological_columns(self) -> list[str]:
        tautologies: list[str] = []
        for column_key in self.column_axis:
            values = list(self.column(column_key).values())
            if values and all(value == TruthValue.TRUE.value for value in values):
                tautologies.append(column_key)
        return tautologies


from .search_vector import SearchVector
