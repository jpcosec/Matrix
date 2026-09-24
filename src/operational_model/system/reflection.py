"""Reifying relations as symbols, so a world can talk about its own relations.

`LogicalSystem.relations` and `LogicalSystem.things` are disjoint registries. A
relation id lives in one, symbols live in the other, and nothing links them. So
this pair of facts cannot be connected:

    (persigue pedrito maria)     `persigue` is a relation id
    (es perseguir verbo)         `perseguir` is a symbol

There is no way to ask "what kind of thing is the relation I just used". The same
gap blocks predicating over a context, because `WiGame.context_id` is a plain
`str | None` rather than a symbol.

This module closes it by **reification**: a relation gets a mirror symbol in the
`rel:` namespace, and a context gets one in the `ctx:` namespace. The mirror is a
real registered `Thing`, so it can sit on an axis and be the subject of a
meta-level proposition, while the relation keeps working as a relation. The two
registries stay separate; what is new is a declared, reversible correspondence.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..core.name import Name
from ..core.relation import Relation
from ..core.symbol import Symbol
from ..core.thing import Thing

if TYPE_CHECKING:
    from .logical_system import LogicalSystem

RELATION_NAMESPACE = "rel:"
CONTEXT_NAMESPACE = "ctx:"


def relation_symbol_id(relation_id: str) -> str:
    """Returns the mirror symbol id for a relation."""

    if relation_id.startswith(RELATION_NAMESPACE):
        return relation_id
    return f"{RELATION_NAMESPACE}{relation_id}"


def context_symbol_id(context_id: str) -> str:
    """Returns the mirror symbol id for a context."""

    if context_id.startswith(CONTEXT_NAMESPACE):
        return context_id
    return f"{CONTEXT_NAMESPACE}{context_id}"


def is_relation_symbol(symbol_id: str) -> bool:
    """Reports whether a symbol mirrors a relation."""

    return symbol_id.startswith(RELATION_NAMESPACE) and len(symbol_id) > len(
        RELATION_NAMESPACE
    )


def is_context_symbol(symbol_id: str) -> bool:
    """Reports whether a symbol mirrors a context."""

    return symbol_id.startswith(CONTEXT_NAMESPACE) and len(symbol_id) > len(
        CONTEXT_NAMESPACE
    )


def dereference(symbol_id: str) -> str:
    """Returns the relation or context id behind a mirror symbol."""

    if is_relation_symbol(symbol_id):
        return symbol_id[len(RELATION_NAMESPACE) :]
    if is_context_symbol(symbol_id):
        return symbol_id[len(CONTEXT_NAMESPACE) :]
    raise ValueError(f"symbol {symbol_id!r} does not mirror a relation or a context")


@dataclass(frozen=True)
class Reification:
    """The link between a relation or context and its mirror symbol."""

    kind: str  # "relation" | "context"
    source_id: str
    symbol_id: str


def reify_relation(system: "LogicalSystem", relation_id: str) -> Reification:
    """Registers the mirror symbol for an existing relation."""

    if relation_id not in system.relations:
        raise KeyError(f"relation {relation_id!r} is not registered")
    symbol_id = relation_symbol_id(relation_id)
    if symbol_id not in system.things:
        relation = system.relations[relation_id]
        system.register_thing(Thing(Symbol(symbol_id), Name(relation.name or relation_id)))
    return Reification("relation", relation_id, symbol_id)


def reify_context(system: "LogicalSystem", context_id: str) -> Reification:
    """Registers the mirror symbol for a context id."""

    symbol_id = context_symbol_id(context_id)
    if symbol_id not in system.things:
        system.register_thing(Thing(Symbol(symbol_id), Name(context_id)))
    return Reification("context", context_id, symbol_id)


def reify_all_relations(system: "LogicalSystem") -> list[Reification]:
    """Mirrors every registered relation, in sorted order."""

    return [reify_relation(system, r) for r in sorted(system.relations)]


def reify_all_contexts(system: "LogicalSystem") -> list[Reification]:
    """Mirrors every context id known to the system and its worlds."""

    context_ids = set(system.contexts)
    for wigame in system.wigames.values():
        if wigame.context_id:
            context_ids.add(wigame.context_id)
    return [reify_context(system, c) for c in sorted(context_ids)]


def relation_of_symbol(system: "LogicalSystem", symbol_id: str) -> Relation | None:
    """Returns the relation a mirror symbol stands for, if any."""

    if not is_relation_symbol(symbol_id):
        return None
    return system.relations.get(dereference(symbol_id))


def describes(system: "LogicalSystem", symbol_id: str) -> str | None:
    """Returns what a mirror symbol denotes: a relation id, a context id, or None."""

    if is_relation_symbol(symbol_id) and dereference(symbol_id) in system.relations:
        return dereference(symbol_id)
    if is_context_symbol(symbol_id):
        candidate = dereference(symbol_id)
        if candidate in system.contexts or any(
            w.context_id == candidate for w in system.wigames.values()
        ):
            return candidate
    return None
