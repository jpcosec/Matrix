"""Routing target categories for contexts."""

from __future__ import annotations

from enum import Enum


class RouteTargetKind(str, Enum):
    """Defines whether a route points to a context or a WiGame."""

    CONTEXT = "context"
    WIGAME = "wigame"
