from src.operational_model import (
    KERNEL_CONNECTIVES,
    KERNEL_META_RELATIONS,
    WI_RELATION_FAMILIES,
    classify_symbol,
    is_kernel_symbol,
)


def test_kernel_sets_cover_current_candidate_space() -> None:
    candidate_space = {
        "instance",
        "has_property",
        "in_state",
        "event1",
        "event2",
        "event3",
        "part_of",
        "depends_on",
        "causes",
        "precedes",
        "equivalent",
        "and",
        "or",
        "not",
        "if",
    }
    classified = KERNEL_CONNECTIVES | KERNEL_META_RELATIONS | WI_RELATION_FAMILIES
    assert candidate_space == classified


def test_instance_and_equivalent_are_kernel_meta_relations() -> None:
    assert classify_symbol("instance").layer == "kernel"
    assert classify_symbol("instance").role == "meta-relation"
    assert classify_symbol("equivalent").layer == "kernel"
    assert is_kernel_symbol("equivalent") is True


def test_logical_connectives_are_kernel_symbols() -> None:
    for symbol in ("and", "or", "not", "if"):
        policy = classify_symbol(symbol)
        assert policy.layer == "kernel"
        assert policy.role == "connective"
        assert policy.stability == "keep"


def test_domain_relations_stay_inside_wi() -> None:
    for symbol in ("has_property", "in_state", "part_of", "depends_on", "causes", "precedes"):
        policy = classify_symbol(symbol)
        assert policy.layer == "wi"
        assert policy.role == "relation-family"
        assert policy.stability == "keep"


def test_event_arity_helpers_are_wi_level_temporary_sugar() -> None:
    for symbol in ("event1", "event2", "event3"):
        policy = classify_symbol(symbol)
        assert policy.layer == "wi"
        assert policy.stability == "defer"
        assert "temporary sugar" in policy.rationale
