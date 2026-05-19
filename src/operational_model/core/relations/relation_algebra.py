"""Operational algebra profile for relations."""

from __future__ import annotations

from dataclasses import dataclass

from ..proposition import Proposition


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

    def requires_symmetric_axes(self) -> bool:
        """Reports whether a relation expects matching subject/object spaces."""

        return self.commutative

    def validate_axes(self, axis_a: list[str], axis_b: list[str]) -> tuple[bool, str | None]:
        """Checks whether one Li space is compatible with this algebra profile."""

        if self.requires_symmetric_axes() and set(axis_a) != set(axis_b):
            return False, "commutative relations require symmetric axes"
        return True, None

    def canonical_coordinate_pair(self, subject_symbol_id: str, object_symbol_id: str) -> tuple[str, str]:
        """Returns the canonical pair for fact identity comparisons."""

        if self.supports_commutative_equivalence():
            return tuple(sorted((subject_symbol_id, object_symbol_id)))
        return subject_symbol_id, object_symbol_id

    def proposition_identity_key(self, proposition: Proposition) -> tuple[str, str, str, str]:
        """Builds an identity key for a proposition under this algebra."""

        left, right = self.canonical_coordinate_pair(
            proposition.subject_symbol_id,
            proposition.object_symbol_id,
        )
        return proposition.relation_id, left, right, proposition.wigame_id

    def propositions_are_equivalent(self, left: Proposition, right: Proposition) -> bool:
        """Checks proposition identity under relation semantics."""

        return self.proposition_identity_key(left) == self.proposition_identity_key(right)

    def routing_hooks(self) -> tuple[str, ...]:
        """Returns the routing-facing hook names implied by this relation."""

        hooks: list[str] = []
        if self.commutative:
            hooks.append("symmetric-route")
        if self.transitive:
            hooks.append("closure-route")
        return tuple(hooks)

    def reduction_hooks(self) -> tuple[str, ...]:
        """Returns reduction-facing hook names implied by this relation."""

        hooks: list[str] = []
        if self.commutative:
            hooks.append("canonical-pair-reduction")
        if self.associative:
            hooks.append("grouping-reduction")
        if self.distributive:
            hooks.append("distribution-reduction")
        return tuple(hooks)
