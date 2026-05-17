"""Sense matrix implementation for WiGames."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .._ids import new_id
from ..core.sense_value import SenseValue
from .boolean_matrix import BooleanMatrix


@dataclass
class SiMatrix(BooleanMatrix):
    """Stores proposition sense indexed by subject and term."""

    @classmethod
    def pure(cls, row_axis: list[str], column_axis: list[str]) -> "SiMatrix":
        """Builds a sense matrix initialized as `sinnlos`."""

        return cls.filled(
            row_axis=row_axis,
            column_axis=column_axis,
            fill=SenseValue.SINNLOS.value,
            matrix_id=new_id("si"),
        )

    def to_dict(self) -> dict[str, Any]:
        payload = super().to_dict()
        payload["values"] = [
            "".join(
                "V"
                if v == SenseValue.SINNVOLL.value
                else "L"
                if v == SenseValue.SINNLOS.value
                else "U"
                for v in row
            )
            for row in self.values
        ]
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SiMatrix":
        raw = payload["values"]
        if raw and isinstance(raw[0], str):
            _map = {
                "V": SenseValue.SINNVOLL.value,
                "L": SenseValue.SINNLOS.value,
                "U": SenseValue.UNSINNIG.value,
            }
            values = [[_map[ch] for ch in row] for row in raw]
        else:
            values = raw
        return cls(
            row_axis=payload["rows"],
            column_axis=payload["columns"],
            values=values,
            matrix_id=payload.get("matrix_id", new_id("si")),
            metadata=payload.get("metadata", {}),
        )

    def is_pure(self) -> bool:
        """Reports whether the matrix contains no `unsinnig` cells."""

        return all(
            value != SenseValue.UNSINNIG.value
            for row_key in self.row_axis
            for value in self.row(row_key).values()
        )
