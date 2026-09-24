"""Tests for order axioms on RelationAlgebra."""

import pytest

from src.operational_model import Relation, RelationAlgebra
from src.operational_model.core.relations import RelationPairValidationError


def test_total_order_profile_is_classified_as_total_order() -> None:
    algebra = RelationAlgebra(
        transitive=True,
        irreflexive=True,
        antisymmetric=True,
        total=True,
    )

    assert algebra.is_strict_partial_order() is True
    assert algebra.is_total_order() is True


def test_profile_without_total_is_not_a_total_order() -> None:
    algebra = RelationAlgebra(
        transitive=True,
        irreflexive=True,
        antisymmetric=True,
        total=False,
    )

    assert algebra.is_strict_partial_order() is True
    assert algebra.is_total_order() is False


def test_strict_total_order_pairs_are_accepted() -> None:
    algebra = RelationAlgebra(antisymmetric=True, total=True)

    algebra.validate_pairs([("a", "b"), ("b", "c"), ("a", "c")])


def test_antisymmetric_total_profile_rejects_reversed_pair() -> None:
    algebra = RelationAlgebra(antisymmetric=True, total=True)

    with pytest.raises(RelationPairValidationError) as excinfo:
        algebra.validate_pairs([("a", "b"), ("b", "a"), ("b", "c"), ("a", "c")])

    assert "antisymmetric" in str(excinfo.value)


def test_antisymmetric_total_profile_rejects_self_loop() -> None:
    algebra = RelationAlgebra(irreflexive=True, antisymmetric=True, total=True)

    with pytest.raises(RelationPairValidationError) as excinfo:
        algebra.validate_pairs([("a", "a"), ("a", "b"), ("b", "c"), ("a", "c")])

    assert "irreflexive" in str(excinfo.value)


def test_antisymmetric_total_profile_rejects_missing_pair() -> None:
    algebra = RelationAlgebra(antisymmetric=True, total=True)

    with pytest.raises(RelationPairValidationError) as excinfo:
        algebra.validate_pairs([("a", "b"), ("b", "c")])

    assert "total" in str(excinfo.value)


def test_irreflexive_requires_distinct_operands() -> None:
    algebra = RelationAlgebra(irreflexive=True)

    assert algebra.requires_distinct_operands() is True
    assert RelationAlgebra().requires_distinct_operands() is False


def test_transitive_pairs_are_checked_for_closure() -> None:
    algebra = RelationAlgebra(transitive=True)

    with pytest.raises(RelationPairValidationError) as excinfo:
        algebra.validate_pairs([("a", "b"), ("b", "c")])

    assert "transitive" in str(excinfo.value)

    algebra.validate_pairs([("a", "b"), ("b", "c"), ("a", "c")])


def test_legacy_construction_still_behaves_as_before() -> None:
    relation = Relation("before", "is before", transitive=True)

    assert relation.semantics.transitive is True
    assert relation.semantics.is_strict_partial_order() is False
    assert relation.semantics.is_total_order() is False


def test_legacy_flags_still_normalize_into_algebra() -> None:
    relation = Relation(
        "peer",
        "is peer of",
        commutative=True,
        transitive=True,
    )

    assert relation.semantics == RelationAlgebra(commutative=True, transitive=True)
    assert relation.commutative is True
    assert relation.transitive is True


def test_new_relation_flags_normalize_into_algebra() -> None:
    relation = Relation(
        "less",
        "is less than",
        transitive=True,
        irreflexive=True,
        antisymmetric=True,
        total=True,
    )

    assert relation.semantics.is_total_order() is True
    assert relation.irreflexive is True
    assert relation.antisymmetric is True
    assert relation.total is True


def test_public_api_imports() -> None:
    from src.operational_model import Relation as PublicRelation
    from src.operational_model import RelationAlgebra as PublicRelationAlgebra

    assert PublicRelation is Relation
    assert PublicRelationAlgebra is RelationAlgebra
    assert issubclass(RelationPairValidationError, ValueError)


def test_unrelated_axioms_are_not_enforced() -> None:
    # Without antisymmetry, mirrored pairs are admissible.
    RelationAlgebra(irreflexive=True).validate_pairs([("a", "b"), ("b", "a")])
    # Without totality, unrelated nodes are admissible.
    RelationAlgebra(transitive=True, antisymmetric=True).validate_pairs([("a", "b"), ("b", "c"), ("a", "c")])
