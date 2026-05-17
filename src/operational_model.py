from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
import uuid

import yaml


def _new_id(prefix: str) -> str:
    return f"{prefix}:{uuid.uuid4().hex[:12]}"


class TruthValue(str, Enum):
    TRUE = "true"
    FALSE = "false"
    UNKNOWN = "unknown"


class SenseValue(str, Enum):
    SINNVOLL = "sinnvoll"
    SINNLOS = "sinnlos"
    UNSINNIG = "unsinnig"


class RouteTargetKind(str, Enum):
    CONTEXT = "context"
    WIGAME = "wigame"


@dataclass(frozen=True)
class Name:
    sign: str
    namespace: str = "default"


@dataclass
class Symbol:
    symbol_id: str
    signs: set[str] = field(default_factory=set)
    supporting_fact_ids: set[str] = field(default_factory=set)
    supporting_wigame_ids: set[str] = field(default_factory=set)
    metadata: dict[str, Any] = field(default_factory=dict)

    def bind_name(self, name: Name) -> None:
        self.signs.add(name.sign)

    def support(self, fact_id: str, wigame_id: str | None = None) -> None:
        self.supporting_fact_ids.add(fact_id)
        if wigame_id:
            self.supporting_wigame_ids.add(wigame_id)


@dataclass
class Thing:
    symbol: Symbol
    name: Name
    aliases: set[str] = field(default_factory=set)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.symbol.bind_name(self.name)
        for alias in self.aliases:
            self.symbol.signs.add(alias)

    @property
    def symbol_id(self) -> str:
        return self.symbol.symbol_id


@dataclass
class Relation:
    relation_id: str
    name: str
    transitive: bool = False
    associative: bool = False
    distributive: bool = False
    commutative: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Proposition:
    relation_id: str
    subject_symbol_id: str
    object_symbol_id: str
    wigame_id: str
    proposition_id: str = field(default_factory=lambda: _new_id("prop"))

    def sexpr(self) -> str:
        return f"({self.relation_id} {self.subject_symbol_id} {self.object_symbol_id})"


@dataclass
class Fact:
    proposition: Proposition
    truth: TruthValue
    fact_id: str = field(default_factory=lambda: _new_id("fact"))
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass
class LiSpace:
    li_id: str
    axis_a: list[str]
    axis_b: list[str]
    relation_id: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def accepts(self, proposition: Proposition) -> bool:
        return (
            proposition.relation_id == self.relation_id
            and proposition.subject_symbol_id in self.axis_a
            and proposition.object_symbol_id in self.axis_b
        )


@dataclass
class BooleanMatrix:
    row_axis: list[str]
    column_axis: list[str]
    values: list[list[Any]]
    matrix_id: str = field(default_factory=lambda: _new_id("matrix"))
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if len(self.values) != len(self.row_axis):
            raise ValueError("row axis length and values height must match")
        for row in self.values:
            if len(row) != len(self.column_axis):
                raise ValueError("column axis length and row width must match")

    @classmethod
    def filled(
        cls,
        row_axis: list[str],
        column_axis: list[str],
        fill: Any,
        matrix_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "BooleanMatrix":
        return cls(
            row_axis=list(row_axis),
            column_axis=list(column_axis),
            values=[[fill for _ in column_axis] for _ in row_axis],
            matrix_id=matrix_id or _new_id("matrix"),
            metadata=metadata or {},
        )

    def row_index(self, row_key: str) -> int:
        return self.row_axis.index(row_key)

    def column_index(self, column_key: str) -> int:
        return self.column_axis.index(column_key)

    def get(self, row_key: str, column_key: str) -> Any:
        return self.values[self.row_index(row_key)][self.column_index(column_key)]

    def set(self, row_key: str, column_key: str, value: Any) -> None:
        self.values[self.row_index(row_key)][self.column_index(column_key)] = value

    def row(self, row_key: str) -> dict[str, Any]:
        row_idx = self.row_index(row_key)
        return {
            column_key: self.values[row_idx][column_idx]
            for column_idx, column_key in enumerate(self.column_axis)
        }

    def column(self, column_key: str) -> dict[str, Any]:
        column_idx = self.column_index(column_key)
        return {
            row_key: self.values[row_idx][column_idx]
            for row_idx, row_key in enumerate(self.row_axis)
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "matrix_id": self.matrix_id,
            "rows": list(self.row_axis),
            "columns": list(self.column_axis),
            "values": [list(row) for row in self.values],
            "metadata": dict(self.metadata),
        }


@dataclass
class ViMatrix(BooleanMatrix):
    @classmethod
    def empty(cls, row_axis: list[str], column_axis: list[str]) -> "ViMatrix":
        return cls.filled(
            row_axis=row_axis,
            column_axis=column_axis,
            fill=TruthValue.UNKNOWN.value,
            matrix_id=_new_id("vi"),
        )

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ViMatrix":
        return cls(
            row_axis=payload["rows"],
            column_axis=payload["columns"],
            values=payload["values"],
            matrix_id=payload.get("matrix_id", _new_id("vi")),
            metadata=payload.get("metadata", {}),
        )

    def subjects_matching(self, search_vector: "SearchVector") -> list[str]:
        requested = search_vector.active_terms(self.column_axis)
        matches: list[str] = []
        for row_key in self.row_axis:
            row = self.row(row_key)
            if all(row[column] == TruthValue.TRUE.value for column in requested):
                matches.append(row_key)
        return matches

    def tautological_columns(self) -> list[str]:
        tautologies: list[str] = []
        for column_key in self.column_axis:
            values = list(self.column(column_key).values())
            if values and all(value == TruthValue.TRUE.value for value in values):
                tautologies.append(column_key)
        return tautologies


@dataclass
class SiMatrix(BooleanMatrix):
    @classmethod
    def pure(cls, row_axis: list[str], column_axis: list[str]) -> "SiMatrix":
        return cls.filled(
            row_axis=row_axis,
            column_axis=column_axis,
            fill=SenseValue.SINNLOS.value,
            matrix_id=_new_id("si"),
        )

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SiMatrix":
        return cls(
            row_axis=payload["rows"],
            column_axis=payload["columns"],
            values=payload["values"],
            matrix_id=payload.get("matrix_id", _new_id("si")),
            metadata=payload.get("metadata", {}),
        )

    def is_pure(self) -> bool:
        for row_key in self.row_axis:
            row = self.row(row_key)
            if any(value == SenseValue.UNSINNIG.value for value in row.values()):
                return False
        return True


@dataclass
class SearchVector:
    wigame_id: str
    terms: list[str]
    vector_id: str = field(default_factory=lambda: _new_id("pi"))
    metadata: dict[str, Any] = field(default_factory=dict)

    def active_terms(self, available_columns: list[str]) -> list[str]:
        unknown = [term for term in self.terms if term not in available_columns]
        if unknown:
            raise KeyError(f"unknown search terms: {unknown}")
        return list(self.terms)

    def as_matrix(self, column_axis: list[str]) -> BooleanMatrix:
        active = set(self.active_terms(column_axis))
        return BooleanMatrix(
            row_axis=[self.vector_id],
            column_axis=list(column_axis),
            values=[[column in active for column in column_axis]],
            matrix_id=self.vector_id,
            metadata={"kind": "search_vector", **self.metadata},
        )


@dataclass
class RoutingProjection(BooleanMatrix):
    source_wigame_id: str = ""
    target_wigame_id: str = ""
    relation_id: str = "projects_to"

    @classmethod
    def empty(
        cls,
        source_wigame_id: str,
        source_axis: list[str],
        target_wigame_id: str,
        target_axis: list[str],
        relation_id: str = "projects_to",
    ) -> "RoutingProjection":
        return cls(
            row_axis=list(source_axis),
            column_axis=list(target_axis),
            values=[[False for _ in target_axis] for _ in source_axis],
            matrix_id=_new_id("ri"),
            metadata={"kind": "routing_projection"},
            source_wigame_id=source_wigame_id,
            target_wigame_id=target_wigame_id,
            relation_id=relation_id,
        )

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RoutingProjection":
        return cls(
            row_axis=payload["rows"],
            column_axis=payload["columns"],
            values=payload["values"],
            matrix_id=payload.get("matrix_id", _new_id("ri")),
            metadata=payload.get("metadata", {}),
            source_wigame_id=payload["source_wigame_id"],
            target_wigame_id=payload["target_wigame_id"],
            relation_id=payload.get("relation_id", "projects_to"),
        )

    def link(self, source_symbol_id: str, target_symbol_id: str) -> None:
        self.set(source_symbol_id, target_symbol_id, True)

    def project_subjects(self, source_subjects: list[str]) -> list[str]:
        projected: list[str] = []
        for source_subject in source_subjects:
            for target_symbol_id, is_linked in self.row(source_subject).items():
                if is_linked and target_symbol_id not in projected:
                    projected.append(target_symbol_id)
        return projected

    def back_project_subjects(self, target_subjects: list[str]) -> list[str]:
        back_projected: list[str] = []
        for target_subject in target_subjects:
            for source_symbol_id, is_linked in self.column(target_subject).items():
                if is_linked and source_symbol_id not in back_projected:
                    back_projected.append(source_symbol_id)
        return back_projected

    def to_dict(self) -> dict[str, Any]:
        payload = super().to_dict()
        payload.update(
            {
                "source_wigame_id": self.source_wigame_id,
                "target_wigame_id": self.target_wigame_id,
                "relation_id": self.relation_id,
            }
        )
        return payload


@dataclass
class WiGame:
    wigame_id: str
    li: LiSpace
    context_id: str | None = None
    propositions: dict[str, Proposition] = field(default_factory=dict)
    facts: dict[str, Fact] = field(default_factory=dict)
    Vi: ViMatrix | None = None
    Si: SiMatrix | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.Vi is None:
            self.Vi = ViMatrix.empty(self.li.axis_a, self.li.axis_b)
        if self.Si is None:
            self.Si = SiMatrix.pure(self.li.axis_a, self.li.axis_b)

    @property
    def axis_a(self) -> list[str]:
        return self.li.axis_a

    @property
    def axis_b(self) -> list[str]:
        return self.li.axis_b

    @property
    def relation_id(self) -> str:
        return self.li.relation_id

    def accepts(self, proposition: Proposition) -> bool:
        return proposition.wigame_id == self.wigame_id and self.li.accepts(proposition)

    def register_proposition(
        self,
        proposition: Proposition,
        sense: SenseValue | None = None,
    ) -> None:
        self.propositions[proposition.proposition_id] = proposition
        if not self.li.accepts(proposition):
            if (
                proposition.subject_symbol_id in self.axis_a
                and proposition.object_symbol_id in self.axis_b
            ):
                self.Si.set(
                    proposition.subject_symbol_id,
                    proposition.object_symbol_id,
                    SenseValue.UNSINNIG.value,
                )
            return
        self.Si.set(
            proposition.subject_symbol_id,
            proposition.object_symbol_id,
            (sense or SenseValue.SINNLOS).value,
        )

    def add_fact(self, fact: Fact, sense: SenseValue = SenseValue.SINNVOLL) -> None:
        proposition = fact.proposition
        if not self.accepts(proposition):
            raise ValueError("fact proposition does not fit this WiGame")
        self.register_proposition(proposition, sense=sense)
        self.facts[fact.fact_id] = fact
        self.Vi.set(
            proposition.subject_symbol_id,
            proposition.object_symbol_id,
            fact.truth.value,
        )

    def set_sense(
        self, subject_symbol_id: str, object_symbol_id: str, sense: SenseValue
    ) -> None:
        self.Si.set(subject_symbol_id, object_symbol_id, sense.value)

    def search(self, search_vector: SearchVector) -> list[str]:
        if search_vector.wigame_id != self.wigame_id:
            raise ValueError("search vector belongs to a different WiGame")
        candidates = self.Vi.subjects_matching(search_vector)
        matches: list[str] = []
        for subject_symbol_id in candidates:
            row_is_valid = all(
                self.Si.get(subject_symbol_id, term) != SenseValue.UNSINNIG.value
                for term in search_vector.active_terms(self.axis_b)
            )
            if row_is_valid:
                matches.append(subject_symbol_id)
        return matches

    def tautological_columns(self) -> list[str]:
        return self.Vi.tautological_columns()

    def is_pure(self) -> bool:
        return self.Si.is_pure()

    def to_dict(self) -> dict[str, Any]:
        return {
            "wigame_id": self.wigame_id,
            "ejeA": list(self.axis_a),
            "ejeB": list(self.axis_b),
            "relacion": self.relation_id,
            "contexto": self.context_id,
            "Li": {
                "li_id": self.li.li_id,
                "metadata": dict(self.li.metadata),
            },
            "Vi": self.Vi.to_dict(),
            "Si": self.Si.to_dict(),
            "facts": [
                {
                    "fact_id": fact_id,
                    "truth": fact.truth.value,
                    "proposition": {
                        "proposition_id": fact.proposition.proposition_id,
                        "relation_id": fact.proposition.relation_id,
                        "subject_symbol_id": fact.proposition.subject_symbol_id,
                        "object_symbol_id": fact.proposition.object_symbol_id,
                        "wigame_id": fact.proposition.wigame_id,
                    },
                    "evidence": dict(fact.evidence),
                }
                for fact_id, fact in self.facts.items()
            ],
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "WiGame":
        li = LiSpace(
            li_id=payload.get("Li", {}).get("li_id", _new_id("li")),
            axis_a=payload["ejeA"],
            axis_b=payload["ejeB"],
            relation_id=payload["relacion"],
            metadata=payload.get("Li", {}).get("metadata", {}),
        )
        wigame = cls(
            wigame_id=payload["wigame_id"],
            li=li,
            context_id=payload.get("contexto"),
            Vi=ViMatrix.from_dict(payload["Vi"]),
            Si=SiMatrix.from_dict(payload["Si"]),
            metadata=payload.get("metadata", {}),
        )

        for fact_payload in payload.get("facts", []):
            proposition_payload = fact_payload["proposition"]
            proposition = Proposition(
                relation_id=proposition_payload["relation_id"],
                subject_symbol_id=proposition_payload["subject_symbol_id"],
                object_symbol_id=proposition_payload["object_symbol_id"],
                wigame_id=proposition_payload["wigame_id"],
                proposition_id=proposition_payload["proposition_id"],
            )
            fact = Fact(
                proposition=proposition,
                truth=TruthValue(fact_payload["truth"]),
                fact_id=fact_payload["fact_id"],
                evidence=fact_payload.get("evidence", {}),
            )
            wigame.propositions[proposition.proposition_id] = proposition
            wigame.facts[fact.fact_id] = fact
        return wigame

    def to_yaml(self) -> str:
        return yaml.safe_dump(self.to_dict(), sort_keys=False)

    @classmethod
    def from_yaml(cls, payload: str) -> "WiGame":
        return cls.from_dict(yaml.safe_load(payload))


@dataclass
class ContextRoute:
    source_context_id: str
    target_kind: RouteTargetKind
    target_id: str
    relation_id: str = "routes_to"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Context:
    context_id: str
    descriptor: Proposition | None = None
    routes: list[ContextRoute] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def route_to_context(
        self,
        target_context_id: str,
        relation_id: str = "routes_to",
    ) -> ContextRoute:
        route = ContextRoute(
            source_context_id=self.context_id,
            target_kind=RouteTargetKind.CONTEXT,
            target_id=target_context_id,
            relation_id=relation_id,
        )
        self.routes.append(route)
        return route

    def route_to_wigame(
        self,
        target_wigame_id: str,
        relation_id: str = "routes_to",
    ) -> ContextRoute:
        route = ContextRoute(
            source_context_id=self.context_id,
            target_kind=RouteTargetKind.WIGAME,
            target_id=target_wigame_id,
            relation_id=relation_id,
        )
        self.routes.append(route)
        return route


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
