from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ._ids import new_id
from .proposition import Proposition
from .truth_value import TruthValue


@dataclass
class Fact:
    proposition: Proposition
    truth: TruthValue
    fact_id: str = field(default_factory=lambda: new_id("fact"))
    evidence: dict[str, Any] = field(default_factory=dict)
