"""Differential symbol support model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .name import Name


@dataclass
class Symbol:
    """Stores the signs and supports associated with a symbol."""

    symbol_id: str
    signs: set[str] = field(default_factory=set)
    supporting_fact_ids: set[str] = field(default_factory=set)
    supporting_wigame_ids: set[str] = field(default_factory=set)
    metadata: dict[str, Any] = field(default_factory=dict)

    def bind_name(self, name: Name) -> None:
        """Associates a language sign with the symbol."""

        self.signs.add(name.sign)

    def support(self, fact_id: str, wigame_id: str | None = None) -> None:
        """Registers fact and WiGame support for the symbol."""

        self.supporting_fact_ids.add(fact_id)
        if wigame_id:
            self.supporting_wigame_ids.add(wigame_id)
