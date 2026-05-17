"""System-level orchestration for WiGames, contexts, and projections."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..core.fact import Fact
from ..core.li_space import LiSpace
from ..core.name import Name
from ..core.relation import Relation
from ..core.sense_value import SenseValue
from ..core.symbol import Symbol
from ..core.thing import Thing
from ..routing.context import Context
from ..routing.routing_projection import RoutingProjection
from . import logical_system_queries, logical_system_registry
from .wigame import WiGame


@dataclass
class LogicalSystem:
    """Registers and coordinates the operational model graph."""

    names: dict[str, Name] = field(default_factory=dict)
    symbols: dict[str, Symbol] = field(default_factory=dict)
    things: dict[str, Thing] = field(default_factory=dict)
    relations: dict[str, Relation] = field(default_factory=dict)
    li_spaces: dict[str, LiSpace] = field(default_factory=dict)
    wigames: dict[str, WiGame] = field(default_factory=dict)
    contexts: dict[str, Context] = field(default_factory=dict)
    projections: dict[str, RoutingProjection] = field(default_factory=dict)

    def register_name(self, name: Name) -> None:
        """Registers a name in the system catalog."""

        logical_system_registry.register_name(self, name)

    def register_symbol(self, symbol: Symbol) -> None:
        """Registers a symbol in the system catalog."""

        logical_system_registry.register_symbol(self, symbol)

    def register_thing(self, thing: Thing) -> None:
        """Registers a thing and its symbol/name dependencies."""

        logical_system_registry.register_thing(self, thing)

    def register_relation(self, relation: Relation) -> None:
        """Registers a relation definition."""

        logical_system_registry.register_relation(self, relation)

    def register_li(self, li_space: LiSpace) -> None:
        """Registers an Li space."""

        logical_system_registry.register_li(self, li_space)

    def register_wigame(self, wigame: WiGame) -> None:
        """Registers a WiGame and its Li space."""

        logical_system_registry.register_wigame(self, wigame)

    def register_context(self, context: Context) -> None:
        """Registers a higher-order routing context."""

        logical_system_registry.register_context(self, context)

    def register_projection(self, projection: RoutingProjection) -> None:
        """Registers a WiGame-to-WiGame projection."""

        logical_system_registry.register_projection(self, projection)

    def add_fact(self, fact: Fact, sense: SenseValue = SenseValue.SINNVOLL) -> None:
        """Adds a fact and propagates symbol support updates."""

        logical_system_registry.add_fact(self, fact, sense=sense)

    def search(self, wigame_id: str, terms: list[str]) -> list[str]:
        """Runs a local search inside one WiGame."""

        return logical_system_queries.search(self, wigame_id, terms)

    def project_subjects(
        self,
        projection_id: str,
        source_subjects: list[str],
    ) -> list[str]:
        """Projects source subjects through one routing matrix."""

        return logical_system_queries.project_subjects(
            self, projection_id, source_subjects
        )

    def cross_search(
        self,
        source_wigame_id: str,
        source_terms: list[str],
        projection_id: str,
        target_terms: list[str] | None = None,
    ) -> dict[str, list[str]]:
        """Runs a search in one WiGame and optionally intersects it in another."""

        return logical_system_queries.cross_search(
            self,
            source_wigame_id,
            source_terms,
            projection_id,
            target_terms,
        )

    def route_search(
        self,
        source_wigame_id: str,
        source_terms: list[str],
        path: list[str],
        target_terms: list[str] | None = None,
    ) -> dict[str, list[str]]:
        """Runs a multi-hop search across a path of projections."""

        return logical_system_queries.route_search(
            self, source_wigame_id, source_terms, path, target_terms
        )
