"""WiGame aggregate for proposition evaluation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..core.fact import Fact
from ..core.li_space import LiSpace
from ..core.proposition import Proposition
from ..core.sense_value import SenseValue
from ..matrices.si_matrix import SiMatrix
from ..matrices.vi_matrix import ViMatrix
from ..routing.search_vector import SearchVector
from . import wi_game_queries, wi_game_registry, wi_game_serialization


@dataclass
class WiGame:
    """Stores propositions, facts, and derived matrices for one language game."""

    wigame_id: str
    li: LiSpace
    context_id: str | None = None
    propositions: dict[str, Proposition] = field(default_factory=dict)
    facts: dict[str, Fact] = field(default_factory=dict)
    Vi: ViMatrix | None = None
    Si: SiMatrix | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initializes the backing truth and sense matrices."""

        self.Vi = self.Vi or wi_game_registry.initialize_vi(self)
        self.Si = self.Si or wi_game_registry.initialize_si(self)

    @property
    def axis_a(self) -> list[str]:
        """Returns the subject axis of the game."""

        return self.li.axis_a

    @property
    def axis_b(self) -> list[str]:
        """Returns the term axis of the game."""

        return self.li.axis_b

    @property
    def relation_id(self) -> str:
        """Returns the single relation admitted by the Li space."""

        return self.li.relation_id

    def accepts(self, proposition: Proposition) -> bool:
        """Checks whether a proposition belongs to this WiGame."""

        return wi_game_registry.accepts_proposition(self, proposition)

    def register_proposition(
        self,
        proposition: Proposition,
        sense: SenseValue | None = None,
    ) -> None:
        """Registers a proposition and updates the sense matrix."""

        wi_game_registry.register_proposition(self, proposition, sense=sense)

    def add_fact(self, fact: Fact, sense: SenseValue = SenseValue.SINNVOLL) -> None:
        """Registers a fact and writes its truth into `Vi`."""

        wi_game_registry.add_fact(self, fact, sense=sense)

    def set_sense(
        self,
        subject_symbol_id: str,
        object_symbol_id: str,
        sense: SenseValue,
    ) -> None:
        """Overrides the sense value for one proposition slot."""

        wi_game_registry.set_sense(self, subject_symbol_id, object_symbol_id, sense)

    def search(self, search_vector: SearchVector) -> list[str]:
        """Searches `Vi` under the constraints imposed by `Si`."""

        return wi_game_queries.search(self, search_vector)

    def tautological_columns(self) -> list[str]:
        """Returns non-discriminating truth columns."""

        return wi_game_queries.tautological_columns(self)

    def is_pure(self) -> bool:
        """Reports whether the sense matrix contains no `unsinnig` values."""

        return wi_game_queries.is_pure(self)

    def to_dict(self) -> dict[str, Any]:
        """Serializes the WiGame into its direct operational shape."""

        return wi_game_serialization.to_dict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "WiGame":
        """Hydrates a WiGame from serialized operational data."""

        return wi_game_serialization.from_dict(payload)

    def to_yaml(self) -> str:
        """Serializes the WiGame to YAML."""

        return wi_game_serialization.to_yaml(self)

    @classmethod
    def from_yaml(cls, payload: str) -> "WiGame":
        """Hydrates a WiGame from YAML."""

        return wi_game_serialization.from_yaml(payload)
