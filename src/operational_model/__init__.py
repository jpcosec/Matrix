"""Public API for the proposition-first operational model."""

from .core import (
    Fact,
    LiSpace,
    Name,
    Proposition,
    Relation,
    RelationAlgebra,
    RouteTargetKind,
    SenseValue,
    Symbol,
    Thing,
    TruthValue,
)
from .kernel import (
    KERNEL_CONNECTIVES,
    KERNEL_META_RELATIONS,
    WI_RELATION_FAMILIES,
    SymbolPolicy,
    classify_symbol,
    is_kernel_symbol,
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
    "KERNEL_CONNECTIVES",
    "KERNEL_META_RELATIONS",
    "LiSpace",
    "LogicalSystem",
    "Name",
    "OperationResult",
    "Proposition",
    "Relation",
    "RelationAlgebra",
    "RouteTargetKind",
    "RoutingProjection",
    "SExpressionRuntime",
    "SearchVector",
    "SenseValue",
    "SiMatrix",
    "SymbolPolicy",
    "Symbol",
    "Thing",
    "TruthValue",
    "ViMatrix",
    "WI_RELATION_FAMILIES",
    "WiGame",
    "classify_symbol",
    "is_kernel_symbol",
    "parse_s_expression",
]
