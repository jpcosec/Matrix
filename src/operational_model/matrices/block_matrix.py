"""Block Matrix implementation for Omnirepresentation (WCi ⊕ Si ⊕ Vi)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .boolean_matrix import BooleanMatrix
from .si_matrix import SiMatrix
from .vi_matrix import ViMatrix


@dataclass
class BlockMatrix:
    """Represents a unified block matrix combining context routing, sense masks, and truth values."""

    context_matrix: BooleanMatrix  # WCi (Context x Context)
    sense_matrix: SiMatrix         # Si (Context x Terms/Facts)
    truth_matrix: ViMatrix         # Vi (Subjects x Terms/Facts)

    def to_global_matrix(self) -> BooleanMatrix:
        """Combines WCi, Si, Si^T, and Vi into a single unified global BooleanMatrix M."""
        c_rows = list(self.context_matrix.row_axis)
        f_cols = list(self.truth_matrix.column_axis)
        f_rows = list(self.truth_matrix.row_axis)

        global_rows = c_rows + f_rows
        global_cols = c_rows + f_cols

        # Initialize empty global values
        total_rows = len(global_rows)
        total_cols = len(global_cols)
        grid: list[list[Any]] = [[False for _ in range(total_cols)] for _ in range(total_rows)]

        # 1. Fill top-left block: WCi (Context x Context)
        for r_idx, r_key in enumerate(c_rows):
            for c_idx, c_key in enumerate(c_rows):
                grid[r_idx][c_idx] = self.context_matrix.get(r_key, c_key)

        # 2. Fill top-right block: Si (Context x Facts)
        for r_idx, r_key in enumerate(c_rows):
            for c_idx, c_key in enumerate(f_cols):
                grid[r_idx][len(c_rows) + c_idx] = self.sense_matrix.get(r_key, c_key) if c_key in self.sense_matrix.column_axis else False

        # 3. Fill bottom-left block: Si^T (Subjects x Context)
        si_trans = self.sense_matrix.transpose()
        for r_idx, r_key in enumerate(f_rows):
            for c_idx, c_key in enumerate(c_rows):
                grid[len(c_rows) + r_idx][c_idx] = si_trans.get(r_key, c_key) if r_key in si_trans.row_axis and c_key in si_trans.column_axis else False

        # 4. Fill bottom-right block: Vi (Subjects x Facts)
        for r_idx, r_key in enumerate(f_rows):
            for c_idx, c_key in enumerate(f_cols):
                grid[len(c_rows) + r_idx][len(c_rows) + c_idx] = self.truth_matrix.get(r_key, c_key)

        return BooleanMatrix(row_axis=global_rows, column_axis=global_cols, values=grid)

    def evaluate_operational(self) -> BooleanMatrix:
        """Computes the operational matrix W* = Vi AND Si for valid facts."""
        return self.truth_matrix.elementwise_and(self.sense_matrix)
