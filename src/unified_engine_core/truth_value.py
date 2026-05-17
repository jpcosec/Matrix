"""Truth value representation for the unified engine."""

from __future__ import annotations

from enum import IntEnum


class TruthValue(IntEnum):
    """Encodes four-valued logical truth for unified matrices."""

    T = 2
    F = 0
    U = 1
    N = -1

    def __str__(self) -> str:
        """Returns the compact single-letter truth label."""

        return {2: "T", 0: "F", 1: "U", -1: "N"}[self.value]

    @property
    def label(self) -> str:
        """Returns the long English truth label."""

        return {
            2: "TRUE",
            0: "FALSE",
            1: "UNKNOWN",
            -1: "NOT_APPLICABLE",
        }[self.value]
