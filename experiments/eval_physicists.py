"""Evaluation of routed queries and convergence on the physicists corpus."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from dataclasses import dataclass
import json
from pathlib import Path
import random
import resource
from time import perf_counter
from typing import Any

from populator import build_contexts, read_documents
from populator.contexts import ContextIndex
from populator.extract import Document
from populator.tokenize import normalize

from pipeline.convergence import context_taxonomy, converge_in_batches, symbol_convergence
from pipeline.decompose import Declaration, decompose
from pipeline.ingest import ingest_contexts
from pipeline.query import ask, referent_of

CORPUS = Path(__file__).resolve().parents[1] / "corpus" / "physicists"
QA_RELATIONS = (
    "born_in",
    "died_in",
    "award",
    "educated_at",
    "employer",
    "field",
    "discovered",
    "spouse",
)
PLANTED_COUNT = 50


@dataclass
class Evaluation:
    """Everything the report needs."""

    metrics: dict[str, Any]
    system: Any = None
    runtime: Any = None
    taxonomy: Any = None
    convergence: Any = None
    planted: list[Declaration] = None  # type: ignore[assignment]


def _symbol(label: str, qid: str) -> str:
    return f"{normalize(label).replace(' ', '_')}@{qid}"


def _first_symbol(system: Any, names: list[str]) -> str | None:
    return next((name for name in names if name in system.symbols), None)


def _pronoun_symbol(system: Any, qid: str) -> str | None:
    """Returns the pronoun symbol of one person, in the lead or the whole article."""

    for suffix in ("", "#0"):
        found = _first_symbol(system, [f"{pronoun}@{qid}{suffix}" for pronoun in ("she", "he")])
        if found:
            return found
    return None


def _label_symbol(system: Any, label: str, qid: str) -> str | None:
    base = _symbol(label, qid)
    return _first_symbol(system, [base, f"{base}#0"])


def _symbol_configs(declarations: list[Declaration], symbol: str) -> set[str]:
    """Returns the configuration keys a symbol takes part in (first-pass references)."""

    configs: set[str] = set()
    for declaration in declarations:
        if declaration.a == symbol:
            configs.add(f"{declaration.relation}|a|{normalize(declaration.b_sign)}")
        if declaration.b == symbol:
            configs.add(f"{declaration.relation}|b|{normalize(declaration.a_sign)}")
    return configs


def _article_of(ctx_id: str) -> str:
    return ctx_id.split("#", 1)[0]


def _section_of(ctx_id: str) -> int:
    if "#" not in ctx_id:
        return 0
    try:
        return int(ctx_id.split("#", 1)[1])
    except ValueError:
        return 0


def _tokens(text: str) -> set[str]:
    """Normalized token set, used for inclusion comparisons (`nobel_prize` in `... in physics`)."""

    return {token for token in normalize(text).replace("_", " ").split() if token}


def run_evaluation(
    out_dir: str | Path = "/tmp/eval/physicists",
    limit: int | None = None,
    llm: bool = False,
    seed: int = 0,
    taxonomy: bool = False,
    unit: str = "document",
    source: str = "simple",
    regime: str = "document",
    with_sections: bool = False,
    decomposer: str = "heuristic",
) -> Evaluation:
    """Builds the physicists world, converges it and measures the metrics.

    Regimes: ``document`` (Simple English, one context per article), ``section``
    (English articles split by section) and ``pairs`` (Simple English article plus
    the English lead of the same person, the multi-source regime).
    """

    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    metrics: dict[str, Any] = {}
    timings: dict[str, float] = {}
    dumps = {"path": root / "metrics.json"}
    if regime == "section":
        unit, source = "section", "en"

    start = perf_counter()
    if regime == "pairs":
        contexts = _pairs_contexts(limit, with_sections)
    else:
        directory = CORPUS / ("en" if source == "en" else "articles")
        documents = read_documents(directory)
        if limit is not None:
            documents = documents[:limit]
        contexts = build_contexts(documents, unit=unit, lang="en")
    timings["populator"] = round(perf_counter() - start, 3)

    backend = None
    if llm:
        from pipeline.curate import PiBackend

        backend = PiBackend()

    start = perf_counter()
    declarations: list[Declaration] = []
    llm_chunks = 0
    if decomposer in {"heuristic", "both"}:
        for context in contexts:
            declarations.extend(decompose(context, lang="en", backend=backend))
    if decomposer in {"llm", "both"}:
        from pipeline.llm_cache import cache_key, cached_decompose, read_cache

        cache = read_cache()
        for context in contexts:
            if cache_key(context) in cache:
                llm_chunks += 1
            declarations.extend(cached_decompose(context, None))
        if decomposer == "both":
            declarations = _dedupe_declarations(declarations)
    planted = _planted_declarations(contexts, seed=seed)
    declarations.extend(planted)
    timings["decompose"] = round(perf_counter() - start, 3)

    from src.operational_model import LogicalSystem, SExpressionRuntime

    system = LogicalSystem()
    runtime = SExpressionRuntime(system)
    start = perf_counter()
    ingest_report = ingest_contexts(system, runtime, contexts, declarations)
    timings["ingest"] = round(perf_counter() - start, 3)

    built_taxonomy = None
    if taxonomy:
        start = perf_counter()
        built_taxonomy = context_taxonomy(system, contexts, declarations)
        timings["taxonomy"] = round(perf_counter() - start, 3)

    start = perf_counter()
    convergence = converge_in_batches(system, contexts, declarations, batch_size=40)
    timings["convergence"] = round(perf_counter() - start, 3)

    metrics["world"] = {
        "contexts": ingest_report.contexts,
        "symbols": len(system.symbols),
        "wigames": len(system.wigames),
        "facts": sum(len(wigame.facts) for wigame in system.wigames.values()),
        "projections": len(system.projections),
        "promoted": len(convergence.promoted),
        "proposed": len(convergence.proposed),
        "referents": len(set(convergence.referents.values())),
        "isolated": len(convergence.isolated),
        "variables": len(convergence.scores),
        "candidate_pairs": convergence.candidates_count,
        "batches": convergence.batches,
        "taxonomy_nodes": len(built_taxonomy.nodes) if built_taxonomy else None,
    }
    _dump(metrics, root)
    metrics["pronoun_convergence"] = _pronoun_metrics(system, convergence, contexts)
    _dump(metrics, root)
    metrics["qa"] = _qa_metrics(system, declarations)
    metrics["qa_pronoun_subject"] = _qa_metrics(system, declarations, use_pronoun=True)
    metrics["garbage"] = _garbage_metrics(system, convergence, planted, declarations)
    if unit == "section":
        metrics["intra_article"] = _intra_article_metrics(system, convergence, declarations)
        metrics["false_merges"] = _false_merges(system, convergence)
        metrics["qa_hop"] = _qa_hop_metrics(system, declarations)
        metrics["garbage_converged"] = _garbage_metrics(system, convergence, planted, declarations, only_converged=True)
    if regime == "pairs":
        metrics["false_merges"] = _false_merges(system, convergence)
        metrics["decomposer"] = {
            "mode": decomposer,
            "declarations": len(declarations),
            "llm_cached_chunks": llm_chunks,
        }
        metrics["pairs"] = _pairs_convergence(system, convergence, declarations)
        metrics["pairs"]["symbol_declarations"] = _symbol_declaration_stats(declarations)
        metrics["pairs"]["shared_configs_per_pair"] = _shared_configs_per_pair(system, declarations)
        _dump(metrics, root)
        metrics["intra_context"] = _intra_context_metrics(system, convergence, declarations)
        metrics["ranking"] = _ranking_metrics(system, convergence)
        metrics["qa_pairs"] = _qa_pairs_metrics(system, declarations)
        metrics["tautological_configurations"] = convergence.tautological_configurations
    _dump(metrics, root)
    metrics["gap"] = _gap_metrics(system, convergence, contexts, declarations)
    _dump(metrics, root)
    timings["peak_memory_mb"] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1)
    timings["total"] = round(sum(value for key, value in timings.items() if key != "peak_memory_mb"), 3)
    metrics["timings"] = timings
    _dump(metrics, root)

    _dump(metrics, root)
    (root / "report.md").write_text(
        _render_report(metrics, system, runtime, convergence, planted, declarations),
        encoding="utf-8",
    )
    return Evaluation(
        metrics=metrics,
        system=system,
        runtime=runtime,
        taxonomy=built_taxonomy,
        convergence=convergence,
        planted=planted,
    )


def _dedupe_declarations(declarations: list[Declaration]) -> list[Declaration]:
    """Keeps the first declaration per (relation, a, b)."""

    seen: set[tuple[str, str, str]] = set()
    unique: list[Declaration] = []
    for declaration in declarations:
        key = (declaration.relation, declaration.a, declaration.b)
        if key in seen:
            continue
        seen.add(key)
        unique.append(declaration)
    return unique


def _symbol_declaration_stats(declarations: list[Declaration]) -> dict[str, Any]:
    """Mean and median declarations per symbol."""

    counts: Counter[str] = Counter()
    for declaration in declarations:
        counts[declaration.a] += 1
        counts[declaration.b] += 1
    values = sorted(counts.values())
    if not values:
        return {"symbols": 0, "mean": 0.0, "median": 0.0}
    middle = values[len(values) // 2]
    return {
        "symbols": len(values),
        "mean": round(sum(values) / len(values), 2),
        "median": middle,
    }


def _shared_configs_per_pair(system: Any, declarations: list[Declaration]) -> dict[str, Any]:
    """Mean shared informative configurations between the correct source pairs."""

    people = _people()
    configs: dict[str, set[str]] = {}
    shared_counts: list[int] = []
    for qid in sorted(people):
        simple = _source_symbols(system, qid, "simple")
        english = _source_symbols(system, qid, "en")
        if not simple or not english:
            continue
        for symbol in simple + english:
            configs.setdefault(symbol, _symbol_configs(declarations, symbol))
        best = max(
            len(configs[source] & configs[target]) for source in simple for target in english
        )
        shared_counts.append(best)
    if not shared_counts:
        return {"pairs": 0, "mean": 0.0}
    return {"pairs": len(shared_counts), "mean": round(sum(shared_counts) / len(shared_counts), 2)}


def _dump(metrics: dict[str, Any], root: Path) -> None:
    """Writes the metrics file (partial runs are better than no runs)."""

    (root / "metrics.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")


def _pairs_contexts(limit: int | None, with_sections: bool) -> list[ContextIndex]:
    """Simple English article plus the English lead (and optionally sections)."""

    simple_documents = read_documents(CORPUS / "articles")
    english_documents = read_documents(CORPUS / "en")
    qids = sorted(Path(document.document_id).stem for document in simple_documents)
    if limit is not None:
        qids = qids[:limit]
    wanted = set(qids)
    simple_documents = [d for d in simple_documents if Path(d.document_id).stem in wanted]
    english_documents = [d for d in english_documents if Path(d.document_id).stem in wanted]
    contexts = build_contexts(simple_documents, unit="document", lang="en")
    for context in build_contexts(english_documents, unit="section", lang="en"):
        if with_sections or context.chunk.ctx_id.endswith("#0"):
            contexts.append(context)
    return contexts


def _source_of(ctx_id: str) -> str:
    return "en" if "#" in ctx_id else "simple"


def _source_symbols(system: Any, qid: str, source: str) -> list[str]:
    """Returns the pronoun and label symbols of one person in one source.

    The label is matched by sign (the article may declare `eddington` rather than
    `arthur_eddington`): pronouns plus any symbol whose signs hold the whole label
    or its surname.
    """

    suffix = "#0" if source == "en" else ""
    context = f"{qid}{suffix}"
    label = _people().get(qid, "")
    keys = {normalize(label).replace(" ", "_")} if label else set()
    surname = normalize(label).split()[-1] if label else ""
    found: list[str] = []
    for symbol_id, symbol in sorted(system.symbols.items()):
        if not symbol_id.endswith(f"@{context}"):
            continue
        signs = {normalize(sign).replace(" ", "_") for sign in symbol.signs}
        if sign_head(symbol_id) in {"she", "he"} or (keys & signs) or (surname and surname in signs):
            found.append(symbol_id)
    return found


def sign_head(symbol_id: str) -> str:
    """Returns the normalized head of a symbol id (`she@Q1#0` -> `she`)."""

    return symbol_id.split("@", 1)[0]


def _pairs_convergence(system: Any, convergence: Any, declarations: list[Declaration]) -> dict[str, Any]:
    """Fraction of people whose Simple English and English symbols converge."""

    people = _people()
    pairs = _promoted_pairs(convergence)
    total = 0
    any_converged = 0
    breakdown = {"pronoun_pronoun": [0, 0], "label_label": [0, 0], "pronoun_label": [0, 0]}
    examples: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for qid in sorted(people):
        simple = _source_symbols(system, qid, "simple")
        english = _source_symbols(system, qid, "en")
        if not simple or not english:
            continue
        total += 1
        found = False
        for source_symbol in simple:
            for target_symbol in english:
                kind = _pair_kind(source_symbol, target_symbol)
                slot = breakdown.setdefault(kind, [0, 0])
                slot[0] += 1
                if _linked(system, convergence, source_symbol, target_symbol, pairs):
                    slot[1] += 1
                    found = True
                    if len(examples) < 10:
                        examples.append(
                            {
                                "source": source_symbol,
                                "target": target_symbol,
                                "kind": kind,
                                "phi": _pair_phi(convergence, source_symbol, target_symbol),
                                "referent": referent_of(system, source_symbol),
                            }
                        )
        any_converged += found
        if not found and len(failures) < 10:
            source_symbol = simple[0]
            target_symbol = english[0]
            source_configs = _symbol_configs(declarations, source_symbol)
            target_configs = _symbol_configs(declarations, target_symbol)
            failures.append(
                {
                    "qid": qid,
                    "source": source_symbol,
                    "target": target_symbol,
                    "source_configs": len(source_configs),
                    "target_configs": len(target_configs),
                    "shared_configs": len(source_configs & target_configs),
                    "phi": _pair_phi(convergence, source_symbol, target_symbol),
                    "shared_examples": sorted(source_configs & target_configs)[:3],
                }
            )
    return {
        "people_evaluated": total,
        "people_converged": any_converged,
        "fraction": round(any_converged / total, 3) if total else 0.0,
        "breakdown": {kind: {"pairs": counts[0], "converged": counts[1]} for kind, counts in breakdown.items()},
        "examples": examples,
        "failures": failures,
    }


def _pair_kind(first: str, second: str) -> str:
    first_head = first.split("@", 1)[0]
    second_head = second.split("@", 1)[0]
    first_pronoun = first_head in {"she", "he"}
    second_pronoun = second_head in {"she", "he"}
    if first_pronoun and second_pronoun:
        return "pronoun_pronoun"
    if first_pronoun or second_pronoun:
        return "pronoun_label"
    return "label_label"


def _intra_context_metrics(system: Any, convergence: Any, declarations: list[Declaration]) -> dict[str, Any]:
    """Fraction of contexts where the pronoun converges with the label of the same context."""

    pairs = _promoted_pairs(convergence)
    contexts: dict[str, set[str]] = defaultdict(set)
    for declaration in declarations:
        contexts[declaration.ctx_id].add(declaration.a)
        contexts[declaration.ctx_id].add(declaration.b)
    evaluated = 0
    converged = 0
    examples: list[dict[str, Any]] = []
    for ctx_id, symbols in sorted(contexts.items()):
        pronoun = next((symbol for symbol in sorted(symbols) if symbol.split("@", 1)[0] in {"she", "he"}), None)
        if pronoun is None:
            continue
        candidates = [
            symbol
            for symbol in sorted(symbols)
            if symbol != pronoun and symbol.split("@", 1)[0] not in {"she", "he"}
        ]
        if not candidates:
            continue
        evaluated += 1
        if any(_linked(system, convergence, pronoun, candidate, pairs) for candidate in candidates):
            converged += 1
        elif len(examples) < 5:
            examples.append({"context": ctx_id, "pronoun": pronoun, "candidates": candidates[:3]})
    return {
        "contexts_evaluated": evaluated,
        "contexts_converged": converged,
        "fraction": round(converged / evaluated, 3) if evaluated else 0.0,
        "examples": examples,
    }


def _ranking_metrics(system: Any, convergence: Any) -> dict[str, Any]:
    """Ranks the English lead symbols among every candidate pair of the report.

    Candidates are all symbol pairs sharing at least one configuration
    (`report.candidate_scores`). A query whose target is not a candidate is
    `unranked` and contributes zero to MRR and hit@k, which are computed over all
    queries.
    """

    people = _people()
    queries = [
        symbol
        for qid in sorted(people)
        for symbol in [f"{pronoun}@{qid}" for pronoun in ("she", "he")]
        if symbol in system.symbols
    ]
    if not queries:
        return {"queries": 0, "mrr": 0.0, "hit@1": 0.0, "hit@3": 0.0}
    pair_scores = getattr(convergence, "candidate_scores", {})
    candidates_by_source: dict[str, list[tuple[float, str]]] = defaultdict(list)
    for (source, target), phi in pair_scores.items():
        candidates_by_source[source].append((float(phi), target))
    for values in candidates_by_source.values():
        values.sort(key=lambda item: (-item[0], item[1]))
    ranks: list[int | None] = []
    for query in queries:
        qid = query.split("@", 1)[1]
        correct = set(_source_symbols(system, qid, "en"))
        candidates = candidates_by_source.get(query, [])
        ranks.append(
            next((index + 1 for index, (_, other) in enumerate(candidates) if other in correct), None)
        )
    total = len(queries)
    if not total:
        return {"queries": 0, "ranked": 0, "unranked": 0, "mrr": 0.0, "hit@1": 0.0, "hit@3": 0.0}
    ranked = [rank for rank in ranks if rank]
    return {
        "queries": total,
        "ranked": len(ranked),
        "unranked": total - len(ranked),
        "mrr": round(sum(1 / rank for rank in ranked) / total, 3),
        "hit@1": round(sum(1 for rank in ranked if rank == 1) / total, 3),
        "hit@3": round(sum(1 for rank in ranked if rank <= 3) / total, 3),
    }


def _qa_pairs_metrics(system: Any, declarations: list[Declaration]) -> dict[str, Any]:
    """Wikidata facts declared only in EN, asked from the Simple English symbol."""

    facts = _wikidata_facts()
    by_article: dict[str, list[Declaration]] = defaultdict(list)
    for declaration in declarations:
        by_article[_article_of(declaration.ctx_id)].append(declaration)
    per_relation: dict[str, dict[str, int]] = defaultdict(lambda: {"positive": 0, "recall": 0})
    for entry in facts:
        qid = entry.get("qid", "")
        candidates = by_article.get(qid, [])
        simple = _source_symbols(system, qid, "simple")
        if not simple:
            continue
        asker = simple[0]
        for fact in entry.get("facts", []):
            relation = fact.get("r")
            if relation not in QA_RELATIONS or not fact.get("b"):
                continue
            wanted = _tokens(fact["b"])
            english_only = [
                declaration
                for declaration in candidates
                if declaration.relation == relation
                and wanted <= _tokens(declaration.b_sign)
                and _source_of(declaration.ctx_id) == "en"
            ]
            if not english_only:
                continue
            per_relation[relation]["positive"] += 1
            answer = ask(system, relation, asker, None)
            if any(wanted <= _tokens(sign) for _, _, signs, _ in answer.objects for sign in signs):
                per_relation[relation]["recall"] += 1
    totals = {"positive": 0, "recall": 0}
    report: dict[str, Any] = {}
    for relation, counts in sorted(per_relation.items()):
        report[relation] = {
            "positive": counts["positive"],
            "recall": round(counts["recall"] / counts["positive"], 3) if counts["positive"] else 0.0,
        }
        for key in totals:
            totals[key] += counts[key]
    report["global"] = {
        "positive": totals["positive"],
        "recall": round(totals["recall"] / totals["positive"], 3) if totals["positive"] else 0.0,
    }
    return report


def _people() -> dict[str, str]:
    path = CORPUS / "people.csv"
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as handle:
        return {row["qid"]: row["label"] for row in csv.DictReader(handle)}


def _wikidata_facts() -> list[dict[str, Any]]:
    path = CORPUS / "facts.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _mentions() -> dict[str, list[str]]:
    path = CORPUS / "mentions.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _gap_rows(limit: int | None = None) -> list[dict[str, str]]:
    path = CORPUS / "gap-validation.tsv"
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    return rows[:limit] if limit is not None else rows


def _pronoun_metrics(system: Any, convergence: Any, contexts: list[ContextIndex]) -> dict[str, Any]:
    people = _people()
    mentions = _mentions()
    good = total = converged = 0
    for qid, label in people.items():
        pronoun = _pronoun_symbol(system, qid)
        name = _symbol(label, qid)
        if pronoun is None or name not in system.symbols:
            continue
        total += 1
        reference_p = referent_of(system, pronoun)
        reference_n = referent_of(system, name)
        if reference_p is None or reference_n is None:
            continue
        converged += 1
        if reference_p == reference_n:
            good += 1
    groups: dict[str, set[str]] = defaultdict(set)
    for symbol, referent in convergence.referents.items():
        groups[referent].add(symbol)
    false_positives = 0
    pairs = 0
    for members in groups.values():
        names = [s for s in members if "@" in s and s.split("@")[0] not in {"she", "he"}]
        pronouns = [s for s in members if s.split("@")[0] in {"she", "he"}]
        for pronoun in pronouns:
            source = pronoun.split("@", 1)[1]
            for name in names:
                target = name.split("@", 1)[1]
                if source == target:
                    continue
                pairs += 1
                if target not in mentions.get(source, []):
                    false_positives += 1
    return {
        "accuracy": round(good / converged, 3) if converged else 0.0,
        "articles_with_both_symbols": total,
        "converged_pairs": converged,
        "cross_context_pairs": pairs,
        "cross_context_without_mention": false_positives,
    }


def _gap_metrics(
    system: Any,
    convergence: Any,
    contexts: list[ContextIndex],
    declarations: list[Declaration],
) -> dict[str, Any]:
    rows = _gap_rows()
    if not rows:
        return {"rows": 0, "decided": 0, "coverage": 0.0, "accuracy": 0.0}

    from src.operational_model import SExpressionRuntime

    gap_documents = [Document(f"{row['ID']}.md", row["Text"]) for row in rows]
    gap_contexts = build_contexts(gap_documents, lang="en")
    gap_declarations: list[Declaration] = []
    for context in gap_contexts:
        gap_declarations.extend(decompose(context, lang="en"))
    ingest_contexts(system, SExpressionRuntime(system), gap_contexts, gap_declarations)
    gap_convergence = converge_in_batches(system, gap_contexts, gap_declarations, batch_size=40)

    decided = correct = 0
    for row in rows:
        pronoun_symbol = f"{normalize(row['Pronoun'])}@{row['ID']}"
        reference = referent_of(system, pronoun_symbol)
        if reference is None:
            continue
        candidate_a = f"{normalize(row['A']).replace(' ', '_')}@{row['ID']}"
        candidate_b = f"{normalize(row['B']).replace(' ', '_')}@{row['ID']}"
        reference_a = referent_of(system, candidate_a)
        reference_b = referent_of(system, candidate_b)
        if reference not in {reference_a, reference_b}:
            continue
        decided += 1
        truth = row["A-coref"].strip().upper() == "TRUE"
        chose_a = reference == reference_a and reference_a is not None
        if chose_a == truth:
            correct += 1
    return {
        "rows": len(rows),
        "decided": decided,
        "coverage": round(decided / len(rows), 3) if rows else 0.0,
        "accuracy": round(correct / decided, 3) if decided else 0.0,
        "gap_convergence_promoted": len(gap_convergence.promoted),
    }


def _qa_metrics(system: Any, declarations: list[Declaration], use_pronoun: bool = False) -> dict[str, Any]:
    facts = _wikidata_facts()
    per_relation: dict[str, dict[str, int]] = defaultdict(lambda: {"positive": 0, "recall": 0, "negative": 0, "precision": 0})
    for entry in facts:
        qid, label = entry.get("qid", ""), entry.get("label", "")
        if not qid:
            continue
        subject = _pronoun_symbol(system, qid) if use_pronoun else _symbol(label, qid)
        if not subject:
            continue
        for fact in entry.get("facts", []):
            relation = fact.get("r")
            if relation not in QA_RELATIONS:
                continue
            answer = ask(system, relation, subject, fact.get("b"))
            per_relation[relation]["positive"] += 1
            if answer.truth_for(fact.get("b")) == "true":
                per_relation[relation]["recall"] += 1
            negatives = _negative_objects(facts, qid, relation)
            for negative in negatives:
                outcome = ask(system, relation, subject, negative).truth_for(negative)
                per_relation[relation]["negative"] += 1
                if outcome != "true":
                    per_relation[relation]["precision"] += 1
    totals = {"positive": 0, "recall": 0, "negative": 0, "precision": 0}
    report: dict[str, Any] = {}
    for relation, counts in sorted(per_relation.items()):
        report[relation] = {
            "positive": counts["positive"],
            "recall": round(counts["recall"] / counts["positive"], 3) if counts["positive"] else 0.0,
            "negative": counts["negative"],
            "precision": round(counts["precision"] / counts["negative"], 3) if counts["negative"] else 0.0,
        }
        for key in totals:
            totals[key] += counts[key]
    report["global"] = {
        "positive": totals["positive"],
        "recall": round(totals["recall"] / totals["positive"], 3) if totals["positive"] else 0.0,
        "negative": totals["negative"],
        "precision": round(totals["precision"] / totals["negative"], 3) if totals["negative"] else 0.0,
    }
    return report


def _negative_objects(facts: list[dict[str, Any]], qid: str, relation: str, limit: int = 1) -> list[str]:
    for entry in facts:
        if entry.get("qid") == qid:
            continue
        for fact in entry.get("facts", []):
            if fact.get("r") == relation and fact.get("b"):
                return [fact["b"]]
    return []


def _planted_declarations(contexts: list[ContextIndex], seed: int = 0) -> list[Declaration]:
    """Fifty false facts: a valid relation with another person's object."""

    rng = random.Random(seed + 7)
    people = _people()
    facts = _wikidata_facts()
    subjects: dict[str, str] = {}
    for qid, label in people.items():
        subjects[qid] = label
    chosen_contexts = [context.chunk.ctx_id for context in contexts]
    if not chosen_contexts:
        return []
    declarations: list[Declaration] = []
    for number in range(min(PLANTED_COUNT, len(chosen_contexts))):
        context = chosen_contexts[number % len(chosen_contexts)]
        qid = context
        other = next((q for q in subjects if q != qid), None)
        if other is None:
            break
        foreign = next(
            (
                fact
                for entry in facts
                if entry.get("qid") == other
                for fact in entry.get("facts", [])
                if fact.get("r") in QA_RELATIONS and fact.get("b")
            ),
            None,
        )
        if foreign is None:
            break
        label = subjects.get(qid, qid)
        declarations.append(
            Declaration(
                ctx_id=qid,
                relation=foreign["r"],
                a=_symbol(label, qid),
                b=f"{normalize(foreign['b']).replace(' ', '_')}@{qid}",
                a_sign=label,
                b_sign=foreign["b"],
                sentence_index=0,
                span=(0, 1),
                source="planted",
            )
        )
    return declarations


def _garbage_metrics(
    system: Any,
    convergence: Any,
    planted: list[Declaration],
    declarations: list[Declaration],
    only_converged: bool = False,
) -> dict[str, Any]:
    projected = {
        symbol
        for entry in convergence.proposed + convergence.promoted
        for symbol in (entry.get("source"), entry.get("target"))
    }
    planted_objects = {declaration.b for declaration in planted}
    isolated = sum(
        1
        for symbol in planted_objects
        if symbol not in convergence.referents
        and symbol not in projected
        and convergence.scores.get(symbol, 0.0) < 0.5
    )
    real_objects = {
        declaration.b
        for declaration in declarations
        if declaration.source != "planted"
        and (not only_converged or declaration.b in convergence.referents or declaration.a in convergence.referents)
    }
    sample = sorted(real_objects)[: len(planted_objects) or 1]
    real_isolated = sum(
        1
        for symbol in sample
        if symbol not in convergence.referents
        and symbol not in projected
        and convergence.scores.get(symbol, 0.0) < 0.5
    )
    return {
        "planted": len(planted_objects),
        "planted_isolated": isolated,
        "planted_isolated_fraction": round(isolated / len(planted_objects), 3) if planted_objects else 0.0,
        "real_sampled": len(sample),
        "real_isolated": real_isolated,
        "real_isolated_fraction": round(real_isolated / len(sample), 3) if sample else 0.0,
    }


def _promoted_pairs(convergence: Any) -> set[frozenset[str]]:
    pairs: set[frozenset[str]] = set()
    for entry in convergence.promoted:
        if entry.get("kind") in {"equivalent", "projection"}:
            pairs.add(frozenset((entry["source"], entry["target"])))
    return pairs


def _linked(system: Any, convergence: Any, first: str, second: str, pairs: set[frozenset[str]]) -> bool:
    reference_first = referent_of(system, first)
    reference_second = referent_of(system, second)
    if reference_first is not None and reference_first == reference_second:
        return True
    return frozenset((first, second)) in pairs


def _pair_phi(convergence: Any, first: str, second: str) -> float | None:
    for entry in convergence.promoted + convergence.proposed:
        if {entry.get("source"), entry.get("target")} == {first, second}:
            return float(entry.get("phi", 0.0))
    return None


def _intra_article_metrics(system: Any, convergence: Any, declarations: list[Declaration]) -> dict[str, Any]:
    """Fraction of article sections whose pronoun converges with the lead or the label."""

    people = _people()
    sections: dict[str, set[int]] = defaultdict(set)
    for declaration in declarations:
        sections[_article_of(declaration.ctx_id)].add(_section_of(declaration.ctx_id))
    pairs = _promoted_pairs(convergence)
    fractions: list[float] = []
    examples: list[dict[str, Any]] = []
    for stem, numbers in sorted(sections.items()):
        if len(numbers) < 3:
            continue
        anchor = _first_symbol(
            system,
            [f"{pronoun}@{stem}#0" for pronoun in ("she", "he")]
            + [f"{_symbol(people.get(stem, stem), stem)}#0"],
        )
        if anchor is None:
            examples.append({"article": stem, "reason": "no pronoun or label symbol in #0"})
            continue
        counted = 0
        converged = 0
        for number in sorted(numbers - {0}):
            pronoun = _first_symbol(
                system, [f"{name}@{stem}#{number}" for name in ("she", "he")]
            )
            if pronoun is None:
                continue
            counted += 1
            if _linked(system, convergence, pronoun, anchor, pairs):
                converged += 1
            elif len(examples) < 5:
                pronoun_configs = _symbol_configs(declarations, pronoun)
                anchor_configs = _symbol_configs(declarations, anchor)
                examples.append(
                    {
                        "article": stem,
                        "section": number,
                        "pronoun": pronoun,
                        "anchor": anchor,
                        "phi": _pair_phi(convergence, pronoun, anchor),
                        "pronoun_configs": len(pronoun_configs),
                        "anchor_configs": len(anchor_configs),
                        "shared_configs": len(pronoun_configs & anchor_configs),
                        "pronoun_examples": sorted(pronoun_configs)[:3],
                        "anchor_examples": sorted(anchor_configs)[:3],
                    }
                )
        if counted:
            fractions.append(converged / counted)
    return {
        "articles_evaluated": len(fractions),
        "mean_section_convergence": round(sum(fractions) / len(fractions), 3) if fractions else 0.0,
        "examples": examples[:5],
    }


def _false_merges(system: Any, convergence: Any) -> dict[str, Any]:
    """Promoted equivalences between symbols of articles that do not mention each other."""

    mentions = _mentions()
    examples: list[dict[str, Any]] = []
    for entry in convergence.promoted:
        if entry.get("kind") != "equivalent":
            continue
        stem_a = _article_of(entry["source"].split("@", 1)[-1])
        stem_b = _article_of(entry["target"].split("@", 1)[-1])
        if stem_a == stem_b:
            continue
        if stem_b in mentions.get(stem_a, []) or stem_a in mentions.get(stem_b, []):
            continue
        examples.append(
            {
                "source": entry["source"],
                "target": entry["target"],
                "phi": entry.get("phi"),
                "stem_a": stem_a,
                "stem_b": stem_b,
            }
        )
    return {"count": len(examples), "examples": examples[:5]}


def _qa_hop_metrics(system: Any, declarations: list[Declaration]) -> dict[str, Any]:
    """Recall asking from a section for facts declared in another section."""

    facts = _wikidata_facts()
    by_article: dict[str, list[Declaration]] = defaultdict(list)
    for declaration in declarations:
        by_article[_article_of(declaration.ctx_id)].append(declaration)
    per_relation: dict[str, dict[str, int]] = defaultdict(lambda: {"positive": 0, "recall": 0})
    for entry in facts:
        qid, label = entry.get("qid", ""), entry.get("label", "")
        candidates = by_article.get(qid, [])
        for fact in entry.get("facts", []):
            relation = fact.get("r")
            if relation not in QA_RELATIONS or not fact.get("b"):
                continue
            per_relation[relation]["positive"] += 1
            wanted = _tokens(fact["b"])
            declared = [
                declaration
                for declaration in candidates
                if declaration.relation == relation
                and wanted <= _tokens(declaration.b_sign)
                and _section_of(declaration.ctx_id) >= 1
            ]
            if not declared:
                continue
            source_section = _section_of(declared[0].ctx_id)
            asker = _first_symbol(
                system,
                [
                    f"{name}@{qid}#{number}"
                    for number in (0, 1, 2)
                    if number != source_section
                    for name in ("she", "he")
                ],
            )
            if asker is None:
                continue
            answer = ask(system, relation, asker, None)
            if any(wanted <= _tokens(sign) for _, _, signs, _ in answer.objects for sign in signs):
                per_relation[relation]["recall"] += 1
    totals = {"positive": 0, "recall": 0}
    report: dict[str, Any] = {}
    for relation, counts in sorted(per_relation.items()):
        report[relation] = {
            "positive": counts["positive"],
            "recall": round(counts["recall"] / counts["positive"], 3) if counts["positive"] else 0.0,
        }
        for key in totals:
            totals[key] += counts[key]
    report["global"] = {
        "positive": totals["positive"],
        "recall": round(totals["recall"] / totals["positive"], 3) if totals["positive"] else 0.0,
    }
    return report


def _ask_examples(system: Any, facts: list[dict[str, Any]], count: int = 10) -> list[dict[str, Any]]:
    """Returns asked questions, with Wikidata ones first and text facts after."""

    examples: list[dict[str, Any]] = []
    for entry in facts:
        if len(examples) >= count:
            break
        qid, label = entry.get("qid", ""), entry.get("label", "")
        for fact in entry.get("facts", []):
            if len(examples) >= count or fact.get("r") not in QA_RELATIONS:
                continue
            answer = ask(system, fact["r"], _symbol(label, qid), fact.get("b"))
            if answer.truth_for(fact.get("b")) != "true":
                continue
            examples.append(_example(f"was {label} {fact['r']} {fact['b']}?", answer))
    for world_id in sorted(system.wigames):
        if len(examples) >= count:
            break
        wigame = system.wigames[world_id]
        for fact in list(wigame.facts.values())[:1]:
            proposition = fact.proposition
            if fact.truth.value != "true":
                continue
            subject = proposition.subject_symbol_id
            signs = {sign for symbol in [subject] if symbol in system.symbols for sign in system.symbols[symbol].signs}
            if not signs or not any(sign[:1].isupper() or sign.lower() in {"she", "he"} for sign in signs):
                continue
            answer = ask(system, proposition.relation_id, proposition.subject_symbol_id, None)
            examples.append(
                _example(
                    f"what do we know about {proposition.subject_symbol_id}? ({proposition.relation_id})",
                    answer,
                )
            )
            break
    return examples[:count]


def _example(question: str, answer: Any) -> dict[str, Any]:
    return {
        "question": question,
        "path": answer.path,
        "objects": [object_symbol for object_symbol, _, _, _ in answer.objects],
        "prov": [prov for _, _, _, provenance in answer.objects[:1] for prov in provenance[:1]],
    }


def _render_report(
    metrics: dict[str, Any],
    system: Any,
    runtime: Any,
    convergence: Any,
    planted: list[Declaration],
    declarations: list[Declaration] | None = None,
) -> str:
    people = _people()
    examples = _ask_examples(system, _wikidata_facts(), count=10)
    groups: dict[str, set[str]] = defaultdict(set)
    for symbol, referent in convergence.referents.items():
        groups[referent].add(symbol)
    promoted = sorted(
        (entry for entry in convergence.promoted if entry["kind"] in {"equivalent", "projection"}),
        key=lambda entry: entry["source"],
    )[:10]
    fallback = sorted(
        (entry for entry in convergence.proposed if entry["kind"] == "equivalent"),
        key=lambda entry: entry["source"],
    )[:10]
    lines = [
        "# Physicists evaluation",
        "",
        "## Metrics",
        "",
        "```json",
        json.dumps(metrics, indent=2, ensure_ascii=False),
        "```",
        "",
        "## Ten routed answers",
        "",
    ]
    for example in examples:
        prov = example["prov"][0] if example["prov"] else {}
        lines.append(
            f"- {example['question']} → ruta {len(example['path'])} mundo(s); "
            f"objetos: {', '.join(sorted(set(example['objects']))[:4])}; "
            f"cita: {prov.get('document_id', '?')}:{prov.get('span', ['?', '?'])[0]}-{prov.get('span', ['?', '?'])[1]}"
        )
    lines.extend(["", "## Ten promoted convergences", ""])
    for entry in promoted:
        shared = 0
        if declarations is not None:
            shared = len(
                _symbol_configs(declarations, entry["source"]) & _symbol_configs(declarations, entry["target"])
            )
        lines.append(
            f"- {entry['source']} ~ {entry['target']} ({entry['kind']}, φ={entry['phi']:.4f}, "
            f"configuraciones compartidas={shared})"
        )
    if not promoted:
        lines.append(
            f"- (ninguna promovida; se listan {len(fallback)} propuestas equivalentes con sus φ)"
        )
        for entry in fallback:
            lines.append(f"- propuesta: {entry['source']} ~ {entry['target']} (φ={entry['phi']:.4f})")
    lines.extend(["", "## Five isolated symbols", ""])
    if convergence.isolated:
        for symbol in convergence.isolated[:5]:
            lines.append(f"- {symbol} (score={convergence.scores.get(symbol, 0.0):.3f})")
    else:
        lines.append("- (ninguno: todos los símbolos con soporte alcanzan φ >= 0.5)")
    pairs = metrics.get("pairs")
    if pairs:
        lines.extend(
            [
                "",
                "## Pairs: converged people",
                "",
                f"{pairs['people_converged']}/{pairs['people_evaluated']} ({pairs['fraction']}). "
                f"Desglose: {pairs['breakdown']}",
                "",
            ]
        )
        for example in pairs["examples"]:
            lines.append(
                f"- {example['source']} ~ {example['target']} ({example['kind']}, "
                f"φ={example['phi']}, referente={example['referent']})"
            )
        lines.extend(["", "## Pairs: failures", ""])
        for failure in pairs["failures"]:
            lines.append(
                f"- {failure['qid']}: {failure['source']} vs {failure['target']} — "
                f"configuraciones {failure['source_configs']}/{failure['target_configs']}, "
                f"compartidas {failure['shared_configs']} {failure['shared_examples']}, φ={failure['phi']}"
            )
        tautological = metrics.get("tautological_configurations") or []
        lines.extend(["", f"## Tautological configurations (top 20 of {len(tautological)})", ""])
        for entry in tautological[:20]:
            lines.append(f"- {entry['config']} (df={entry['df']}/{entry['contexts']})")
    merges = metrics.get("false_merges")
    if merges:
        lines.extend(["", "## False merges", ""])
        if merges["count"]:
            for example in merges["examples"]:
                lines.append(
                    f"- {example['source']} ~ {example['target']} (φ={example['phi']:.4f}, "
                    f"{example['stem_a']} y {example['stem_b']} no se mencionan)"
                )
        else:
            lines.append("- (ninguna)")
    lines.extend(
        [
            "",
            f"Plantillas plantadas: {len(planted)} hechos falsos en contextos propios.",
            f"Etiquetas conocidas: {len(people)}.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    """Runs the evaluation CLI."""

    parser = argparse.ArgumentParser(description="Evaluate routed queries on physicists.")
    parser.add_argument("--out", default="/tmp/eval/physicists")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--regime", choices=["document", "section", "pairs"], default=None)
    parser.add_argument("--with-sections", action="store_true", help="pairs regime: include EN sections")
    parser.add_argument("--decomposer", choices=["heuristic", "llm", "both"], default="heuristic")
    parser.add_argument("--max-memory-gb", type=float, default=4.0)
    parser.add_argument("--unit", choices=["document", "section"], default="document")
    parser.add_argument("--source", choices=["simple", "en"], default="simple")
    parser.add_argument("--llm", action="store_true")
    parser.add_argument("--taxonomy", action="store_true", help="also build the Context tree (slow)")
    args = parser.parse_args(argv)

    if args.max_memory_gb and args.max_memory_gb > 0:
        limit_bytes = int(args.max_memory_gb * 1024**3)
        try:
            resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, limit_bytes))
        except (ValueError, OSError):
            pass
    regime = args.regime or ("section" if args.unit == "section" else "document")
    evaluation = run_evaluation(
        args.out,
        limit=args.limit,
        llm=args.llm,
        taxonomy=args.taxonomy,
        unit=args.unit,
        source=args.source,
        regime=regime,
        with_sections=args.with_sections,
        decomposer=args.decomposer,
    )
    metrics = evaluation.metrics
    print(f"artículos evaluados: {metrics['world']['contexts']} (regime={regime}, decomposer={args.decomposer})")
    print(f"convergencia de pronombres: {metrics['pronoun_convergence']}")
    if "tautological_configurations" in metrics:
        print(f"tautological_configurations: {len(metrics['tautological_configurations'])}")
    for key in ("pairs", "intra_context", "ranking", "qa_pairs", "intra_article", "false_merges", "qa_hop", "garbage_converged"):
        if key in metrics:
            print(f"{key}: {metrics[key]}")
    print(f"GAP: {metrics['gap']}")
    print(f"QA global (etiqueta): {metrics['qa']['global']}")
    print(f"QA global (pronombre): {metrics['qa_pronoun_subject']['global']}")
    print(f"basura: {metrics['garbage']}")
    print(f"mundo: {metrics['world']}")
    print(f"tiempos: {metrics['timings']}")
    print(f"informe: {Path(args.out) / 'report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
