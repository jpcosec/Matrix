"""Logical relation definition."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .relations import RelationAlgebra


@dataclass
class Relation:
    """Describes the logical properties of a relation token."""

    relation_id: str
    name: str
    algebra: RelationAlgebra = field(default_factory=RelationAlgebra)
    transitive: bool = False
    associative: bool = False
    distributive: bool = False
    commutative: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Normalizes legacy boolean flags into one explicit algebra profile."""

        legacy = RelationAlgebra(
            transitive=self.transitive,
            associative=self.associative,
            distributive=self.distributive,
            commutative=self.commutative,
        )
        if self.algebra == RelationAlgebra():
            self.algebra = legacy
        else:
            self.transitive = self.algebra.transitive
            self.associative = self.algebra.associative
            self.distributive = self.algebra.distributive
            self.commutative = self.algebra.commutative

    @property
    def semantics(self) -> RelationAlgebra:
        """Returns the explicit operational profile of the relation."""

        return self.algebra
