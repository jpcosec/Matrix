from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import yaml

from ._ids import new_id
from .fact import Fact
from .li_space import LiSpace
from .proposition import Proposition
from .search_vector import SearchVector
from .sense_value import SenseValue
from .si_matrix import SiMatrix
from .truth_value import TruthValue
from .vi_matrix import ViMatrix


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
        self,
        subject_symbol_id: str,
        object_symbol_id: str,
        sense: SenseValue,
    ) -> None:
        self.Si.set(subject_symbol_id, object_symbol_id, sense.value)

    def search(self, search_vector: SearchVector) -> list[str]:
        if search_vector.wigame_id != self.wigame_id:
            raise ValueError("search vector belongs to a different WiGame")
        requested_terms = search_vector.active_terms(self.axis_b)
        candidates = self.Vi.subjects_matching(search_vector)
        matches: list[str] = []
        for subject_symbol_id in candidates:
            row_is_valid = all(
                self.Si.get(subject_symbol_id, term) != SenseValue.UNSINNIG.value
                for term in requested_terms
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
            li_id=payload.get("Li", {}).get("li_id", new_id("li")),
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
