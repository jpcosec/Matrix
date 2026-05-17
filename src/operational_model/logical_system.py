from __future__ import annotations

from dataclasses import dataclass, field

from .context import Context
from .fact import Fact
from .li_space import LiSpace
from .name import Name
from .relation import Relation
from .routing_projection import RoutingProjection
from .search_vector import SearchVector
from .sense_value import SenseValue
from .symbol import Symbol
from .thing import Thing
from .wigame import WiGame


@dataclass
class LogicalSystem:
    names: dict[str, Name] = field(default_factory=dict)
    symbols: dict[str, Symbol] = field(default_factory=dict)
    things: dict[str, Thing] = field(default_factory=dict)
    relations: dict[str, Relation] = field(default_factory=dict)
    li_spaces: dict[str, LiSpace] = field(default_factory=dict)
    wigames: dict[str, WiGame] = field(default_factory=dict)
    contexts: dict[str, Context] = field(default_factory=dict)
    projections: dict[str, RoutingProjection] = field(default_factory=dict)

    def register_name(self, name: Name) -> None:
        self.names[name.sign] = name

    def register_symbol(self, symbol: Symbol) -> None:
        self.symbols[symbol.symbol_id] = symbol

    def register_thing(self, thing: Thing) -> None:
        self.register_name(thing.name)
        self.register_symbol(thing.symbol)
        self.things[thing.symbol_id] = thing

    def register_relation(self, relation: Relation) -> None:
        self.relations[relation.relation_id] = relation

    def register_li(self, li_space: LiSpace) -> None:
        self.li_spaces[li_space.li_id] = li_space

    def register_wigame(self, wigame: WiGame) -> None:
        self.wigames[wigame.wigame_id] = wigame
        self.register_li(wigame.li)

    def register_context(self, context: Context) -> None:
        self.contexts[context.context_id] = context

    def register_projection(self, projection: RoutingProjection) -> None:
        self.projections[projection.matrix_id] = projection

    def add_fact(self, fact: Fact, sense: SenseValue = SenseValue.SINNVOLL) -> None:
        wigame = self.wigames[fact.proposition.wigame_id]
        wigame.add_fact(fact, sense=sense)

        subject = self.symbols.get(fact.proposition.subject_symbol_id)
        if subject:
            subject.support(fact.fact_id, wigame.wigame_id)

        obj = self.symbols.get(fact.proposition.object_symbol_id)
        if obj:
            obj.support(fact.fact_id, wigame.wigame_id)

    def search(self, wigame_id: str, terms: list[str]) -> list[str]:
        wigame = self.wigames[wigame_id]
        return wigame.search(SearchVector(wigame_id=wigame_id, terms=terms))

    def project_subjects(
        self,
        projection_id: str,
        source_subjects: list[str],
    ) -> list[str]:
        projection = self.projections[projection_id]
        return projection.project_subjects(source_subjects)

    def cross_search(
        self,
        source_wigame_id: str,
        source_terms: list[str],
        projection_id: str,
        target_terms: list[str] | None = None,
    ) -> dict[str, list[str]]:
        source_hits = self.search(source_wigame_id, source_terms)
        projection = self.projections[projection_id]
        projected_hits = projection.project_subjects(source_hits)
        result = {
            "source_hits": source_hits,
            "projected_hits": projected_hits,
        }
        if target_terms is not None:
            target_wigame = self.wigames[projection.target_wigame_id]
            target_hits = target_wigame.search(
                SearchVector(wigame_id=target_wigame.wigame_id, terms=target_terms)
            )
            result["target_hits"] = target_hits
            result["cross_hits"] = [
                symbol_id for symbol_id in projected_hits if symbol_id in target_hits
            ]
        return result
