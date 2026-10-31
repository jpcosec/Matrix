"""Fact model for propositions with truth assignments."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .._ids import new_id
from .evidence import make_evidence, validate_evidence
from .proposition import Proposition
from .truth_value import TruthValue


@dataclass
class Fact:
    """Represents an evaluated proposition with evidence metadata."""

    proposition: Proposition
    truth: TruthValue
    fact_id: str = field(default_factory=lambda: new_id("fact"))
    evidence: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Fills evidence defaults and validates any provided payload."""

        if not self.evidence:
            self.evidence = make_evidence()
            return
        validate_evidence(self.evidence)
        self.evidence.setdefault("tier", "observed")
        self.evidence.setdefault("curation", "confirmed")
        self.evidence.setdefault("history", [])
