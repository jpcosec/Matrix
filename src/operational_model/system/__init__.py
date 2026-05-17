"""System-level orchestration for the operational model."""

from .logical_system import LogicalSystem
from .wigame import WiGame
from .wi_game_queries import is_pure, search, tautological_columns
from .wi_game_registry import (
    accepts_proposition,
    add_fact,
    register_proposition,
    set_sense,
)
from .wi_game_serialization import from_dict, from_yaml, to_dict, to_yaml

__all__ = [
    "LogicalSystem",
    "WiGame",
    "accepts_proposition",
    "add_fact",
    "from_dict",
    "from_yaml",
    "is_pure",
    "register_proposition",
    "search",
    "set_sense",
    "tautological_columns",
    "to_dict",
    "to_yaml",
]
