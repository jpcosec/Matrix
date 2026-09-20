"""CHIC over contexts and local symbols: taxonomy, convergence and maintenance."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import numpy as np
from scipy import sparse

from populator.contexts import ContextIndex
from populator.tokenize import normalize
from sia.cohesion import cohesion_pair
from sia.contingency import Contingency, PairContingency, contingency, contingency_pairs
from sia.hierarchy import build_hierarchy, classes, significant_levels
from sia.intensity import phi_classical, phi_classical_pairs, phi_entropic, phi_entropic_pairs

from .decompose import Declaration
from .ingest import build_world

ROOT_CONTEXT = "ctx:root"
PROMOTE_PHI = 0.95
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
class PairScores:
    """Intensity and support for the ordered pairs that share a configuration."""

    symbols: list[str]
    rows: np.ndarray
    cols: np.ndarray
    phi: np.ndarray
    n_st: np.ndarray
    oversized: list[str] = field(default_factory=list)

    def ordered(self, phi_min: float) -> list[tuple[float, str, str]]:
        """Returns the pairs above ``phi_min`` sorted by ``(-phi, source, target)``."""

        values = [
            (float(phi), self.symbols[int(row)], self.symbols[int(col)])
            for row, col, phi in zip(self.rows, self.cols, self.phi)
            if phi >= phi_min
        ]
        values.sort(key=lambda item: (-item[0], item[1], item[2]))
        return values


@dataclass
class ConvergenceReport:
    """Result of one convergence run (also carries its incremental state)."""

    referents: dict[str, str] = field(default_factory=dict)
    tautological_configurations: list[dict[str, Any]] = field(default_factory=list)
    pair_scores: dict[tuple[str, str], float] = field(default_factory=dict)
    candidates_count: int = 0
    batches: int = 0
    processed: set[tuple[str, str]] = field(default_factory=set)
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
    max_features: int | None = 600,
) -> Taxonomy:
    """Builds the Context tree from contexts x features and their nesting.

    ``max_features`` keeps the most frequent features: ``build_hierarchy`` is
    O(p^2) per level in Python, so a few thousand features take minutes while
    hundreds take under a second.
    """

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
    frequent = [feature for feature, count in support.items() if count >= min_support]
    if max_features is not None and len(frequent) > max_features:
        frequent = sorted(frequent, key=lambda feature: (-support[feature], feature))[:max_features]
    features = sorted(frequent)
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
    min_support: int = 2,
    min_contexts: int = 2,
    max_iter: int = 5,
    measure: Callable[[PairContingency], np.ndarray] = phi_classical_pairs,
    taut_df: float = 0.30,
    report: ConvergenceReport | None = None,
    max_config_size: int = 500,
) -> ConvergenceReport:
    """Proposes projections and equivalences between local symbols by convergence.

    The default measure is the **classical** ``phi`` on purpose: on real text a
    symbol takes part in few configurations, so the Poisson model of the
    contingency lies in the small-``lambda`` regime where the entropic index
    (which multiplies ``phi`` by an entropy-based ``tau``) punishes the few
    counterexamples much harder than the classical one. Promotion is
    ``phi >= promote_phi`` in both directions for an ``equivalent`` (a merged
    referent) and in one direction for a ``projection``: a projection is
    directional by definition and does not require reciprocity.

    Configurations that appear in more than ``taut_df`` of the contexts with
    declarations are *sinnlos* in the corpus (true for almost everybody) and are
    dropped before the intensity is computed. Equivalences may also be found
    inside one context (classical coreference: ``she@Q#0`` and ``marie_curie@Q#0``
    sharing informative configurations); projections always cross contexts.
    """

    report = report if report is not None else ConvergenceReport()
    norms = {sign.symbol_id: sign.norm for context in contexts for sign in context.signs.values()}
    relations: dict[str, set[str]] = defaultdict(set)
    counts_by_symbol: Counter[str] = Counter()
    contexts_by_symbol: dict[str, set[str]] = defaultdict(set)
    for declaration in declarations:
        relations[declaration.a].add(declaration.relation)
        relations[declaration.b].add(declaration.relation)
        counts_by_symbol[declaration.a] += 1
        counts_by_symbol[declaration.b] += 1
        contexts_by_symbol[declaration.a].add(declaration.ctx_id)
        contexts_by_symbol[declaration.b].add(declaration.ctx_id)
    variables = {symbol for symbol, count in counts_by_symbol.items() if count >= min_support}
    if len(variables) < 2:
        return report

    processed = report.processed
    equivalences: set[frozenset[str]] = getattr(system, "equivalences", set())
    system.equivalences = equivalences
    for symbol, referent in getattr(system, "referents", {}).items():
        report.referents.setdefault(symbol, referent)
    for iteration in range(max_iter):
        tautological: list[dict[str, Any]] = []
        configurations = _configurations(
            declarations, norms, report.referents, variables, min_contexts, taut_df, tautological
        )
        if tautological and not report.tautological_configurations:
            report.tautological_configurations = sorted(
                tautological, key=lambda entry: (-entry["df"], entry["config"])
            )[:20]
        if len(configurations) < 2:
            break
        scores = _pair_scores(
            configurations, variables, measure=measure, min_support=min_support, max_config_size=max_config_size
        )
        if scores.oversized and not report.tautological_configurations:
            report.tautological_configurations = [
                {"config": key, "df": 0, "contexts": 0, "reason": "size"}
                for key in scores.oversized[:20]
            ]
        best_incoming: dict[str, float] = {}
        pair_phi: dict[tuple[str, str], float] = {}
        pair_st: dict[tuple[str, str], int] = {}
        for row, col, phi, count in zip(scores.rows, scores.cols, scores.phi, scores.n_st):
            source = scores.symbols[int(row)]
            target = scores.symbols[int(col)]
            if _ctx(source) != _ctx(target) and float(phi) > best_incoming.get(target, 0.0):
                best_incoming[target] = float(phi)
            pair_phi[(source, target)] = float(phi)
            pair_st[(source, target)] = int(count)
            if phi >= phi_min and float(phi) > report.pair_scores.get((source, target), 0.0):
                report.pair_scores[(source, target)] = float(phi)
        for symbol in sorted(variables):
            score = best_incoming.get(symbol, 0.0)
            report.scores[symbol] = score
            system.symbols[symbol].metadata["convergence_score"] = score
            system.symbols[symbol].metadata["contexts_supporting"] = len(contexts_by_symbol.get(symbol, ()))
        candidates = scores.ordered(phi_min)
        report.candidates_count = len(candidates)
        pending = [pair for _, source, target in candidates for pair in [(source, target)] if pair not in processed]
        shared_contexts = (
            _shared_contexts_for(
                configurations,
                _configuration_contexts(declarations, variables, norms, report.referents),
                pending,
            )
            if pending
            else {}
        )
        promotions = 0
        for forward, source, target in candidates:
                if (source, target) in processed:
                    continue
                if _already_promoted(report, equivalences, source, target):
                    processed.add((source, target))
                    continue
                same_context = _ctx(source) == _ctx(target)
                backward = pair_phi.get((target, source), 0.0)
                shared = shared_contexts.get((source, target), set())
                shared_configurations = pair_st.get((source, target), 0)
                equivalent = backward >= phi_min
                informative = shared_configurations >= 2
                supported = shared_configurations >= 2 and (
                    len(shared) >= min_contexts if not same_context else True
                )
                same_referent = (
                    equivalent and min(forward, backward) >= PROMOTE_PHI and informative and supported
                )
                directional = (
                    not same_context
                    and not same_referent
                    and forward >= PROMOTE_PHI
                    and informative
                    and len(shared) >= min_contexts
                )
                entries = _candidate_entries(
                    system,
                    source,
                    target,
                    relations,
                    forward,
                    backward,
                    shared_configurations,
                    shared,
                    equivalent,
                    allow_projection=not same_context,
                )
                promoted_pair = False
                for entry in entries:
                    promote = same_referent or (directional and entry["kind"] == "projection")
                    if promote:
                        if entry.get("candidate_id"):
                            _promote(system, entry)
                        report.promoted.append({**entry, "status": "promoted", "iteration": iteration})
                        promotions += 1
                        promoted_pair = True
                    else:
                        report.proposed.append(entry)
                if promoted_pair:
                    equivalences.add(frozenset((source, target)))
                if same_referent:
                    _merge_referents(report, source, target)
                    for symbol, referent in report.referents.items():
                        system.symbols[symbol].metadata["referent"] = referent
        report.iterations = iteration + 1
        if promotions == 0:
            break

    report.promoted = _dedupe_entries(report.promoted)
    report.proposed = _dedupe_entries(report.proposed)
    system.referents = dict(report.referents)
    report.isolated = [
        symbol
        for symbol in sorted(variables)
        if report.scores.get(symbol, 0.0) < 0.5 and symbol not in report.referents
    ]
    return report


def _dedupe_entries(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keeps the highest-phi entry per (kind, source, target)."""

    best: dict[tuple[str, str, str], dict[str, Any]] = {}
    order: list[tuple[str, str, str]] = []
    for entry in entries:
        key = (str(entry.get("kind")), str(entry.get("source")), str(entry.get("target")))
        if key not in best:
            best[key] = entry
            order.append(key)
        elif float(entry.get("phi", 0.0)) > float(best[key].get("phi", 0.0)):
            best[key] = entry
    return [best[key] for key in order]


def _already_promoted(
    report: "ConvergenceReport",
    equivalences: set[frozenset[str]],
    source: str,
    target: str,
) -> bool:
    """Reports whether two symbols already share a referent."""

    if frozenset((source, target)) in equivalences:
        return True
    referent = report.referents.get(source)
    return referent is not None and report.referents.get(target) == referent


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


def _configurations(
    declarations: list[Declaration],
    norms: dict[str, str],
    referents: dict[str, str],
    variables: set[str],
    min_contexts: int = 1,
    taut_df: float = 1.0,
    tautological: list[dict[str, Any]] | None = None,
) -> dict[str, set[str]]:
    """Builds the configuration → symbols rows of the convergence matrix.

    Configurations declared in fewer than ``min_contexts`` contexts are noise
    (nothing corroborates them) and are dropped before the intensity is computed.
    Configurations in more than ``taut_df`` of the contexts with declarations are
    tautological (they discriminate nothing) and are dropped too, recorded in
    ``tautological`` when a list is given.
    """

    rows: dict[str, set[str]] = defaultdict(set)
    contexts_of: dict[str, set[str]] = defaultdict(set)
    contexts: set[str] = set()
    for declaration in declarations:
        contexts.add(declaration.ctx_id)
        if declaration.a in variables:
            key = f"{declaration.relation}|a|{_reference(declaration.b, norms, referents)}"
            rows[key].add(declaration.a)
            contexts_of[key].add(declaration.ctx_id)
        if declaration.b in variables:
            key = f"{declaration.relation}|b|{_reference(declaration.a, norms, referents)}"
            rows[key].add(declaration.b)
            contexts_of[key].add(declaration.ctx_id)
    if not contexts:
        return {}
    limit = max(taut_df, 0.0) * len(contexts)
    kept: dict[str, set[str]] = {}
    for key, members in rows.items():
        support = len(contexts_of[key])
        if support < max(min_contexts, 1):
            continue
        if support > limit:
            if tautological is not None:
                tautological.append({"config": key, "df": support, "contexts": len(contexts)})
            continue
        kept[key] = members
    return kept


def _reference(symbol: str, norms: dict[str, str], referents: dict[str, str]) -> str:
    if symbol in referents:
        return referents[symbol]
    return norms.get(symbol, symbol.split("@")[0])


def converge_in_batches(
    system: Any,
    contexts: list[ContextIndex],
    declarations: list[Declaration],
    batch_size: int = 40,
    **kwargs: Any,
) -> ConvergenceReport:
    """Maintains the language games: contexts enter in batches.

    This is the ``W_i`` maintenance of ``convergence.md`` §4: a batch of contexts
    is compared against the symbols and referents already in the world (the
    inverted index grows with each batch), never all contexts against all.
    ``max_iter`` applies inside each batch and the report is carried over, so
    referents, scores and already-processed pairs are not recomputed.
    """

    report: ConvergenceReport = kwargs.pop("report", None) or ConvergenceReport()
    by_context: dict[str, list[Declaration]] = defaultdict(list)
    for declaration in declarations:
        by_context[declaration.ctx_id].append(declaration)
    order = sorted(contexts, key=lambda context: _context_order(context.chunk.ctx_id))
    seen_contexts: list[ContextIndex] = []
    seen_declarations: list[Declaration] = []
    for start in range(0, len(order), batch_size):
        batch = order[start : start + batch_size]
        seen_contexts.extend(batch)
        for context in batch:
            seen_declarations.extend(by_context.get(context.chunk.ctx_id, []))
        report = symbol_convergence(
            system, seen_contexts, seen_declarations, report=report, **kwargs
        )
        report.batches += 1
    return report


def _context_order(ctx_id: str) -> tuple[str, int]:
    """Sorts contexts by document and section number."""

    article, _, section = ctx_id.partition("#")
    try:
        number = int(section) if section else 0
    except ValueError:
        number = 0
    return article, number


def _max_incoming(
    scores: np.ndarray,
    symbols: list[str],
    index: int,
    report_scores: dict[str, float],
) -> float:
    """Returns the largest phi arriving at one symbol from another context."""

    best = 0.0
    for row, symbol in enumerate(symbols):
        if row == index or _ctx(symbol) == _ctx(symbols[index]):
            continue
        value = float(scores[row, index])
        if value > best:
            best = value
    return best


def _candidate_mask(
    scores: np.ndarray,
    n_st: np.ndarray,
    phi_min: float,
    min_support: int,
) -> np.ndarray:
    """Marks the ordered pairs worth inspecting: enough intensity and support."""

    mask = (scores >= phi_min) & (n_st >= min_support)
    np.fill_diagonal(mask, False)
    return mask


def _shared_contexts_for(
    configurations: dict[str, set[str]],
    contexts_by_configuration: dict[str, set[str]],
    pairs: list[tuple[str, str]],
) -> dict[tuple[str, str], set[str]]:
    """Computes the shared contexts of the given ordered pairs only."""

    wanted = set(pairs) | {(target, source) for source, target in pairs}
    shared: dict[tuple[str, str], set[str]] = defaultdict(set)
    for key, members in configurations.items():
        contexts = contexts_by_configuration.get(key)
        if not contexts:
            continue
        ordered = sorted(members)
        for first_index, first in enumerate(ordered):
            for second in ordered[first_index + 1 :]:
                if (first, second) in wanted:
                    shared[(first, second)] |= contexts
                if (second, first) in wanted:
                    shared[(second, first)] |= contexts
    return shared


def _candidate_pairs(
    configurations: dict[str, set[str]],
    variables: set[str],
    min_support: int = 2,
    max_config_size: int = 500,
) -> tuple[list[str], np.ndarray, np.ndarray, np.ndarray, list[str]]:
    """Returns the ordered symbol pairs that share at least one configuration.

    Uses an inverted index (configuration → symbols) so nothing grows with the
    square of the symbol count. Configurations larger than ``max_config_size``
    symbols generate no pairs and are reported as oversized.
    """

    symbols = sorted(variables)
    index = {symbol: position for position, symbol in enumerate(symbols)}
    counts: Counter[tuple[int, int]] = Counter()
    oversized: list[str] = []
    for key, members in configurations.items():
        ordered = sorted(index[symbol] for symbol in members if symbol in index)
        if len(ordered) > max_config_size:
            oversized.append(key)
            continue
        for position, first in enumerate(ordered):
            for second in ordered[position + 1 :]:
                counts[(first, second)] += 1
                counts[(second, first)] += 1
    pairs = sorted(pair for pair, count in counts.items() if count >= min_support)
    rows = np.array([pair[0] for pair in pairs], dtype=np.int64)
    cols = np.array([pair[1] for pair in pairs], dtype=np.int64)
    n_st = np.array([counts[pair] for pair in pairs], dtype=np.int32)
    return symbols, rows, cols, n_st, oversized


def _configuration_matrix(
    configurations: dict[str, set[str]],
    symbols: list[str],
) -> sparse.csr_matrix:
    """Builds the sparse configurations x symbols matrix."""

    index = {symbol: position for position, symbol in enumerate(symbols)}
    rows: list[int] = []
    columns: list[int] = []
    for row, key in enumerate(configurations):
        for symbol in configurations[key]:
            rows.append(row)
            columns.append(index[symbol])
    matrix = sparse.csr_matrix(
        (np.ones(len(rows), dtype=np.int8), (rows, columns)),
        shape=(len(configurations), len(symbols)),
    )
    matrix.data[:] = 1
    return matrix


def _pair_scores(
    configurations: dict[str, set[str]],
    variables: set[str],
    measure: Callable[[PairContingency], np.ndarray] = phi_classical_pairs,
    min_support: int = 2,
    max_config_size: int = 500,
) -> PairScores:
    """Computes phi and the shared configuration count for the candidate pairs."""

    symbols, rows, cols, n_st, oversized = _candidate_pairs(
        configurations, variables, min_support=min_support, max_config_size=max_config_size
    )
    if rows.size == 0:
        return PairScores(symbols=symbols, rows=rows, cols=cols, phi=np.zeros(0), n_st=n_st, oversized=oversized)
    matrix = _configuration_matrix(configurations, symbols)
    pairs = contingency_pairs(matrix, rows, cols)
    phi = np.asarray(measure(pairs), dtype=np.float64)
    return PairScores(symbols=symbols, rows=rows, cols=cols, phi=phi, n_st=n_st, oversized=oversized)


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
    allow_projection: bool = True,
) -> list[dict]:
    from src.operational_model.system.candidates import register_candidate

    entries: list[dict] = []
    for relation in sorted(relations[source] & relations[target]) if allow_projection else []:
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
        entries.append(
            {
                "status": "proposed",
                "kind": "equivalent",
                "candidate_id": None,
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
    convergence = system.convergence_report
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
