"""Reachability / acyclicity / state-minimization analysis with a BFS oracle.

The engine path is `BooleanMatrix.transitive_closure` (used by `compile` to
derive closure facts); the oracle is a plain BFS. Agreement between both is the
verification: if they diverge, the closure facts are wrong.
"""

from __future__ import annotations

from collections import deque
from typing import Any

from src.operational_model import BooleanMatrix

from .store import KB, load_yaml, now, read_jsonl, write_json


def edges_of(kb: KB, context: str, relation: str, *, include_derived: bool = False) -> list[tuple[str, str]]:
    rows = read_jsonl(kb.facts_dir / f"wigame__{context}__{relation}.jsonl")
    return [
        (row["subject"], row["object"])
        for row in rows
        if row["truth"] == "true" and (include_derived or not row.get("derived"))
    ]


def _bfs(edges: list[tuple[str, str]], start: str, nodes: list[str]) -> set[str]:
    adjacency: dict[str, set[str]] = {node: set() for node in nodes}
    for subject, obj in edges:
        adjacency.setdefault(subject, set()).add(obj)
    seen: set[str] = set()
    queue = deque(adjacency.get(start, set()))
    while queue:
        node = queue.popleft()
        if node in seen:
            continue
        seen.add(node)
        queue.extend(adjacency.get(node, set()) - seen)
    return seen


def analyze(kb: KB, context: str, relation: str = "precede") -> dict[str, Any]:
    """Analyzes one machine/recipe context."""

    raw_edges = edges_of(kb, context, relation)
    all_edges = edges_of(kb, context, relation, include_derived=True)
    nodes = sorted({node for edge in all_edges for node in edge})
    derived = sorted(set(all_edges) - set(raw_edges))

    strict = _strict_reachability(raw_edges, nodes) if nodes else None
    mismatches: list[dict[str, str]] = []
    for source in nodes:
        oracle = _bfs(raw_edges, source, nodes)
        engine = {target for target in nodes if strict is not None and strict.get(source, target)}
        if oracle != engine:
            mismatches.append(
                {"source": source, "oracle_only": sorted(oracle - engine), "engine_only": sorted(engine - oracle)}
            )

    cyclic = sorted(source for source in nodes if strict is not None and strict.get(source, source))
    initial = _declared_initial(kb, context)
    initial_candidates = [initial] if initial else []
    if not initial_candidates:
        incoming = {node: 0 for node in nodes}
        for _subject, obj in raw_edges:
            incoming[obj] = incoming.get(obj, 0) + 1
        initial_candidates = sorted(node for node in nodes if incoming.get(node, 0) == 0)
    reachable = (_bfs(raw_edges, initial_candidates[0], nodes) | {initial_candidates[0]}) if initial_candidates else set()
    unreachable = sorted(set(nodes) - reachable) if initial_candidates else []

    signatures = _raw_row_masks(raw_edges, nodes)
    classes: dict[str, list[str]] = {}
    for node, mask in zip(nodes, signatures):
        classes.setdefault(str(mask), []).append(node)
    equivalent = [group for group in classes.values() if len(group) > 1]

    return {
        "context": context,
        "relation": relation,
        "nodes": nodes,
        "edges": len(raw_edges),
        "derived_edges": derived,
        "cyclic_nodes": cyclic,
        "acyclic": not cyclic,
        "initial": initial_candidates[0] if initial_candidates else None,
        "initial_source": "declared" if initial else ("in_degree_zero" if initial_candidates else None),
        "unreachable": unreachable,
        "state_classes": sorted(classes.values(), key=lambda group: group[0]),
        "equivalent_states": equivalent,
        "bfs_oracle_agreement": not mismatches,
        "oracle_mismatches": mismatches,
    }


def _strict_reachability(edges: list[tuple[str, str]], nodes: list[str]) -> BooleanMatrix:
    """A+ = A · A* ; strict reachability (length >= 1 paths)."""

    adjacency = BooleanMatrix.filled(nodes, nodes, False)
    for subject, obj in edges:
        adjacency.set(subject, obj, True)
    star = adjacency.transitive_closure()
    return adjacency.bool_mult(star)


def _raw_row_masks(edges: list[tuple[str, str]], nodes: list[str]) -> list[int]:
    """Out-neighbour signature per node using raw transitions only.

    Derived closure cells must not enter the signature: in a linear chain every
    state reaches the same suffix, which would collapse all states.
    """

    adjacency = BooleanMatrix.filled(nodes, nodes, False)
    for subject, obj in edges:
        adjacency.set(subject, obj, True)
    return adjacency.to_row_bitmasks()


def _declared_initial(kb: KB, context: str) -> str | None:
    path = kb.root / "machines_source.yaml"
    if not path.exists():
        return None
    for machine in load_yaml(path).get("machines", []):
        if machine.get("context") == context:
            return machine.get("initial")
    return None


def analyze_all(kb: KB, relation: str = "precede") -> dict[str, Any]:
    """Runs the analysis on every context that has the given relation."""

    contexts: list[str] = []
    prefix = "wigame__"
    suffix = f"__{relation}.yaml"
    for path in sorted(kb.wigames_dir.glob(f"*{suffix}")):
        contexts.append(path.name[len(prefix) : -len(suffix)])

    results = [analyze(kb, context, relation) for context in contexts]
    payload = {
        "analyzed_at": now(),
        "relation": relation,
        "contexts": len(results),
        "all_agreements": all(item["bfs_oracle_agreement"] for item in results),
        "results": results,
    }
    write_json(kb.root / "reachability_report.json", payload)
    return payload
