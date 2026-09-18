"""Query helpers for LogicalSystem traversal."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..routing.search_vector import SearchVector
from .operation_results import SearchResult

if TYPE_CHECKING:
    from .logical_system import LogicalSystem


def search(system: "LogicalSystem", wigame_id: str, terms: list[str]) -> list[str]:
    """Runs a local search inside one WiGame."""
    wigame = system.wigames[wigame_id]
    return wigame.search(SearchVector(wigame_id=wigame_id, terms=terms))


def project_subjects(
    system: "LogicalSystem",
    projection_id: str,
    source_subjects: list[str],
) -> list[str]:
    """Projects source subjects through one routing matrix."""
    projection = system.projections[projection_id]
    return projection.project_subjects(source_subjects)


def cross_search(
    system: "LogicalSystem",
    source_wigame_id: str,
    source_terms: list[str],
    projection_id: str,
    target_terms: list[str] | None = None,
) -> SearchResult:
    """Runs a search in one WiGame and optionally intersects it in another."""
    hits = search(system, source_wigame_id, source_terms)
    projection = system.projections[projection_id]
    projected = projection.project_subjects(hits)
    if target_terms is None:
        return SearchResult(hits, projected)
    target_id = projection.target_wigame_id
    res = _target_search_payload(system, target_id, projected, target_terms)
    return SearchResult(hits, projected, res["target_hits"], res["cross_hits"])


def route_search(
    system: "LogicalSystem",
    source_wigame_id: str,
    source_terms: list[str],
    path: list[str],
    target_terms: list[str] | None = None,
) -> SearchResult:
    """Runs a multi-hop search across a path of projections."""
    hits = search(system, source_wigame_id, source_terms)
    projected = _follow_path(system, hits, path)
    if target_terms is not None and path:
        target_id = system.projections[path[-1]].target_wigame_id
        res = _target_search_payload(system, target_id, projected, target_terms)
        return SearchResult(hits, projected, res["target_hits"], res["cross_hits"])
    return SearchResult(hits, projected)


def _target_search_payload(
    system: "LogicalSystem",
    target_wigame_id: str,
    projected_hits: list[str],
    target_terms: list[str],
) -> dict[str, list[str]]:
    """Builds the target-side results for a cross search."""
    target_wigame = system.wigames[target_wigame_id]
    target_hits = target_wigame.search(
        SearchVector(wigame_id=target_wigame.wigame_id, terms=target_terms)
    )
    return {
        "target_hits": target_hits,
        "cross_hits": [s for s in projected_hits if s in target_hits],
    }


def _follow_path(system: "LogicalSystem", subjects: list[str], path: list[str]) -> list[str]:
    """Projects subjects through a sequence of routing matrices."""
    res = subjects
    for p_id in path:
        res = system.project_subjects(p_id, res)
    return res
