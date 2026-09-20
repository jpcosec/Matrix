"""CHIC over contexts and local symbols: taxonomy, convergence and maintenance."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from scipy import sparse

from populator.contexts import ContextIndex
from populator.tokenize import normalize
from sia.cohesion import cohesion_pair
from sia.contingency import contingency
from sia.hierarchy import build_hierarchy, classes, significant_levels
from sia.intensity import phi_entropic

from .decompose import Declaration
from .ingest import build_world

ROOT_CONTEXT = "ctx:root"
KERNEL_WIGAME = "wigame:kernel:equivalent"
KERNEL_RELATION = "equivalent"


@dataclass
class Taxonomy:
    """Feature classes over the contexts plus their nesting and membership."""

    nodes: dict[str, list[str]]
    membership: dict[str, list[str]]
    nests: list[tuple[str, str, float]]
    levels: list[int]
    features: list[str] = field(default_factory=list)
    context_nodes: dict[str, str] = field(default_factory=dict)
    parents: dict[str, str | None] = field(default_factory=dict)


@dataclass
class ConvergenceReport:
    """Result of one convergence run."""

    referents: dict[str, str] = field(default_factory=dict)
    proposed: list[dict] = field(default_factory=list)
    promoted: list[dict] = field(default_factory=list)
    isolated: list[str] = field(default_factory=list)
    scores: dict[str, float] = field(default_factory=dict)
    iterations: int = 0
    ref_counter: int = 0


@dataclass
class Maintenance:
    """Gates and discriminative dimensions proposed for one WiGame."""

    wigame_id: str
    gates: list[dict] = field(default_factory=list)
    collisions: list[tuple[str, str]] = field(default_factory=list)
    discriminants: dict[tuple[str, str], str | None] = field(default_factory=dict)
    unresolved: list[tuple[str, str]] = field(default_factory=list)


def context_taxonomy(
    system: Any,
    contexts: list[ContextIndex],
    declarations: list[Declaration],
    min_support: int = 2,
) -> Taxonomy:
    """Builds the Context tree from contexts x features and their nesting."""

    ctx_ids = [context.chunk.ctx_id for context in contexts]
    feature_sets: dict[str, set[str]] = {ctx_id: set() for ctx_id in ctx_ids}
    for context in contexts:
        for sign in context.signs.values():
            if sign.kind in {"term", "name"}:
                feature_sets[context.chunk.ctx_id].add(f"sign:{sign.norm}")
    for declaration in declarations:
        feature_sets.setdefault(declaration.ctx_id, set()).add(
            f"config:{declaration.relation}:{normalize(declaration.b_sign)}"
        )
    support: Counter[str] = Counter(feature for features in feature_sets.values() for feature in features)
    features = sorted(feature for feature, count in support.items() if count >= min_support)
    if len(features) < 2:
        return Taxonomy(nodes={}, membership={}, nests=[], levels=[], features=features)

    index = {feature: position for position, feature in enumerate(features)}
    rows: list[int] = []
    columns: list[int] = []
    for row, ctx_id in enumerate(ctx_ids):
        for feature in feature_sets[ctx_id]:
            if feature in index:
                rows.append(row)
                columns.append(index[feature])
    matrix = sparse.csr_matrix(
        (np.ones(len(rows), dtype=np.int8), (rows, columns)),
        shape=(len(ctx_ids), len(features)),
    )
    matrix.data[:] = 1

    counts = contingency(matrix)
    cohesion = cohesion_pair(phi_entropic(counts))
    levels = build_hierarchy(cohesion)
    significant = significant_levels(levels, cohesion)
    relevant = sorted({*significant, *_maximal_levels(levels)})
    seen_classes: set[frozenset[int]] = set()
    nodes: dict[str, list[str]] = {}
    for level_index in relevant:
        level = levels[level_index]
        if len(level.cls) < 2:
            continue
        key = frozenset(level.cls)
        if key in seen_classes:
            continue
        seen_classes.add(key)
        nodes[f"ctx:class:{len(nodes)}"] = [features[position] for position in level.cls]

    parents: dict[str, str | None] = {}
    for node_id, feature_class in nodes.items():
        container_set = set(feature_class)
        containers = [
            (other, other_class)
            for other, other_class in nodes.items()
            if other != node_id and container_set < set(other_class)
        ]
        parents[node_id] = min(containers, key=lambda item: len(item[1]))[0] if containers else None

    membership: dict[str, list[str]] = {}
    context_nodes: dict[str, str] = {}
    for node_id, feature_class in nodes.items():
        members = [
            ctx_id
            for ctx_id in ctx_ids
            if _contribution(feature_sets[ctx_id], feature_class) >= 0.5
        ]
        membership[node_id] = members
        for ctx_id in members:
            context_nodes[ctx_id] = _deepest_node(context_nodes.get(ctx_id), node_id, parents)
    nests = _nesting(matrix, min_support)

    _materialize_contexts(system, nodes, membership, parents)
    return Taxonomy(
        nodes=nodes,
        membership=membership,
        nests=nests,
        levels=significant,
        features=features,
        context_nodes=context_nodes,
        parents=parents,
    )


def _maximal_levels(levels: list[Any]) -> list[int]:
    """Returns the levels whose class is not contained in any other class."""

    class_sets = [set(level.cls) for level in levels]
    return [
        index
        for index, current in enumerate(class_sets)
        if not any(current < other for other_index, other in enumerate(class_sets) if other_index != index)
    ]


def _contribution(features: set[str], feature_class: list[str]) -> float:
    present = sum(1 for feature in feature_class if feature in features)
    return present / len(feature_class) if feature_class else 0.0


def _deepest_node(current: str | None, node_id: str, parents: dict[str, str | None]) -> str:
    if current is None:
        return node_id
    while parents.get(node_id) is not None:
        node_id = parents[node_id] or node_id
    return node_id


def _nesting(matrix: sparse.csr_matrix, min_support: int) -> list[tuple[str, str, float]]:
    """Returns the directed context inclusion edges (A fits in B)."""

    transposed = matrix.T.tocsr()
    counts = contingency(transposed)
    phi = phi_entropic(counts)
    nests: list[tuple[str, str, float]] = []
    size = phi.shape[0]
    for first in range(size):
        if counts.n_a[first] < min_support:
            continue
        for second in range(size):
            if first == second:
                continue
            value = float(phi[first, second])
            if value >= 0.9:
                nests.append((f"ctx#{first}", f"ctx#{second}", value))
    return nests


def _materialize_contexts(
    system: Any,
    nodes: dict[str, list[str]],
    membership: dict[str, list[str]],
    parents: dict[str, str | None],
) -> None:
    """Creates the Context tree and routes every node to its member contexts."""

    from src.operational_model import Context, SExpressionRuntime

    runtime = SExpressionRuntime(system)
    runtime.evaluate(f"(create context {ROOT_CONTEXT})")
    for node_id in sorted(nodes):
        parent = parents.get(node_id) or ROOT_CONTEXT
        runtime.evaluate(f"(create context {node_id} parent:{parent})")
    for node_id, members in membership.items():
        node = system.contexts.get(node_id)
        if node is None:
            continue
        for member in members:
            node.route_to_context(member)
            context = system.contexts.get(member)
            if context is not None:
                context.metadata["parent"] = node_id


def symbol_convergence(
    system: Any,
    contexts: list[ContextIndex],
    declarations: list[Declaration],
    phi_min: float = 0.9,
    min_support: int = 3,
    min_contexts: int = 2,
    max_iter: int = 5,
) -> ConvergenceReport:
    """Proposes projections and equivalences between local symbols by convergence."""

    report = ConvergenceReport()
    norms = {sign.symbol_id: sign.norm for context in contexts for sign in context.signs.values()}
    relations: dict[str, set[str]] = defaultdict(set)
    counts_by_symbol: Counter[str] = Counter()
    for declaration in declarations:
        relations[declaration.a].add(declaration.relation)
        relations[declaration.b].add(declaration.relation)
        counts_by_symbol[declaration.a] += 1
        counts_by_symbol[declaration.b] += 1
    variables = {symbol for symbol, count in counts_by_symbol.items() if count >= min_support}
    if len(variables) < 2:
        return report
    _ensure_kernel_wigame(system, variables)

    processed: set[tuple[str, str]] = set()
    for iteration in range(max_iter):
        configurations = _configurations(
            declarations, norms, report.referents, variables, min_contexts
        )
        if len(configurations) < 2:
            break
        symbols, scores, n_st, shared_contexts = _pair_scores(
            configurations, variables, declarations, norms, report.referents
        )
        position = {symbol: index for index, symbol in enumerate(symbols)}
        for source in sorted(variables):
            incoming = [
                float(scores[position[target], position[source]])
                for target in variables
                if target != source and _ctx(target) != _ctx(source)
            ]
            report.scores[source] = max(incoming) if incoming else 0.0
            system.symbols[source].metadata["convergence_score"] = report.scores[source]
            system.symbols[source].metadata["contexts_supporting"] = len(
                {declaration.ctx_id for declaration in declarations if source in (declaration.a, declaration.b)}
            )
        promotions = 0
        for source in sorted(variables):
            for target in sorted(variables):
                if source == target or _ctx(source) == _ctx(target) or (source, target) in processed:
                    continue
                if _already_promoted(system, source, target):
                    processed.add((source, target))
                    continue
                forward = float(scores[position[source], position[target]])
                backward = float(scores[position[target], position[source]])
                if forward < phi_min:
                    continue
                processed.add((source, target))
                equivalent = backward >= phi_min
                entries = _candidate_entries(
                    system,
                    source,
                    target,
                    relations,
                    forward,
                    backward,
                    int(n_st[position[source], position[target]]),
                    shared_contexts[(source, target)],
                    equivalent,
                )
                promotion = (
                    equivalent
                    and min(forward, backward) >= 0.99
                    and int(n_st[position[source], position[target]]) >= 1
                    and len(shared_contexts[(source, target)]) >= min_contexts
                )
                for entry in entries:
                    if promotion:
                        _promote(system, entry)
                        report.promoted.append({**entry, "status": "promoted", "iteration": iteration})
                        promotions += 1
                    else:
                        report.proposed.append(entry)
                if promotion:
                    _merge_referents(report, source, target)
                    for symbol, referent in report.referents.items():
                        system.symbols[symbol].metadata["referent"] = referent
        report.iterations = iteration + 1
        if promotions == 0:
            break

    report.isolated = [
        symbol
        for symbol in sorted(variables)
        if report.scores.get(symbol, 0.0) < 0.5 and symbol not in report.referents
    ]
    return report


def _already_promoted(system: Any, source: str, target: str) -> bool:
    """Reports whether an equivalence between two symbols is already confirmed."""

    wigame = system.wigames.get(KERNEL_WIGAME)
    if wigame is None:
        return False
    wanted = {
        f"({KERNEL_RELATION} {source} {target})",
        f"({KERNEL_RELATION} {target} {source})",
    }
    return any(fact.proposition.sexpr() in wanted for fact in wigame.facts.values())


def _promote(system: Any, entry: dict) -> None:
    from src.operational_model.system.candidates import promote_candidate

    promote_candidate(system, entry["candidate_id"])


def _merge_referents(report: ConvergenceReport, source: str, target: str) -> None:
    existing = report.referents.get(source) or report.referents.get(target)
    if existing is None:
        referent = f"ref:{report.ref_counter}"
        report.ref_counter += 1
    else:
        referent = existing
        for symbol, value in list(report.referents.items()):
            if value in {report.referents.get(source), report.referents.get(target)}:
                report.referents[symbol] = referent
    report.referents[source] = referent
    report.referents[target] = referent


def _ensure_kernel_wigame(system: Any, variables: set[str]) -> None:
    from src.operational_model import SExpressionRuntime

    runtime = SExpressionRuntime(system)
    runtime.evaluate(f"(create relation {KERNEL_RELATION} {KERNEL_RELATION} commutative:true)")
    symbols = " ".join(sorted(variables))
    runtime.evaluate(
        f"(create li li:kernel:equivalent {KERNEL_RELATION} (axis-a {symbols}) (axis-b {symbols}))"
    )
    runtime.evaluate(f"(create wigame {KERNEL_WIGAME} li:kernel:equivalent)")


def _configurations(
    declarations: list[Declaration],
    norms: dict[str, str],
    referents: dict[str, str],
    variables: set[str],
    min_contexts: int = 1,
) -> dict[str, set[str]]:
    """Builds the configuration → symbols rows of the convergence matrix.

    Configurations declared in fewer than ``min_contexts`` contexts are noise
    (nothing corroborates them) and are dropped before the intensity is computed.
    """

    rows: dict[str, set[str]] = defaultdict(set)
    contexts_of: dict[str, set[str]] = defaultdict(set)
    for declaration in declarations:
        if declaration.a in variables:
            key = f"{declaration.relation}|a|{_reference(declaration.b, norms, referents)}"
            rows[key].add(declaration.a)
            contexts_of[key].add(declaration.ctx_id)
        if declaration.b in variables:
            key = f"{declaration.relation}|b|{_reference(declaration.a, norms, referents)}"
            rows[key].add(declaration.b)
            contexts_of[key].add(declaration.ctx_id)
    return {key: members for key, members in rows.items() if len(contexts_of[key]) >= max(min_contexts, 1)}


def _reference(symbol: str, norms: dict[str, str], referents: dict[str, str]) -> str:
    if symbol in referents:
        return referents[symbol]
    return norms.get(symbol, symbol.split("@")[0])


def _pair_scores(
    configurations: dict[str, set[str]],
    variables: set[str],
    declarations: list[Declaration],
    norms: dict[str, str],
    referents: dict[str, str],
) -> tuple[list[str], np.ndarray, np.ndarray, dict[tuple[str, str], set[str]]]:
    symbols = sorted(variables)
    index = {symbol: position for position, symbol in enumerate(symbols)}
    keys = list(configurations)
    rows: list[int] = []
    columns: list[int] = []
    for row, key in enumerate(keys):
        for symbol in configurations[key]:
            rows.append(row)
            columns.append(index[symbol])
    matrix = sparse.csr_matrix(
        (np.ones(len(rows), dtype=np.int8), (rows, columns)),
        shape=(len(keys), len(symbols)),
    )
    matrix.data[:] = 1
    counts = contingency(matrix)
    scores = phi_entropic(counts)
    n_st = np.asarray((matrix.T @ matrix).todense(), dtype=np.int64)
    shared_contexts: dict[tuple[str, str], set[str]] = defaultdict(set)
    contexts_by_configuration = _configuration_contexts(declarations, variables, norms, referents)
    for row, key in enumerate(keys):
        members = sorted(configurations[key])
        for first_position, first in enumerate(members):
            for second in members[first_position + 1 :]:
                contexts = contexts_by_configuration.get(key, set())
                shared_contexts[(first, second)] |= contexts
                shared_contexts[(second, first)] |= contexts
    return symbols, scores, n_st, shared_contexts


def _configuration_contexts(
    declarations: list[Declaration],
    variables: set[str],
    norms: dict[str, str],
    referents: dict[str, str],
) -> dict[str, set[str]]:
    """Returns the contexts where each configuration was declared."""

    contexts_of_configuration: dict[str, set[str]] = defaultdict(set)
    for declaration in declarations:
        if declaration.a in variables:
            key = f"{declaration.relation}|a|{_reference(declaration.b, norms, referents)}"
            contexts_of_configuration[key].add(declaration.ctx_id)
        if declaration.b in variables:
            key = f"{declaration.relation}|b|{_reference(declaration.a, norms, referents)}"
            contexts_of_configuration[key].add(declaration.ctx_id)
    return contexts_of_configuration


def _candidate_entries(
    system: Any,
    source: str,
    target: str,
    relations: dict[str, set[str]],
    forward: float,
    backward: float,
    n_st: int,
    shared: set[str],
    equivalent: bool,
) -> list[dict]:
    from src.operational_model.system.candidates import register_candidate

    entries: list[dict] = []
    for relation in sorted(relations[source] & relations[target]):
        source_wigame = f"wigame:{_ctx(source)}:{relation}"
        target_wigame = f"wigame:{_ctx(target)}:{relation}"
        if source_wigame not in system.wigames or target_wigame not in system.wigames:
            continue
        candidate = register_candidate(
            system,
            "projection",
            source_wigame,
            {"source_wigame": source_wigame, "target_wigame": target_wigame, "pairs": [[source, target]]},
            {
                "tier": "statistical",
                "curation": "proposed",
                "stats": {"phi": forward, "n_s": _declaration_count(system, source), "n_t": _declaration_count(system, target), "n_st": n_st, "contexts": len(shared)},
            },
        )
        entries.append(
            {
                "status": "proposed",
                "kind": "projection",
                "candidate_id": candidate.candidate_id,
                "source": source,
                "target": target,
                "relation": relation,
                "phi": forward,
            }
        )
    if equivalent:
        candidate = register_candidate(
            system,
            "fact",
            KERNEL_WIGAME,
            {"proposition": f"({KERNEL_RELATION} {source} {target})"},
            {
                "tier": "statistical",
                "curation": "proposed",
                "stats": {
                    "phi": min(forward, backward),
                    "phi_forward": forward,
                    "phi_backward": backward,
                    "n_st": n_st,
                    "contexts": len(shared),
                },
            },
        )
        entries.append(
            {
                "status": "proposed",
                "kind": "equivalent",
                "candidate_id": candidate.candidate_id,
                "source": source,
                "target": target,
                "phi": min(forward, backward),
            }
        )
    return entries


def _declaration_count(system: Any, symbol: str) -> int:
    wigames = [wigame for wigame in system.wigames.values() if symbol in wigame.axis_a or symbol in wigame.axis_b]
    return sum(
        1
        for wigame in wigames
        for fact in wigame.facts.values()
        if symbol in (fact.proposition.subject_symbol_id, fact.proposition.object_symbol_id)
    )


def maintain_wigame(system: Any, wigame_id: str) -> Maintenance:
    """Proposes gates for tautological columns and D_i for indistinguishable subjects."""

    from src.operational_model.system.candidates import register_candidate

    wigame = system.wigames[wigame_id]
    maintenance = Maintenance(wigame_id=wigame_id)
    for column in wigame.Vi.tautological_columns():
        subjects = [subject for subject in wigame.axis_a if wigame.Vi.get(subject, column) == "true"]
        candidate = register_candidate(
            system,
            "class",
            wigame_id,
            {"gate": column, "symbols": subjects},
            {"tier": "statistical", "curation": "proposed", "stats": {"type": "gate"}},
        )
        maintenance.gates.append({"candidate_id": candidate.candidate_id, "gate": column, "symbols": subjects})

    similarity = wigame.Vi.collapse_similarity()
    coordinates = _coordinates(wigame)
    ordering = _coordinate_order(coordinates)
    for first_index, first in enumerate(wigame.axis_a):
        for second in wigame.axis_a[first_index + 1 :]:
            if not similarity.get(first, second):
                continue
            maintenance.collisions.append((first, second))
            discriminant = _discriminant(first, second, coordinates, ordering)
            maintenance.discriminants[(first, second)] = discriminant
            if discriminant is None:
                maintenance.unresolved.append((first, second))
    return maintenance


def _coordinates(wigame: Any) -> dict[str, set[str]]:
    coordinates: dict[str, set[str]] = defaultdict(set)
    for fact in wigame.facts.values():
        if fact.truth.value == "true":
            coordinates[fact.proposition.subject_symbol_id].add(fact.proposition.object_symbol_id)
    return dict(coordinates)


def _coordinate_order(coordinates: dict[str, set[str]]) -> list[str]:
    names = sorted({coordinate for values in coordinates.values() for coordinate in values})
    if len(names) < 2:
        return names
    symbols = sorted(coordinates)
    index = {coordinate: position for position, coordinate in enumerate(names)}
    rows: list[int] = []
    columns: list[int] = []
    for row, symbol in enumerate(symbols):
        for coordinate in coordinates[symbol]:
            rows.append(row)
            columns.append(index[coordinate])
    matrix = sparse.csr_matrix(
        (np.ones(len(rows), dtype=np.int8), (rows, columns)),
        shape=(len(symbols), len(names)),
    )
    matrix.data[:] = 1
    counts = contingency(matrix)
    levels = build_hierarchy(cohesion_pair(phi_entropic(counts)))
    ordered: list[str] = []
    for level in levels:
        for position in level.cls:
            if names[position] not in ordered:
                ordered.append(names[position])
    for name in names:
        if name not in ordered:
            ordered.append(name)
    return ordered


def _discriminant(
    first: str,
    second: str,
    coordinates: dict[str, set[str]],
    ordering: list[str],
) -> str | None:
    first_values = coordinates.get(first, set())
    second_values = coordinates.get(second, set())
    for coordinate in ordering:
        if (coordinate in first_values) != (coordinate in second_values):
            return coordinate
    return None


def _ctx(symbol: str) -> str:
    return symbol.split("@", 1)[1] if "@" in symbol else symbol


def run_convergence(
    corpus_dir: str | Path,
    unit: str = "document",
    lang: str = "en",
    limit: int | None = None,
) -> tuple:
    """Builds a world from a corpus and runs taxonomy, convergence and maintenance."""

    system, runtime, contexts, declarations, report = build_world(corpus_dir, unit=unit, lang=lang, limit=limit)
    taxonomy = context_taxonomy(system, contexts, declarations)
    convergence = symbol_convergence(system, contexts, declarations)
    maintenance = {
        wigame_id: maintain_wigame(system, wigame_id)
        for wigame_id in sorted(system.wigames)
        if any(fact.truth.value == "true" for fact in system.wigames[wigame_id].facts.values())
    }
    return system, runtime, contexts, declarations, report, taxonomy, convergence, maintenance


def main(argv: list[str] | None = None) -> int:
    """Runs the convergence CLI over a corpus."""

    parser = argparse.ArgumentParser(description="Context taxonomy, symbol convergence and maintenance.")
    parser.add_argument("corpus_dir")
    parser.add_argument("--lang", choices=["es", "en"], default="en")
    parser.add_argument("--unit", choices=["document", "section"], default="document")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args(argv)

    _, _, contexts, declarations, ingest_report, taxonomy, convergence, maintenance = run_convergence(
        args.corpus_dir, unit=args.unit, lang=args.lang, limit=args.limit
    )
    gates = sum(len(item.gates) for item in maintenance.values())
    collisions = sum(len(item.collisions) for item in maintenance.values())
    print(f"contextos: {ingest_report.contexts}  wigames: {ingest_report.wigames}  declaraciones: {len(declarations)}")
    print(f"nodos de taxonomía: {len(taxonomy.nodes)}  aristas de anidamiento: {len(taxonomy.nests)}")
    print(f"referentes: {len(set(convergence.referents.values()))}  promovidos: {len(convergence.promoted)}")
    print(f"propuestos: {len(convergence.proposed)}  aislados: {len(convergence.isolated)}")
    print(f"compuertas: {gates}  colisiones: {collisions}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
