from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .proposition import Proposition


@dataclass
class LiSpace:
    li_id: str
    axis_a: list[str]
    axis_b: list[str]
    relation_id: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def accepts(self, proposition: Proposition) -> bool:
        return (
            proposition.relation_id == self.relation_id
            and proposition.subject_symbol_id in self.axis_a
            and proposition.object_symbol_id in self.axis_b
        )
