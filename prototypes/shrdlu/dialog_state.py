"""Minimal dialogue state for the SHRDLU prototype."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DialogState:
    """Tracks recently resolved referents for pronoun handling."""

    last_referents: tuple[str, ...] = field(default_factory=tuple)

    def remember(self, *symbol_ids: str) -> None:
        """Stores the latest resolved referents."""

        self.last_referents = tuple(symbol_ids)

    def resolve_pronoun(self, referent: str) -> tuple[str, ...]:
        """Resolves a prototype pronoun to the last known referents."""

        if referent in {"it", "them", "they"}:
            return self.last_referents
        return ()
