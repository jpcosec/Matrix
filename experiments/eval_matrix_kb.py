"""Evaluate configuration convergence against the hand-curated aliases of the Matrix KBs.

The example KBs of the original Matrix repository (``kb_wikipedia_10_articles``,
``kb_wikipedia_marie_curie``) ship two artifacts that make them an external
ground truth:

- ``proposals/*.jsonl``: one accepted proposal per line, with ``context``,
  ``relation``, ``subject``, ``object`` and their surface signs. Each proposal
  becomes one :class:`~pipeline.decompose.Declaration` whose symbols are
  ``signo@contexto``.
- ``aliases.yaml``: **hand curation** ``aliases: [{context, symbol, canonical}]``
  (``niels_bohr/heinstein -> albert_einstein``, ``lise_meitner/she -> lise_meitner``).
  It is the identity ground truth against which the convergence is scored.

The script converges the symbols with the real pipeline (the same
``ingest_contexts`` and ``converge_in_batches`` used on the physicists corpus) and
compares the promoted and proposed identities against the curation. Nothing here
touches the thresholds of ``phi``: only ``min_contexts`` and ``taut_df`` are
parameterised, because run B and C of the brief measure exactly the effect of the
corroboration and tautology filters.
"""

from __future__ import annotations

import argparse
import json
import resource
from collections import Counter, defaultdict
from pathlib import Path
from time import perf_counter
from typing import Any, Callable

import yaml

from populator.contexts import Chunk, ContextIndex, LocalSign
from pipeline.convergence import _configurations, converge_in_batches
from pipeline.decompose import Declaration
from pipeline.ingest import ingest_contexts

PHI_MIN = 0.90
MIN_SUPPORT = 2
MAX_CONFIG_SIZE = 500
PRONOUN_SLUGS = {"he", "she", "it", "they", "his", "her"}
SUPPORT_BINS = ((0, "0"), (1, "1"), (2, "2"), (3, ">=3"))


def _slug(text: str) -> str:
    """Returns the slug of a proposal field (spaces become underscores)."""

    return text.strip().replace(" ", "_")


def read_proposals(kb_dir: Path) -> list[dict[str, Any]]:
    """Reads every ``proposals/*.jsonl`` of a KB, sorted by file name and line."""

    entries: list[dict[str, Any]] = []
    for path in sorted((kb_dir / "proposals").glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def read_aliases(kb_dir: Path) -> list[dict[str, str]]:
    """Reads the ``aliases`` list of the hand curation of a KB."""

    path = kb_dir / "aliases.yaml"
    if not path.exists():
        return []
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return list(payload.get("aliases") or [])


def build_declarations(proposals: list[dict[str, Any]]) -> tuple[list[Declaration], int]:
    """Turns proposals into context-scoped declarations, dropping exact repeats."""

    declarations: list[Declaration] = []
    seen: set[tuple[str, str, str, str]] = set()
    dropped = 0
    for entry in proposals:
        ctx_id = str(entry["context"])
        relation = str(entry["relation"])
        a = f"{_slug(str(entry['subject']))}@{ctx_id}"
        b = f"{_slug(str(entry['object']))}@{ctx_id}"
        key = (ctx_id, relation, a, b)
        if key in seen:
            dropped += 1
            continue
        seen.add(key)
        declarations.append(
            Declaration(
                ctx_id=ctx_id,
                relation=relation,
                a=a,
                b=b,
                a_sign=str(entry.get("subject_sign", entry["subject"])),
                b_sign=str(entry.get("object_sign", entry["object"])),
                sentence_index=len(declarations),
                span=(0, 0),
                source="matrix_kb",
            )
        )
    return declarations, dropped


def build_context_index(declarations: list[Declaration]) -> list[ContextIndex]:
    """Builds the minimal ``ContextIndex`` the ingestion and convergence need.

    The KB has no source text, so the contexts are reconstructed from the
    declarations: one chunk per context and one ``LocalSign`` per slug, with
    ``norm`` equal to the slug itself and ``kind="pronoun"`` for the pronouns the
    curation resolves.
    """

    signs_by_ctx: dict[str, dict[str, LocalSign]] = defaultdict(dict)
    for declaration in declarations:
        for symbol in (declaration.a, declaration.b):
            ctx_id = declaration.ctx_id
            slug = symbol.rsplit("@", 1)[0]
            if slug not in signs_by_ctx[ctx_id]:
                kind = "pronoun" if slug in PRONOUN_SLUGS else "name"
                signs_by_ctx[ctx_id][slug] = LocalSign(
                    sign=slug, norm=slug, ctx_id=ctx_id, occurrences=[], kind=kind  # type: ignore[arg-type]
                )
    contexts: list[ContextIndex] = []
    for ctx_id in sorted(signs_by_ctx):
        chunk = Chunk(ctx_id=ctx_id, document_id=ctx_id, title=ctx_id, text="", char_offset=0)
        contexts.append(ContextIndex(chunk=chunk, sentences=[], signs=signs_by_ctx[ctx_id]))
    return contexts


def _pair(first: str, second: str) -> tuple[str, str]:
    return (first, second) if first <= second else (second, first)


def gold_classes(
    aliases: list[dict[str, str]],
    declarations: list[Declaration],
) -> tuple[dict[str, str], dict[str, set[str]], dict[tuple[str, str], str], list[str]]:
    """Returns ``symbol -> canonical``, the classes, the gold pairs and what was dropped.

    ``canonical@context`` joins a class only when that symbol exists in the
    declarations of the context; aliases naming a symbol the extraction never
    produced cannot be evaluated and are reported as dropped.
    """

    symbols_by_ctx: dict[str, set[str]] = defaultdict(set)
    for declaration in declarations:
        symbols_by_ctx[declaration.ctx_id].update((declaration.a, declaration.b))

    symbol_canonical: dict[str, str] = {}
    classes: dict[str, set[str]] = defaultdict(set)
    dropped: list[str] = []
    for entry in aliases:
        ctx_id = str(entry["context"])
        canonical = str(entry["canonical"])
        candidates = [f"{_slug(str(entry['symbol']))}@{ctx_id}", f"{_slug(canonical)}@{ctx_id}"]
        for symbol in candidates:
            if symbol not in symbols_by_ctx.get(ctx_id, set()):
                continue
            symbol_canonical.setdefault(symbol, canonical)
            if symbol_canonical[symbol] != canonical:
                continue
            classes[canonical].add(symbol)
        alias_symbol = candidates[0]
        if alias_symbol not in symbols_by_ctx.get(ctx_id, set()):
            dropped.append(alias_symbol)

    gold: dict[tuple[str, str], str] = {}
    for canonical, members in classes.items():
        ordered = sorted(members)
        for index, first in enumerate(ordered):
            for second in ordered[index + 1 :]:
                gold[_pair(first, second)] = canonical
    return symbol_canonical, dict(classes), gold, dropped


def _variables(declarations: list[Declaration]) -> set[str]:
    counts: Counter[str] = Counter()
    for declaration in declarations:
        counts[declaration.a] += 1
        counts[declaration.b] += 1
    return {symbol for symbol, count in counts.items() if count >= MIN_SUPPORT}


def _binary_metrics(predicted: set[tuple[str, str]], gold: set[tuple[str, str]]) -> dict[str, Any]:
    correct = predicted & gold
    precision = len(correct) / len(predicted) if predicted else None
    recall = len(correct) / len(gold) if gold else None
    if precision is None or recall is None:
        f1 = None
    elif precision + recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * recall / (precision + recall)
    return {
        "predicted": len(predicted),
        "gold": len(gold),
        "correct": len(correct),
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_pairs": sorted(predicted - gold),
        "missed_pairs": sorted(gold - predicted),
    }


def _split_metrics(
    predicted: set[tuple[str, str]],
    gold: set[tuple[str, str]],
    keep: Callable[[tuple[str, str]], bool],
) -> dict[str, Any]:
    """Scores a pair set separately for intra-context and cross-context pairs."""

    result: dict[str, Any] = {}
    for label, same in (("intra", True), ("cross", False)):
        gold_side = {
            pair for pair in gold if keep(pair) and (pair[0].rsplit("@", 1)[1] == pair[1].rsplit("@", 1)[1]) == same
        }
        predicted_side = {
            pair for pair in predicted if keep(pair) and (pair[0].rsplit("@", 1)[1] == pair[1].rsplit("@", 1)[1]) == same
        }
        result[label] = _binary_metrics(predicted_side, gold_side)
    return result


def _config_sets(
    configurations: dict[str, set[str]],
) -> dict[str, set[str]]:
    """Inverts a configuration map into ``symbol -> configurations``."""

    sets: dict[str, set[str]] = defaultdict(set)
    for key, members in configurations.items():
        if len(members) > MAX_CONFIG_SIZE:
            continue
        for symbol in members:
            sets[symbol].add(key)
    return dict(sets)


def _shared_count(sets: dict[str, set[str]], first: str, second: str) -> int:
    return len(sets.get(first, set()) & sets.get(second, set()))


def _support_bin(shared: int) -> str:
    label = "0"
    for threshold, name in SUPPORT_BINS:
        if shared >= threshold:
            label = name
    return label


def _promoted_pairs(report: Any) -> dict[tuple[str, str], dict[str, Any]]:
    """Promoted pairs by referent (``equivalent``) or by promoted projection."""

    promoted: dict[tuple[str, str], dict[str, Any]] = {}
    for entry in report.promoted:
        key = _pair(entry["source"], entry["target"])
        info = promoted.setdefault(key, {"kinds": set(), "phi": 0.0, "relations": set()})
        info["kinds"].add(entry["kind"])
        info["relations"].add(entry.get("relation"))
        info["phi"] = max(info["phi"], float(entry.get("phi", 0.0)))
    groups: dict[str, set[str]] = defaultdict(set)
    for symbol, referent in report.referents.items():
        groups[referent].add(symbol)
    for members in groups.values():
        ordered = sorted(members)
        for index, first in enumerate(ordered):
            for second in ordered[index + 1 :]:
                info = promoted.setdefault(_pair(first, second), {"kinds": set(), "phi": 0.0, "relations": set()})
                info["kinds"].add("equivalent_referent")
    return promoted


def _proposed_pairs(report: Any) -> dict[tuple[str, str], dict[str, Any]]:
    proposed: dict[tuple[str, str], dict[str, Any]] = {}
    for entry in report.proposed:
        phi = float(entry.get("phi", 0.0))
        if phi < PHI_MIN:
            continue
        key = _pair(entry["source"], entry["target"])
        info = proposed.setdefault(key, {"kinds": set(), "phi": 0.0})
        info["kinds"].add(entry["kind"])
        info["phi"] = max(info["phi"], phi)
    return proposed


def _ranking(
    symbol_canonical: dict[str, str],
    classes: dict[str, set[str]],
    candidate_scores: dict[tuple[str, str], float],
) -> dict[str, Any]:
    """Ranks, for every symbol with a curated alias, the first gold coreferent."""

    outgoing: dict[str, list[tuple[float, str]]] = defaultdict(list)
    for (source, target), phi in candidate_scores.items():
        if source == target:
            continue
        outgoing[source].append((float(phi), target))

    queries = 0
    reciprocal = 0.0
    hit_1 = 0
    hit_3 = 0
    ranked = 0
    with_coreferent = 0
    reciprocal_with = 0.0
    no_candidates = 0
    details: list[dict[str, Any]] = []
    for symbol in sorted(symbol_canonical):
        canonical = symbol_canonical[symbol]
        coreferents = classes.get(canonical, set()) - {symbol}
        queries += 1
        if not coreferents:
            details.append({"symbol": symbol, "canonical": canonical, "rank": None, "reason": "no_coreferent"})
            continue
        with_coreferent += 1
        candidates = sorted(outgoing.get(symbol, []), key=lambda item: (-item[0], item[1]))
        if not candidates:
            no_candidates += 1
        position = None
        for index, (_, target) in enumerate(candidates):
            if target in coreferents:
                position = index + 1
                break
        if position is None:
            details.append(
                {
                    "symbol": symbol,
                    "canonical": canonical,
                    "rank": None,
                    "candidates": len(candidates),
                    "reason": "coreferent_not_candidate",
                }
            )
            continue
        ranked += 1
        reciprocal += 1.0 / position
        reciprocal_with += 1.0 / position
        if position == 1:
            hit_1 += 1
        if position <= 3:
            hit_3 += 1
        details.append({"symbol": symbol, "canonical": canonical, "rank": position, "candidates": len(candidates)})
    return {
        "queries": queries,
        "queries_with_coreferent": with_coreferent,
        "ranked": ranked,
        "unranked": queries - ranked,
        "no_candidates": no_candidates,
        "mrr": reciprocal / queries if queries else None,
        "hit1": hit_1 / queries if queries else None,
        "hit3": hit_3 / queries if queries else None,
        "mrr_with_coreferent": reciprocal_with / with_coreferent if with_coreferent else None,
        "details": details,
    }


def evaluate(
    kb_dir: str | Path,
    out_dir: str | Path,
    min_contexts: int = 2,
    taut_df: float = 0.30,
    phi_min: float = PHI_MIN,
) -> dict[str, Any]:
    """Converges one KB and scores it against its hand-curated aliases."""

    kb_path = Path(kb_dir)
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    started = perf_counter()

    proposals = read_proposals(kb_path)
    aliases = read_aliases(kb_path)
    declarations, duplicates = build_declarations(proposals)
    contexts = build_context_index(declarations)

    from src.operational_model import LogicalSystem, SExpressionRuntime

    system = LogicalSystem()
    runtime = SExpressionRuntime(system)
    ingest_report = ingest_contexts(system, runtime, contexts, declarations)
    convergence_started = perf_counter()
    report = converge_in_batches(
        system,
        contexts,
        declarations,
        min_contexts=min_contexts,
        taut_df=taut_df,
        phi_min=phi_min,
    )
    convergence_seconds = round(perf_counter() - convergence_started, 3)

    norms = {sign.symbol_id: sign.norm for context in contexts for sign in context.signs.values()}
    variables = _variables(declarations)
    all_symbols = {symbol for declaration in declarations for symbol in (declaration.a, declaration.b)}
    raw_configurations = _configurations(declarations, norms, {}, all_symbols, 1, 1.0)
    kept_configurations = _configurations(
        declarations, norms, report.referents, variables, min_contexts, taut_df
    )
    raw_sets = _config_sets(raw_configurations)
    kept_sets = _config_sets(kept_configurations)

    symbol_canonical, classes, gold, dropped_aliases = gold_classes(aliases, declarations)
    promoted = _promoted_pairs(report)
    proposed = _proposed_pairs(report)
    union = dict(promoted)
    for key, value in proposed.items():
        union.setdefault(key, value)

    gold_pairs = set(gold)
    variable_pair = lambda pair: pair[0] in variables and pair[1] in variables  # noqa: E731
    always = lambda pair: True  # noqa: E731

    scores: dict[str, Any] = {}
    for predicted_name, predicted_map in (
        ("promoted", promoted),
        ("promoted_or_proposed", union),
    ):
        predicted_pairs = set(predicted_map)
        for universe_name, keep in (("all", always), ("variables", variable_pair)):
            scores[f"{predicted_name}_{universe_name}"] = _split_metrics(predicted_pairs, gold_pairs, keep)

    false_merges: list[dict[str, Any]] = []
    unknown_pairs: list[dict[str, Any]] = []
    for key in sorted(promoted):
        first, second = key
        canonical_a = symbol_canonical.get(first)
        canonical_b = symbol_canonical.get(second)
        info = promoted[key]
        entry = {
            "source": first,
            "target": second,
            "kinds": sorted(info["kinds"]),
            "phi": round(info["phi"], 4),
            "shared_configurations": _shared_count(kept_sets, first, second),
            "shared_configurations_raw": _shared_count(raw_sets, first, second),
            "canonical_a": canonical_a,
            "canonical_b": canonical_b,
        }
        if canonical_a and canonical_b and canonical_a != canonical_b:
            false_merges.append(entry)
        elif not canonical_a or not canonical_b:
            unknown_pairs.append(entry)

    support_histogram = Counter()
    support_histogram_raw = Counter()
    diagnoses: list[dict[str, Any]] = []
    for key, canonical in sorted(gold.items()):
        first, second = key
        shared_kept = _shared_count(kept_sets, first, second)
        shared_raw = _shared_count(raw_sets, first, second)
        support_histogram[_support_bin(shared_kept)] += 1
        support_histogram_raw[_support_bin(shared_raw)] += 1
        forward = report.candidate_scores.get((first, second))
        backward = report.candidate_scores.get((second, first))
        diagnoses.append(
            {
                "pair": [first, second],
                "canonical": canonical,
                "intra_context": first.rsplit("@", 1)[1] == second.rsplit("@", 1)[1],
                "configurations_a_raw": len(raw_sets.get(first, set())),
                "configurations_b_raw": len(raw_sets.get(second, set())),
                "configurations_a_kept": len(kept_sets.get(first, set())),
                "configurations_b_kept": len(kept_sets.get(second, set())),
                "shared_raw": shared_raw,
                "shared_kept": shared_kept,
                "phi_forward": round(forward, 4) if forward is not None else None,
                "phi_backward": round(backward, 4) if backward is not None else None,
                "promoted": key in promoted,
                "proposed": key in proposed,
            }
        )
    recovered = [item for item in diagnoses if item["promoted"] or item["proposed"]]
    unrecovered = [item for item in diagnoses if not item["promoted"] and not item["proposed"]]

    correct_promoted = [
        {
            "source": key[0],
            "target": key[1],
            "kinds": sorted(promoted[key]["kinds"]),
            "phi": round(promoted[key]["phi"], 4),
            "shared_configurations": _shared_count(kept_sets, key[0], key[1]),
            "shared_configurations_raw": _shared_count(raw_sets, key[0], key[1]),
            "canonical": gold.get(key),
            "intra_context": key[0].rsplit("@", 1)[1] == key[1].rsplit("@", 1)[1],
        }
        for key in sorted(promoted)
        if key in gold
    ]

    metrics: dict[str, Any] = {
        "kb": str(kb_path),
        "config": {"min_contexts": min_contexts, "taut_df": taut_df, "phi_min": phi_min},
        "world": {
            "contexts": len(contexts),
            "proposals": len(proposals),
            "declarations": len(declarations),
            "duplicate_proposals_dropped": duplicates,
            "ingested_symbols": ingest_report.symbols,
            "ingested_wigames": ingest_report.wigames,
            "ingested_facts": ingest_report.asserted,
            "symbols": len(all_symbols),
            "variables": len(variables),
            "configurations_raw": len(raw_configurations),
            "configurations_kept": len(kept_configurations),
            "tautological_configurations": report.tautological_configurations[:10],
            "candidates": len(report.candidate_scores),
            "candidates_over_phi_min": report.candidates_count,
            "promoted": len(promoted),
            "proposed": len(proposed),
            "referents": len({referent for referent in report.referents.values()}),
            "batches": report.batches,
            "iterations": report.iterations,
            "isolated": len(report.isolated),
            "declarations_per_symbol": _declaration_stats(declarations),
            "top_candidates": sorted(
                (
                    {"source": source, "target": target, "phi": round(float(phi), 4)}
                    for (source, target), phi in report.candidate_scores.items()
                ),
                key=lambda item: (-item["phi"], item["source"], item["target"]),
            )[:20],
        },
        "gold": {
            "aliases": len(aliases),
            "aliases_dropped": sorted(dropped_aliases),
            "classes": len(classes),
            "pairs": len(gold_pairs),
            "pairs_intra": sum(1 for pair in gold_pairs if pair[0].rsplit("@", 1)[1] == pair[1].rsplit("@", 1)[1]),
            "pairs_cross": sum(1 for pair in gold_pairs if pair[0].rsplit("@", 1)[1] != pair[1].rsplit("@", 1)[1]),
            "pairs_variables": sum(1 for pair in gold_pairs if variable_pair(pair)),
        },
        "scores": scores,
        "false_merges": {"count": len(false_merges), "pairs": false_merges},
        "promoted_unknown": {"count": len(unknown_pairs), "pairs": unknown_pairs[:20]},
        "ranking": _ranking(symbol_canonical, classes, report.candidate_scores),
        "support": {
            "histogram_kept": {label: support_histogram[label] for _, label in SUPPORT_BINS},
            "histogram_raw": {label: support_histogram_raw[label] for _, label in SUPPORT_BINS},
            "recovered": len(recovered),
            "unrecovered": len(unrecovered),
            "max_phi_gold": max(
                (
                    max(item["phi_forward"] or 0.0, item["phi_backward"] or 0.0)
                    for item in diagnoses
                ),
                default=0.0,
            ),
            "diagnoses": diagnoses,
        },
        "timings": {
            "convergence_s": convergence_seconds,
            "total_s": round(perf_counter() - started, 3),
            "peak_memory_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1),
        },
    }
    metrics["correct_promoted"] = correct_promoted
    metrics["unrecovered_pairs"] = sorted(
        unrecovered, key=lambda item: (-item["shared_kept"], item["pair"])
    )

    (root / "metrics.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False, default=_json_default), encoding="utf-8"
    )
    (root / "report.md").write_text(_report(metrics), encoding="utf-8")
    return metrics


def _declaration_stats(declarations: list[Declaration]) -> dict[str, float]:
    """Mean, median and maximum declarations per symbol (the support of §5.8)."""

    counts: Counter[str] = Counter()
    for declaration in declarations:
        counts[declaration.a] += 1
        counts[declaration.b] += 1
    values = sorted(counts.values())
    if not values:
        return {"mean": 0.0, "median": 0.0, "max": 0}
    middle = len(values) // 2
    median = values[middle] if len(values) % 2 else (values[middle - 1] + values[middle]) / 2
    return {
        "mean": round(sum(values) / len(values), 3),
        "median": float(median),
        "max": values[-1],
    }


def _json_default(value: Any) -> Any:
    if isinstance(value, (set, frozenset)):
        return sorted(value)
    if isinstance(value, tuple):
        return list(value)
    raise TypeError(f"not JSON serialisable: {type(value)!r}")


def _pair_table(items: list[dict[str, Any]], limit: int | None = None) -> list[str]:
    lines = [
        "| Par | Tipo | φ | Configuraciones compartidas | Contextos |",
        "|---|---|---|---|---|",
    ]
    for item in items[: limit or len(items)]:
        kind = ",".join(item.get("kinds", [])) or item.get("kind", "")
        lines.append(
            f"| `{item['source']}` ~ `{item['target']}` | {kind} | {item['phi']} | "
            f"{item['shared_configurations']} | "
            f"{'intra' if item.get('intra_context') else 'entre contextos'} |"
        )
    if not items:
        lines.append("| (ninguno) | | | | |")
    return lines


def _report(metrics: dict[str, Any]) -> str:
    config = metrics["config"]
    world = metrics["world"]
    gold = metrics["gold"]
    scores = metrics["scores"]
    ranking = metrics["ranking"]
    lines: list[str] = [
        f"# Convergencia contra la curación manual — {Path(metrics['kb']).name}",
        "",
        f"Configuración: `min_contexts={config['min_contexts']}`, `taut_df={config['taut_df']}`, "
        f"`phi_min={config['phi_min']}`.",
        "",
        "## Conteos",
        "",
        "| Métrica | Valor |",
        "|---|---|",
        f"| contextos | {world['contexts']} |",
        f"| propuestas / declaraciones | {world['proposals']} / {world['declarations']} |",
        f"| símbolos / variables | {world['symbols']} / {world['variables']} |",
        f"| declaraciones por símbolo (media / mediana / máx) | "
        f"{world['declarations_per_symbol']['mean']} / {world['declarations_per_symbol']['median']} / "
        f"{world['declarations_per_symbol']['max']} |",
        f"| configuraciones (crudas / tras filtros) | {world['configurations_raw']} / {world['configurations_kept']} |",
        f"| pares candidatos (con φ / ≥ φ_min) | {world['candidates']} / {world['candidates_over_phi_min']} |",
        f"| promovidos / propuestos / referentes | {world['promoted']} / {world['proposed']} / {world['referents']} |",
        f"| aislados | {world['isolated']} |",
        f"| tiempo de convergencia / total | {metrics['timings']['convergence_s']} s / {metrics['timings']['total_s']} s |",
        f"| memoria residente máxima | {metrics['timings']['peak_memory_mb']} MB |",
        "",
        "## Oro y soporte",
        "",
        f"- Clases de equivalencia: {gold['classes']}; pares de oro: {gold['pairs']} "
        f"(intra {gold['pairs_intra']}, entre contextos {gold['pairs_cross']}, solo variables {gold['pairs_variables']}).",
        f"- Alias usados: {gold['aliases'] - len(gold['aliases_dropped'])} de {gold['aliases']} "
        f"(descartados porque el símbolo no aparece en las declaraciones: {len(gold['aliases_dropped'])}).",
        f"- Histograma de configuraciones compartidas por par de oro (tras filtros): {metrics['support']['histogram_kept']}.",
        f"- Histograma sin filtros (formas superficiales): {metrics['support']['histogram_raw']}.",
        f"- φ máxima alcanzada por algún par de oro: {metrics['support']['max_phi_gold']:.4f} "
        f"(la promoción exige 0.95 y la propuesta 0.90).",
        f"- Pares de oro recuperados (promovidos o propuestos): {metrics['support']['recovered']}; "
        f"sin recuperar: {metrics['support']['unrecovered']}.",
        "",
        "## Métricas por pares",
        "",
        "| Conjunto | Universo | Subconjunto | predichos | oro | correctos | precisión | recall | F1 |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for predicted_name in ("promoted", "promoted_or_proposed"):
        for universe_name in ("all", "variables"):
            key = f"{predicted_name}_{universe_name}"
            for side in ("intra", "cross"):
                row = scores[key][side]
                lines.append(
                    f"| {predicted_name} | {universe_name} | {side} | {row['predicted']} | {row['gold']} | "
                    f"{row['correct']} | {_num(row['precision'])} | {_num(row['recall'])} | {_num(row['f1'])} |"
                )
    lines += [
        "",
        "## Falsas fusiones",
        "",
        f"- Promociones entre símbolos que el oro asigna a `canonical` distinto: {metrics['false_merges']['count']}.",
        f"- Promociones con al menos un símbolo fuera del oro (no evaluables): {metrics['promoted_unknown']['count']}.",
        "",
    ]
    lines += _pair_table(metrics["false_merges"]["pairs"])
    lines += [
        "",
        "## Pares candidatos con mayor φ (máx. 10)",
        "",
        "| Par | φ |",
        "|---|---|",
    ]
    candidates = world.get("top_candidates") or []
    for item in candidates[:10]:
        lines.append(f"| `{item['source']}` ~ `{item['target']}` | {item['phi']} |")
    if not candidates:
        lines.append("| (ninguno: ningún par comparte una configuración) | |")
    lines += [
        "",
        "## Pares promovidos correctos (máx. 10)",
        "",
    ]
    lines += _pair_table(metrics["correct_promoted"], limit=10)
    lines += [
        "",
        "## Pares de oro no recuperados (máx. 10, ordenados por soporte compartido)",
        "",
        "| Par | canonical | contexto | declaraciones conf. (a/b, crudas) | compartidas crudas | compartidas tras filtros | φ directa / inversa |",
        "|---|---|---|---|---|---|---|",
    ]
    for item in metrics["unrecovered_pairs"][:10]:
        lines.append(
            f"| `{item['pair'][0]}` ~ `{item['pair'][1]}` | {item['canonical']} | "
            f"{'intra' if item['intra_context'] else 'entre'} | "
            f"{item['configurations_a_raw']}/{item['configurations_b_raw']} | {item['shared_raw']} | "
            f"{item['shared_kept']} | {_num(item['phi_forward'])} / {_num(item['phi_backward'])} |"
        )
    if not metrics["unrecovered_pairs"]:
        lines.append("| (ninguno) | | | | | | |")
    lines += [
        "",
        "## Ranking sobre los símbolos curados",
        "",
        f"- Consultas: {ranking['queries']} (con correferente de oro: {ranking['queries_with_coreferent']}); "
        f"resueltas: {ranking['ranked']}; sin resolver: {ranking['unranked']} "
        f"(de ellas sin ningún candidato: {ranking['no_candidates']}).",
        f"- MRR / acierto en 1 / acierto en 3 sobre todas las consultas: {_num(ranking['mrr'])} / "
        f"{_num(ranking['hit1'])} / {_num(ranking['hit3'])}.",
        f"- MRR sobre las consultas con correferente de oro: {_num(ranking['mrr_with_coreferent'])}.",
        "",
        "## Configuraciones tautológicas descartadas (máx. 10)",
        "",
    ]
    for entry in world["tautological_configurations"]:
        lines.append(f"- `{entry.get('config')}` (df={entry.get('df')}/{entry.get('contexts')})")
    if not world["tautological_configurations"]:
        lines.append("- (ninguna)")
    return "\n".join(lines) + "\n"


def _num(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def main(argv: list[str] | None = None) -> int:
    """Runs the evaluation CLI."""

    parser = argparse.ArgumentParser(
        description="Evaluate configuration convergence against the curated aliases of a Matrix KB."
    )
    parser.add_argument("kb_dir")
    parser.add_argument("--out", required=True)
    parser.add_argument("--min-contexts", type=int, default=2)
    parser.add_argument("--taut-df", type=float, default=0.30)
    parser.add_argument("--max-memory-gb", type=float, default=4.0)
    args = parser.parse_args(argv)

    if args.max_memory_gb and args.max_memory_gb > 0:
        limit_bytes = int(args.max_memory_gb * 1024**3)
        try:
            resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, limit_bytes))
        except (ValueError, OSError):
            pass

    metrics = evaluate(
        args.kb_dir,
        args.out,
        min_contexts=args.min_contexts,
        taut_df=args.taut_df,
    )
    scores = metrics["scores"]
    print(f"KB: {metrics['kb']}  config: {metrics['config']}")
    print(f"mundo: {metrics['world']}")
    for key in ("promoted_all", "promoted_variables", "promoted_or_proposed_all", "promoted_or_proposed_variables"):
        for side in ("intra", "cross"):
            row = scores[key][side]
            print(
                f"{key}/{side}: predichos={row['predicted']} oro={row['gold']} correctos={row['correct']} "
                f"P={_num(row['precision'])} R={_num(row['recall'])} F1={_num(row['f1'])}"
            )
    print(f"falsas fusiones: {metrics['false_merges']['count']}")
    print(f"ranking: {metrics['ranking']['mrr']}")
    print(f"soporte (tras filtros): {metrics['support']['histogram_kept']}")
    print(f"tiempos: {metrics['timings']}")
    print(f"informe: {Path(args.out) / 'report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
