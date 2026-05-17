"""Registration helpers for LogicalSystem catalog updates."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..core.fact import Fact
from ..core.li_space import LiSpace
from ..core.name import Name
from ..core.relation import Relation
from ..core.sense_value import SenseValue
from ..core.symbol import Symbol
from ..core.thing import Thing
from ..routing.context import Context
from ..routing.routing_projection import RoutingProjection

if TYPE_CHECKING:
    from .logical_system import LogicalSystem
    from .wigame import WiGame


def register_name(system: "LogicalSystem", name: Name) -> None:
    """Registers a name in the system catalog."""

    system.names[name.sign] = name


def register_symbol(system: "LogicalSystem", symbol: Symbol) -> None:
    """Registers a symbol in the system catalog."""

    system.symbols[symbol.symbol_id] = symbol


def register_thing(system: "LogicalSystem", thing: Thing) -> None:
    """Registers a thing and its symbol/name dependencies."""

    register_name(system, thing.name)
    register_symbol(system, thing.symbol)
    system.things[thing.symbol_id] = thing


def register_relation(system: "LogicalSystem", relation: Relation) -> None:
    """Registers a relation definition."""

    system.relations[relation.relation_id] = relation


def register_li(system: "LogicalSystem", li_space: LiSpace) -> None:
    """Registers an Li space."""

    system.li_spaces[li_space.li_id] = li_space


def register_wigame(system: "LogicalSystem", wigame: "WiGame") -> None:
    """Registers a WiGame and its Li space."""

    system.wigames[wigame.wigame_id] = wigame
    register_li(system, wigame.li)


def register_context(system: "LogicalSystem", context: Context) -> None:
    """Registers a higher-order routing context."""

    system.contexts[context.context_id] = context


def register_projection(system: "LogicalSystem", projection: RoutingProjection) -> None:
    """Registers a WiGame-to-WiGame projection."""

    system.projections[projection.matrix_id] = projection


def add_fact(
    system: "LogicalSystem",
    fact: Fact,
    sense: SenseValue = SenseValue.SINNVOLL,
) -> None:
    """Adds a fact and propagates symbol support updates."""

    wigame = system.wigames[fact.proposition.wigame_id]
    wigame.add_fact(fact, sense=sense)
    _support_symbol(system, fact.proposition.subject_symbol_id, fact, wigame)
    _support_symbol(system, fact.proposition.object_symbol_id, fact, wigame)


def _support_symbol(
    system: "LogicalSystem",
    symbol_id: str,
    fact: Fact,
    wigame: "WiGame",
) -> None:
    """Updates support metadata for one symbol if present."""

    symbol = system.symbols.get(symbol_id)
    if symbol:
        symbol.support(fact.fact_id, wigame.wigame_id)
