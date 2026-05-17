"""Projection matrix implementation for crossings between WiGames."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .._ids import new_id
from ..matrices.boolean_matrix import BooleanMatrix


@dataclass
class RoutingProjection(BooleanMatrix):
    """Projects source subjects into a target WiGame subject axis."""

    source_wigame_id: str = ""
    target_wigame_id: str = ""
    relation_id: str = "projects_to"

    @classmethod
    def empty(
        cls,
        source_wigame_id: str,
        source_axis: list[str],
        target_wigame_id: str,
        target_axis: list[str],
        relation_id: str = "projects_to",
    ) -> "RoutingProjection":
        """Builds an empty projection between two WiGame subject axes."""

        return cls(
            row_axis=list(source_axis),
            column_axis=list(target_axis),
            values=[[False for _ in target_axis] for _ in source_axis],
            matrix_id=new_id("ri"),
            metadata={"kind": "routing_projection"},
            source_wigame_id=source_wigame_id,
            target_wigame_id=target_wigame_id,
            relation_id=relation_id,
        )

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RoutingProjection":
        """Hydrates a projection matrix from serialized data."""

        return cls(
            row_axis=payload["rows"],
            column_axis=payload["columns"],
            values=payload["values"],
            matrix_id=payload.get("matrix_id", new_id("ri")),
            metadata=payload.get("metadata", {}),
            source_wigame_id=payload["source_wigame_id"],
            target_wigame_id=payload["target_wigame_id"],
            relation_id=payload.get("relation_id", "projects_to"),
        )

    def link(self, source_symbol_id: str, target_symbol_id: str) -> None:
        """Marks a source-to-target projection relation."""

        self.set(source_symbol_id, target_symbol_id, True)

    def project_subjects(self, source_subjects: list[str]) -> list[str]:
        """Projects source subjects into the target WiGame axis."""

        projected: list[str] = []
        for source_subject in source_subjects:
            self._append_projected_targets(projected, source_subject)
        return projected

    def back_project_subjects(self, target_subjects: list[str]) -> list[str]:
        """Back-projects target subjects into the source WiGame axis."""

        back_projected: list[str] = []
        for target_subject in target_subjects:
            self._append_back_projected_sources(back_projected, target_subject)
        return back_projected

    def to_dict(self) -> dict[str, Any]:
        """Serializes the projection with source and target metadata."""

        payload = super().to_dict()
        payload.update(
            {
                "source_wigame_id": self.source_wigame_id,
                "target_wigame_id": self.target_wigame_id,
                "relation_id": self.relation_id,
            }
        )
        return payload

    def _append_projected_targets(
        self, projected: list[str], source_subject: str
    ) -> None:
        """Appends projected targets for a single source subject."""

        for target_symbol_id, is_linked in self.row(source_subject).items():
            if is_linked and target_symbol_id not in projected:
                projected.append(target_symbol_id)

    def _append_back_projected_sources(
        self,
        back_projected: list[str],
        target_subject: str,
    ) -> None:
        """Appends back-projected sources for a single target subject."""

        for source_symbol_id, is_linked in self.column(target_subject).items():
            if is_linked and source_symbol_id not in back_projected:
                back_projected.append(source_symbol_id)
