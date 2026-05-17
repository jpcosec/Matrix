"""Search vector implementation for local WiGame queries."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .._ids import new_id
from ..matrices.boolean_matrix import BooleanMatrix


@dataclass
class SearchVector:
    """Marks requested terms inside a WiGame column axis."""

    wigame_id: str
    terms: list[str]
    vector_id: str = field(default_factory=lambda: new_id("pi"))
    metadata: dict[str, Any] = field(default_factory=dict)

    def active_terms(self, available_columns: list[str]) -> list[str]:
        """Validates and returns the active search terms."""

        unknown = [term for term in self.terms if term not in available_columns]
        if unknown:
            raise KeyError(f"unknown search terms: {unknown}")
        return list(self.terms)

    def as_matrix(self, column_axis: list[str]) -> BooleanMatrix:
        """Materializes the search vector as a single-row matrix."""

        active = set(self.active_terms(column_axis))
        return BooleanMatrix(
            row_axis=[self.vector_id],
            column_axis=list(column_axis),
            values=[[column in active for column in column_axis]],
            matrix_id=self.vector_id,
            metadata={"kind": "search_vector", **self.metadata},
        )
