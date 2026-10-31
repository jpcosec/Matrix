from src.operational_model import Proposition, RelationAlgebra


def test_commutative_relation_treats_swapped_propositions_as_same_identity() -> None:
    algebra = RelationAlgebra(commutative=True)
    left = Proposition("linked", "a", "b", "wigame:links")
    right = Proposition("linked", "b", "a", "wigame:links")

    assert algebra.propositions_are_equivalent(left, right) is True


def test_non_commutative_relation_preserves_directional_identity() -> None:
    algebra = RelationAlgebra(commutative=False)
    left = Proposition("over", "a", "b", "wigame:stack")
    right = Proposition("over", "b", "a", "wigame:stack")

    assert algebra.propositions_are_equivalent(left, right) is False
