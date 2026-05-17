from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .context_route import ContextRoute
from .proposition import Proposition
from .route_target_kind import RouteTargetKind


@dataclass
class Context:
    context_id: str
    descriptor: Proposition | None = None
    routes: list[ContextRoute] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def route_to_context(
        self,
        target_context_id: str,
        relation_id: str = "routes_to",
    ) -> ContextRoute:
        route = ContextRoute(
            source_context_id=self.context_id,
            target_kind=RouteTargetKind.CONTEXT,
            target_id=target_context_id,
            relation_id=relation_id,
        )
        self.routes.append(route)
        return route

    def route_to_wigame(
        self,
        target_wigame_id: str,
        relation_id: str = "routes_to",
    ) -> ContextRoute:
        route = ContextRoute(
            source_context_id=self.context_id,
            target_kind=RouteTargetKind.WIGAME,
            target_id=target_wigame_id,
            relation_id=relation_id,
        )
        self.routes.append(route)
        return route
