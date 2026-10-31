"""Proposition value object for `(R a b)` statements."""

from __future__ import annotations

from dataclasses import dataclass, field

from .._ids import new_id


@dataclass(frozen=True)
class Proposition:
    """Represents a logical proposition inside a WiGame."""

    relation_id: str
    subject_symbol_id: str
    object_symbol_id: str
    wigame_id: str
    proposition_id: str = field(default_factory=lambda: new_id("prop"))

    def sexpr(self) -> str:
        """Returns the proposition encoded as an s-expression."""

        return f"({self.relation_id} {self.subject_symbol_id} {self.object_symbol_id})"
