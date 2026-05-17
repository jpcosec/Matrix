from __future__ import annotations

from dataclasses import dataclass, field

from ._ids import new_id


@dataclass(frozen=True)
class Proposition:
    relation_id: str
    subject_symbol_id: str
    object_symbol_id: str
    wigame_id: str
    proposition_id: str = field(default_factory=lambda: new_id("prop"))

    def sexpr(self) -> str:
        return f"({self.relation_id} {self.subject_symbol_id} {self.object_symbol_id})"
