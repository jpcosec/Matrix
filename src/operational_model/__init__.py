"""Public API for the proposition-first operational model."""

from .core import (
    Fact,
    LiSpace,
    Name,
    Proposition,
    Relation,
    RouteTargetKind,
    SenseValue,
    Symbol,
    Thing,
    TruthValue,
)
from .matrices import BooleanMatrix, SiMatrix, ViMatrix
from .routing import Context, ContextRoute, RoutingProjection, SearchVector
from .system import LogicalSystem, WiGame

__all__ = [
    "BooleanMatrix",
    "Context",
    "ContextRoute",
    "Fact",
    "LiSpace",
    "LogicalSystem",
    "Name",
    "Proposition",
    "Relation",
    "RouteTargetKind",
    "RoutingProjection",
    "SearchVector",
    "SenseValue",
    "SiMatrix",
    "Symbol",
    "Thing",
    "TruthValue",
    "ViMatrix",
    "WiGame",
]
