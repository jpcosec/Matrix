from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ._ids import new_id
from .boolean_matrix import BooleanMatrix
from .sense_value import SenseValue


@dataclass
class SiMatrix(BooleanMatrix):
    @classmethod
    def pure(cls, row_axis: list[str], column_axis: list[str]) -> "SiMatrix":
        return cls.filled(
            row_axis=row_axis,
            column_axis=column_axis,
            fill=SenseValue.SINNLOS.value,
            matrix_id=new_id("si"),
        )

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SiMatrix":
        return cls(
            row_axis=payload["rows"],
            column_axis=payload["columns"],
            values=payload["values"],
            matrix_id=payload.get("matrix_id", new_id("si")),
            metadata=payload.get("metadata", {}),
        )

    def is_pure(self) -> bool:
        for row_key in self.row_axis:
            row = self.row(row_key)
            if any(value == SenseValue.UNSINNIG.value for value in row.values()):
                return False
        return True
