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
from .language import parse_s_expression
from .matrices import BooleanMatrix, SiMatrix, ViMatrix
from .routing import Context, ContextRoute, RoutingProjection, SearchVector
from .system import LogicalSystem, OperationResult, SExpressionRuntime, WiGame

__all__ = [
    "BooleanMatrix",
    "Context",
    "ContextRoute",
    "Fact",
    "LiSpace",
    "LogicalSystem",
    "Name",
    "OperationResult",
    "Proposition",
    "Relation",
    "RouteTargetKind",
    "RoutingProjection",
    "SExpressionRuntime",
    "SearchVector",
    "SenseValue",
    "SiMatrix",
    "Symbol",
    "Thing",
    "TruthValue",
    "ViMatrix",
    "WiGame",
    "parse_s_expression",
]
