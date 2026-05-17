from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .route_target_kind import RouteTargetKind


@dataclass
class ContextRoute:
    source_context_id: str
    target_kind: RouteTargetKind
    target_id: str
    relation_id: str = "routes_to"
    metadata: dict[str, Any] = field(default_factory=dict)
