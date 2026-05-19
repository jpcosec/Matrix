"""Operational algebra profile for relations."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RelationAlgebra:
    """Declares algebraic behavior attached to one relation."""

    transitive: bool = False
    associative: bool = False
    distributive: bool = False
    commutative: bool = False

    def supports_commutative_equivalence(self) -> bool:
        """Reports whether `(R a b)` and `(R b a)` are interchangeable."""

        return self.commutative

    def supports_transitive_closure(self) -> bool:
        """Reports whether `(R a b)` and `(R b c)` may infer `(R a c)`."""

        return self.transitive
