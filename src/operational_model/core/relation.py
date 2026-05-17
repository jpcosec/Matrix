"""Logical relation definition."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Relation:
    """Describes the logical properties of a relation token."""

    relation_id: str
    name: str
    transitive: bool = False
    associative: bool = False
    distributive: bool = False
    commutative: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
