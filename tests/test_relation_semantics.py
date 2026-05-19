from src.operational_model import Relation, RelationAlgebra


def test_legacy_relation_flags_build_algebra_profile() -> None:
    relation = Relation("linked", "is linked to", commutative=True, transitive=True)

    assert relation.semantics == RelationAlgebra(commutative=True, transitive=True)
    assert relation.commutative is True
    assert relation.transitive is True


def test_explicit_algebra_profile_backfills_legacy_flags() -> None:
    relation = Relation(
        "ordered",
        "is ordered with",
        algebra=RelationAlgebra(associative=True, distributive=True),
    )

    assert relation.associative is True
    assert relation.distributive is True
    assert relation.semantics.supports_commutative_equivalence() is False
    assert relation.semantics.supports_transitive_closure() is False
