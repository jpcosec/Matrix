"""Truth matrix implementation for WiGames."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .._ids import new_id
from ..core.truth_value import TruthValue
from .boolean_matrix import BooleanMatrix


@dataclass
class ViMatrix(BooleanMatrix):
    """Stores truth values indexed by subject and term."""

    @classmethod
    def empty(cls, row_axis: list[str], column_axis: list[str]) -> "ViMatrix":
        """Builds an empty truth matrix filled with unknown values."""

        return cls.filled(
            row_axis=row_axis,
            column_axis=column_axis,
            fill=TruthValue.UNKNOWN.value,
            matrix_id=new_id("vi"),
        )

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ViMatrix":
        """Hydrates a truth matrix from serialized data."""

        return cls(
            row_axis=payload["rows"],
            column_axis=payload["columns"],
            values=payload["values"],
            matrix_id=payload.get("matrix_id", new_id("vi")),
            metadata=payload.get("metadata", {}),
        )

    def subjects_matching(self, search_vector: "SearchVector") -> list[str]:
        """Returns subjects whose requested terms are true."""

        requested = search_vector.active_terms(self.column_axis)
        return [
            row_key
            for row_key in self.row_axis
            if all(
                self.row(row_key)[column] == TruthValue.TRUE.value
                for column in requested
            )
        ]

    def tautological_columns(self) -> list[str]:
        """Returns columns that are true for every subject."""

        return [
            column_key
            for column_key in self.column_axis
            if self._column_is_tautological(column_key)
        ]

    def _column_is_tautological(self, column_key: str) -> bool:
        """Checks whether a column is true for the full row axis."""

        values = list(self.column(column_key).values())
        return bool(values) and all(value == TruthValue.TRUE.value for value in values)


from ..routing.search_vector import SearchVector
