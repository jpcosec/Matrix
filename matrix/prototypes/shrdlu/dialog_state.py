"""Dialogue state for the SHRDLU REPL: referents, focus and clarifications."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.operational_model import LogicalSystem

    from .spanish import Clarification


@dataclass
class DialogState:
    """Tracks recently resolved referents, the focused WiGame and pending questions."""

    last_referents: tuple[str, ...] = field(default_factory=tuple)
    focus_wigame: str | None = None
    last_subject: str | None = None
    last_object: str | None = None
    last_verb: str | None = None
    pending: "Clarification | None" = None
    system: "LogicalSystem | None" = None

    def remember(self, *symbol_ids: str) -> None:
        """Stores the latest resolved referents."""

        self.last_referents = tuple(symbol_ids)

    def resolve_pronoun(self, referent: str) -> tuple[str, ...]:
        """Resolves a prototype pronoun to the last known referents."""

        if referent in {"it", "them", "they"}:
            return self.last_referents
        return ()

    def answer(self, choice: str) -> str:
        """Resolves the pending clarification and returns its s-expression."""

        if self.pending is None:
            raise ValueError("no pending clarification")
        index = int(choice.strip()) - 1
        options = self.pending.options
        if not 0 <= index < len(options):
            raise ValueError(f"choice out of range: {choice!r}")
        sexpr = options[index]
        self.pending = None
        return sexpr

    def remember_turn(self, verb: str, subject: str, obj: str) -> None:
        """Stores the last resolved verb, subject and object for ellipsis."""

        self.last_verb = verb
        self.last_subject = subject
        self.last_object = obj
