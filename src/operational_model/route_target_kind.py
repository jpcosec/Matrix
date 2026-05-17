from __future__ import annotations

from enum import Enum


class RouteTargetKind(str, Enum):
    CONTEXT = "context"
    WIGAME = "wigame"
