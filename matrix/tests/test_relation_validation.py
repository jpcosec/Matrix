from src.operational_model import Context, RelationAlgebra


def test_commutative_relation_requires_symmetric_axes() -> None:
    algebra = RelationAlgebra(commutative=True)

    valid, reason = algebra.validate_axes(["a", "b"], ["a", "b"])
    assert valid is True
    assert reason is None

    valid, reason = algebra.validate_axes(["a", "b"], ["x", "y"])
    assert valid is False
    assert reason == "commutative relations require symmetric axes"


def test_relation_algebra_exposes_routing_and_reduction_hooks() -> None:
    algebra = RelationAlgebra(commutative=True, transitive=True, distributive=True)

    assert algebra.routing_hooks() == ("symmetric-route", "closure-route")
    assert algebra.reduction_hooks() == ("canonical-pair-reduction", "distribution-reduction")


def test_context_routes_can_store_relation_semantics_hints() -> None:
    context = Context("ctx:root")

    route = context.route_to_context("ctx:next", semantics=("closure-route",))

    assert route.metadata == {"semantics": ["closure-route"]}
