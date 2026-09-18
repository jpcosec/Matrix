"""System-level orchestration for the operational model."""

from .candidates import (
    Candidate,
    promote_candidate,
    register_candidate,
    reject_candidate,
)
from .deduction import deduce
from .logical_system import LogicalSystem
from .operation_results import OperationResult
from .s_expression_runtime import SExpressionRuntime
from .wigame import WiGame
from .wi_game_queries import (
    get_status,
    information_energy,
    is_pure,
    search,
    tautological_columns,
)
from .wi_game_registry import (
    accepts_proposition,
    add_fact,
    register_proposition,
    set_sense,
)
from .wi_game_serialization import from_dict, from_yaml, to_dict, to_yaml

__all__ = [
    "Candidate",
    "LogicalSystem",
    "OperationResult",
    "SExpressionRuntime",
    "WiGame",
    "accepts_proposition",
    "add_fact",
    "deduce",
    "from_dict",
    "from_yaml",
    "is_pure",
    "promote_candidate",
    "register_candidate",
    "register_proposition",
    "reject_candidate",
    "search",
    "set_sense",
    "tautological_columns",
    "to_dict",
    "to_yaml",
]
