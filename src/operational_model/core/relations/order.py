"""Order utilities over plain (nodes, edges) pairs.

Pure functions: no dependency on WiGame, LiSpace or RelationAlgebra.
Deterministic output. A directed edge ``(u, v)`` means ``u`` precedes ``v``.
"""

from __future__ import annotations

from typing import Optional


class CycleError(ValueError):
    """Raised when ``edges`` contains a directed cycle."""


class UnknownNodeError(ValueError):
    """Raised when an edge refers to a node that is not in ``nodes``."""


def _validate_edges(nodes: list[str], edges: list[tuple[str, str]]) -> None:
    known: set[str] = set(nodes)
    for u, v in edges:
        if u not in known:
            raise UnknownNodeError(f"edge refers to unknown node: {u!r}")
        if v not in known:
            raise UnknownNodeError(f"edge refers to unknown node: {v!r}")


def _build_adjacency(
    nodes: list[str], edges: list[tuple[str, str]]
) -> dict[str, list[str]]:
    adjacency: dict[str, list[str]] = {node: [] for node in nodes}
    for u, v in edges:
        adjacency[u].append(v)
    return adjacency


def _find_cycle(
    nodes: list[str], edges: list[tuple[str, str]]
) -> Optional[list[str]]:
    adjacency = _build_adjacency(nodes, edges)
    color: dict[str, int] = {node: 0 for node in nodes}
    stack: list[str] = []

    def visit(u: str) -> Optional[list[str]]:
        color[u] = 1
        stack.append(u)
        for v in adjacency[u]:
            if color[v] == 0:
                cycle = visit(v)
                if cycle is not None:
                    return cycle
            elif color[v] == 1:
                start = stack.index(v)
                return stack[start:] + [v]
        stack.pop()
        color[u] = 2
        return None

    for node in nodes:
        if color[node] == 0:
            cycle = visit(node)
            if cycle is not None:
                return cycle
    return None


def assert_acyclic(nodes: list[str], edges: list[tuple[str, str]]) -> None:
    """Raise ``CycleError`` if ``edges`` contains a directed cycle."""
    _validate_edges(nodes, edges)
    cycle = _find_cycle(nodes, edges)
    if cycle is not None:
        raise CycleError("cycle: " + " -> ".join(cycle))


def topological_sequence(nodes: list[str], edges: list[tuple[str, str]]) -> list[str]:
    """Return a deterministic linear extension of ``edges`` over ``nodes``."""
    assert_acyclic(nodes, edges)
    order: list[str] = []
    adjacency = _build_adjacency(nodes, edges)
    in_degree = {node: 0 for node in nodes}
    for u, v in edges:
        in_degree[v] += 1
    remaining = set(nodes)
    while remaining:
        for node in nodes:
            if node in remaining and in_degree[node] == 0:
                break
        else:  # pragma: no cover - unreachable after assert_acyclic
            raise CycleError("cycle detected while computing linear extension")
        order.append(node)
        remaining.remove(node)
        for successor in adjacency[node]:
            in_degree[successor] -= 1
    return order


def is_total(nodes: list[str], edges: list[tuple[str, str]]) -> bool:
    """True when every pair of distinct nodes is comparable under the order.

    Comparability is judged on the transitive closure of ``edges``: a chain
    ``a -> b -> c`` makes every pair comparable, so it is total.
    """
    _validate_edges(nodes, edges)
    if len(nodes) <= 1:
        return True
    adjacency = _build_adjacency(nodes, edges)
    reaches: set[tuple[str, str]] = set()
    for start in nodes:
        seen: set[str] = set()
        frontier = [successor for successor in adjacency[start] if successor != start]
        while frontier:
            current = frontier.pop()
            if current in seen:
                continue
            seen.add(current)
            reaches.add((start, current))
            frontier.extend(adjacency[current])
    for i, first in enumerate(nodes):
        for second in nodes[i + 1 :]:
            if (first, second) not in reaches and (second, first) not in reaches:
                return False
    return True


def linear_extension(nodes: list[str], edges: list[tuple[str, str]]) -> list[str]:
    """Alias of :func:`topological_sequence`."""
    return topological_sequence(nodes, edges)
