"""Core proposition-first domain entities."""

from .fact import Fact
from .li_space import LiSpace
from .name import Name
from .proposition import Proposition
from .relation import Relation
from .route_target_kind import RouteTargetKind
from .sense_value import SenseValue
from .symbol import Symbol
from .thing import Thing
from .truth_value import TruthValue

__all__ = [
    "Fact",
    "LiSpace",
    "Name",
    "Proposition",
    "Relation",
    "RouteTargetKind",
    "SenseValue",
    "Symbol",
    "Thing",
    "TruthValue",
]
