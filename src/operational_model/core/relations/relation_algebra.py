"""Operational algebra profile for relations."""

from __future__ import annotations

from dataclasses import dataclass

from ..proposition import Proposition


class RelationPairValidationError(ValueError):
    """Raised when a set of pairs violates a declared algebra axiom."""


@dataclass(frozen=True)
class RelationAlgebra:
    """Declares algebraic behavior attached to one relation."""

    transitive: bool = False
    associative: bool = False
    distributive: bool = False
    commutative: bool = False
    irreflexive: bool = False
    antisymmetric: bool = False
    total: bool = False

    def supports_commutative_equivalence(self) -> bool:
        """Reports whether `(R a b)` and `(R b a)` are interchangeable."""

        return self.commutative

    def supports_transitive_closure(self) -> bool:
        """Reports whether `(R a b)` and `(R b c)` may infer `(R a c)`."""

        return self.transitive

    def requires_symmetric_axes(self) -> bool:
        """Reports whether a relation expects matching subject/object spaces."""

        return self.commutative

    def is_strict_partial_order(self) -> bool:
        """Reports whether this profile describes a strict partial order."""

        return self.transitive and self.irreflexive and self.antisymmetric

    def is_total_order(self) -> bool:
        """Reports whether this profile describes a strict total order."""

        return self.is_strict_partial_order() and self.total

    def requires_distinct_operands(self) -> bool:
        """Reports whether `(R a a)` is not admissible for this profile."""

        return self.irreflexive

    def validate_pairs(self, pairs: list[tuple[str, str]]) -> None:
        """Validates a set of pairs against the declared axioms.

        Raises RelationPairValidationError (a ValueError) naming the first
        violated axiom. Rules are applied only for axioms the profile
        declares: irreflexive (no self-pairs), antisymmetric (no pair plus
        its reverse), total (every distinct pair has at least one direction),
        transitive (closure under composition).
        """

        facts = set(pairs)
        if self.irreflexive:
            for a, b in facts:
                if a == b:
                    raise RelationPairValidationError(
                        f"irreflexive violation: self-pair ({a}, {a}) is not admissible"
                    )
        if self.antisymmetric:
            for a, b in facts:
                if a != b and (b, a) in facts:
                    raise RelationPairValidationError(
                        f"antisymmetric violation: both ({a}, {b}) and ({b}, {a}) are present"
                    )
        if self.total:
            nodes = sorted({node for pair in facts for node in pair})
            for index, a in enumerate(nodes):
                for b in nodes[index + 1 :]:
                    if (a, b) not in facts and (b, a) not in facts:
                        raise RelationPairValidationError(
                            f"total violation: neither ({a}, {b}) nor ({b}, {a}) is present"
                        )
        if self.transitive:
            for a, b in facts:
                for c, d in facts:
                    if b == c and (a, d) not in facts:
                        raise RelationPairValidationError(
                            f"transitive violation: ({a}, {b}) and ({b}, {d}) imply ({a}, {d}) which is missing"
                        )

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
