"""Typed kernel assertions over symbol spaces."""

from __future__ import annotations

from dataclasses import dataclass

from .formulas import RelationAtom
from .symbol_spaces import SymbolSpace


@dataclass(frozen=True)
class TypedAssertionResult:
    """Stable result for one kernel meta-relation assertion."""

    relation_id: str
    subject_symbol_id: str
    object_symbol_id: str
    canonical_subject_symbol_id: str
    canonical_object_symbol_id: str


def lower_typed_assertion(space: SymbolSpace, atom: RelationAtom) -> TypedAssertionResult:
    """Operationalizes one `instance` or `equivalent` atom in the kernel."""

    if atom.relation_id == "equivalent":
        canonical = space.assert_equivalent(atom.subject_symbol_id, atom.object_symbol_id)
        return TypedAssertionResult(
            relation_id=atom.relation_id,
            subject_symbol_id=atom.subject_symbol_id,
            object_symbol_id=atom.object_symbol_id,
            canonical_subject_symbol_id=canonical,
            canonical_object_symbol_id=canonical,
        )
    if atom.relation_id == "instance":
        canonical_member, canonical_class = space.assert_instance(
            atom.subject_symbol_id, atom.object_symbol_id
        )
        return TypedAssertionResult(
            relation_id=atom.relation_id,
            subject_symbol_id=atom.subject_symbol_id,
            object_symbol_id=atom.object_symbol_id,
            canonical_subject_symbol_id=canonical_member,
            canonical_object_symbol_id=canonical_class,
        )
    raise ValueError("typed assertion lowering only supports `instance` and `equivalent`")
