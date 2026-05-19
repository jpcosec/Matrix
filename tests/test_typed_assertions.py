from src.operational_model import RelationAtom, SymbolSpace, lower_typed_assertion


def test_equivalent_assertion_unifies_symbols() -> None:
    space = SymbolSpace()

    result = lower_typed_assertion(space, RelationAtom("equivalent", "canis-lupus-familiaris", "dog"))

    assert result.canonical_subject_symbol_id == result.canonical_object_symbol_id == "canis-lupus-familiaris"
    assert space.are_equivalent("dog", "canis-lupus-familiaris") is True


def test_instance_assertion_uses_canonicalized_symbols() -> None:
    space = SymbolSpace()
    lower_typed_assertion(space, RelationAtom("equivalent", "dog", "canis-lupus-familiaris"))

    result = lower_typed_assertion(space, RelationAtom("instance", "dog", "mammal"))

    assert result.canonical_subject_symbol_id == "canis-lupus-familiaris"
    assert result.canonical_object_symbol_id == "mammal"
    assert space.instances_of("mammal") == ("canis-lupus-familiaris",)


def test_equivalence_rewrites_existing_instance_sets() -> None:
    space = SymbolSpace()
    lower_typed_assertion(space, RelationAtom("instance", "dog", "mammal"))
    lower_typed_assertion(space, RelationAtom("instance", "canis-lupus-familiaris", "mammal"))

    lower_typed_assertion(space, RelationAtom("equivalent", "dog", "canis-lupus-familiaris"))

    assert space.instances_of("mammal") == ("canis-lupus-familiaris",)
