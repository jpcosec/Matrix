"""Result structures for system operations."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SearchResult:
    """Stable return shape for cross-space search operations."""

    source_hits: list[str]
    projected_hits: list[str]
    target_hits: list[str] = field(default_factory=list)
    cross_hits: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class StatusResult:
    """Stable return shape for proposition status queries."""

    status: str
    truth: str | None
    applicable: bool
    reason: str | None = None
    discriminative: bool = True
