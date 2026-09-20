"""Routed questions over the converged language games."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from populator.tokenize import normalize


@dataclass
class Answer:
    """Answer of one routed question: the objects reached plus the route taken."""

    relation: str
    subject: str
    objects: list[tuple[str, str, set[str], list[dict]]] = field(default_factory=list)
    path: list[str] = field(default_factory=list)
    explicit_false: bool = False

    def truth_for(self, object_norm: str | None) -> str:
        """Returns ``true``, ``false`` or ``∅`` for one expected object."""

        if object_norm is None:
            return "true" if self.objects else "\u2205"
        wanted = normalize(object_norm)
        if any(normalize(sign) == wanted for _, _, signs, _ in self.objects for sign in signs):
            return "true"
        return "false" if self.explicit_false else "\u2205"

    def as_dict(self) -> dict[str, Any]:
        """Returns a JSON-serializable summary."""

        return {
            "relation": self.relation,
            "subject": self.subject,
            "path": list(self.path),
            "objects": [
                {"symbol": symbol, "ctx": ctx, "signs": sorted(signs), "prov": prov}
                for symbol, ctx, signs, prov in self.objects
            ],
        }


def referent_of(system: Any, symbol_id: str) -> str | None:
    """Returns the converged referent of a symbol, if it has one."""

    symbol = system.symbols.get(symbol_id)
    if symbol is None:
        return None
    return symbol.metadata.get("referent")


def ask(
    system: Any,
    relation: str,
    subject_symbol: str,
    object_norm: str | None = None,
    hops: int = 2,
) -> Answer:
    """Follows promoted projections up to ``hops`` and collects (R s b) facts."""

    answer = Answer(relation=relation, subject=subject_symbol)
    group = _referent_group(system, subject_symbol)
    start = _start_wigame(system, relation, subject_symbol)
    if start is None:
        return answer
    worlds = _reachable_worlds(system, start, group, hops)
    for symbol in sorted(group):
        context = symbol.split("@", 1)[-1]
        world_id = f"wigame:{context}:{relation}"
        if world_id in system.wigames and world_id not in worlds:
            worlds.append(world_id)
    answer.path = worlds
    for world_id in worlds:
        wigame = system.wigames[world_id]
        for fact in wigame.facts.values():
            proposition = fact.proposition
            if proposition.relation_id != relation or fact.truth.value != "true":
                continue
            if proposition.subject_symbol_id not in group:
                continue
            object_symbol = proposition.object_symbol_id
            signs = _signs_of(system, object_symbol)
            answer.objects.append(
                (object_symbol, object_symbol.split("@", 1)[-1], signs, list(fact.evidence.get("prov", [])))
            )
    answer.objects = _dedupe(answer.objects)
    if object_norm is not None and answer.truth_for(object_norm) == "true":
        return answer
    if object_norm is not None and _is_explicitly_false(system, worlds, group, object_norm, relation):
        answer.explicit_false = True
    return answer


def _signs_of(system: Any, symbol_id: str) -> set[str]:
    symbol = system.symbols.get(symbol_id)
    return set(symbol.signs) if symbol is not None else {symbol_id.split("@", 1)[0]}


def _referent_group(system: Any, symbol_id: str) -> set[str]:
    referent = referent_of(system, symbol_id)
    if referent is None:
        return {symbol_id}
    return {other for other in system.symbols if referent_of(system, other) == referent}


def _start_wigame(system: Any, relation: str, subject_symbol: str) -> str | None:
    context = subject_symbol.split("@", 1)[-1]
    candidate = f"wigame:{context}:{relation}"
    if candidate in system.wigames and subject_symbol in system.wigames[candidate].axis_a:
        return candidate
    for world_id, wigame in sorted(system.wigames.items()):
        if wigame.relation_id == relation and subject_symbol in wigame.axis_a:
            return world_id
    return None


def _reachable_worlds(system: Any, start: str, group: set[str], hops: int) -> list[str]:
    reached = [start]
    frontier = [start]
    for _ in range(max(hops, 0)):
        next_frontier: list[str] = []
        for world_id in frontier:
            for projection in system.projections.values():
                target = _projection_neighbour(projection, world_id, group)
                if target is None or target in reached:
                    continue
                reached.append(target)
                next_frontier.append(target)
        if not next_frontier:
            break
        frontier = next_frontier
    return reached


def _projection_neighbour(projection: Any, world_id: str, group: set[str]) -> str | None:
    """Returns the neighbour reachable through one projection, if the group is linked.

    A projection between two converged worlds is usable in both directions: the
    referent group is what travels, not the symbol order.
    """

    if projection.source_wigame_id == world_id:
        if any(symbol in projection.row_axis and any(projection.row(symbol).values()) for symbol in group):
            return projection.target_wigame_id
        return None
    if projection.target_wigame_id == world_id:
        if any(symbol in projection.column_axis and any(projection.column(symbol).values()) for symbol in group):
            return projection.source_wigame_id
    return None


def _is_explicitly_false(
    system: Any,
    worlds: list[str],
    group: set[str],
    object_norm: str,
    relation: str,
) -> bool:
    wanted = normalize(object_norm)
    for world_id in worlds:
        wigame = system.wigames[world_id]
        for column in wigame.axis_b:
            if normalize(column) != wanted:
                continue
            for subject in group:
                if subject in wigame.axis_a and wigame.Vi.get(subject, column) == "false":
                    return True
    return False


def _dedupe(objects: list[tuple]) -> list[tuple]:
    seen: set[tuple[str, str]] = set()
    unique: list[tuple] = []
    for symbol, ctx, signs, prov in objects:
        key = (symbol, ctx)
        if key in seen:
            continue
        seen.add(key)
        unique.append((symbol, ctx, signs, prov))
    return unique
