from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .name import Name
from .symbol import Symbol


@dataclass
class Thing:
    symbol: Symbol
    name: Name
    aliases: set[str] = field(default_factory=set)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.symbol.bind_name(self.name)
        for alias in self.aliases:
            self.symbol.signs.add(alias)

    @property
    def symbol_id(self) -> str:
        return self.symbol.symbol_id
