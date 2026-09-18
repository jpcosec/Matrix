"""CLI driver that populates a logical system from a text corpus."""

from __future__ import annotations

import argparse
from pathlib import Path
import resource
from time import perf_counter

from populator import build_corpus, read_documents

from .bridge import auto_confirm_candidates, corpus_to_sexprs


def peak_memory_mb() -> float:
    """Returns the process peak resident set size in megabytes."""

    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def build_system(
    corpus_dir: str | Path | None = None,
    wigame_id: str = "vegetales",
    *,
    lang: str | None = None,
    max_concepts: int | None = None,
    max_n: int = 3,
    min_support: int = 5,
    recursive: bool = False,
    corpus=None,
    documents=None,
    max_fact_candidates: int | None = None,
    max_nonsense: int | None = None,
    max_class_candidates: int | None = None,
    hierarchy_max_concepts: int | None = 120,
    report: dict | None = None,
) -> "tuple":
    """Builds the logical system, runtime and evaluation results for a corpus.

    Pass a prebuilt ``corpus`` and its ``documents`` to skip reading and
    chunking (the experiment runner reuses them for provenance checks).
    """

    from src.operational_model import LogicalSystem, OperationResult, SExpressionRuntime, deduce

    overall_start = perf_counter()
    if corpus is None or documents is None:
        start = perf_counter()
        documents = read_documents(corpus_dir, recursive=recursive)
        corpus = build_corpus(
            documents,
            lang=lang,
            max_concepts=max_concepts,
            max_n=max_n,
            min_support=min_support,
        )
        populator_seconds = perf_counter() - start
    else:
        populator_seconds = 0.0

    start = perf_counter()
    sexprs = corpus_to_sexprs(
        corpus,
        wigame_id,
        documents=documents,
        max_fact_candidates=max_fact_candidates,
        max_nonsense=max_nonsense,
        max_class_candidates=max_class_candidates,
        hierarchy_max_concepts=hierarchy_max_concepts,
    )
    sia_seconds = perf_counter() - start

    system = LogicalSystem()
    runtime = SExpressionRuntime(system)
    results: list[OperationResult] = []
    start = perf_counter()
    for sexpr in sexprs:
        result = runtime.evaluate(sexpr)
        results.append(result)
        if sexpr.startswith("(create") and result.status != "accept":
            raise RuntimeError(f"create failed: {sexpr} -> {result}")
    auto = auto_confirm_candidates(system)
    for candidate_id in auto:
        runtime.evaluate(f"(promote {candidate_id})")
    runtime_seconds = perf_counter() - start

    start = perf_counter()
    derived = deduce(system, f"wigame:{wigame_id}")
    deduce_seconds = perf_counter() - start

    if report is not None:
        report.update(
            {
                "documents": len(documents),
                "sentences": len(corpus.individuals),
                "concepts": len(corpus.concepts),
                "sexprs": len(sexprs),
                "auto_confirmed": len(auto),
                "derived": len(derived),
                "populator_seconds": round(populator_seconds, 3),
                "sia_seconds": round(sia_seconds, 3),
                "runtime_seconds": round(runtime_seconds, 3),
                "deduce_seconds": round(deduce_seconds, 3),
                "total_seconds": round(perf_counter() - overall_start, 3),
                "peak_memory_mb": round(peak_memory_mb(), 1),
            }
        )
    return system, runtime, results


def main(argv: list[str] | None = None) -> int:
    """Runs the corpus to WiGame pipeline from the command line."""

    parser = argparse.ArgumentParser(description="Populate a Matrix WiGame from a text corpus.")
    parser.add_argument("corpus_dir")
    parser.add_argument("--wigame", default="vegetales")
    parser.add_argument("--lang", choices=["es", "en"], default=None)
    parser.add_argument("--max-concepts", type=int, default=None)
    parser.add_argument("--max-facts", type=int, default=None)
    parser.add_argument("--max-nonsense", type=int, default=None)
    parser.add_argument("--max-classes", type=int, default=None)
    parser.add_argument("--recursive", action="store_true")
    parser.add_argument("--dump", default=None, help="write the resulting WiGame to YAML")
    args = parser.parse_args(argv)

    report: dict = {}
    system, _, results = build_system(
        args.corpus_dir,
        args.wigame,
        lang=args.lang,
        max_concepts=args.max_concepts,
        max_fact_candidates=args.max_facts,
        max_nonsense=args.max_nonsense,
        max_class_candidates=args.max_classes,
        recursive=args.recursive,
        report=report,
    )
    wigame = system.wigames[f"wigame:{args.wigame}"]
    confirmed = sum(
        1 for candidate in system.candidates.values() if candidate.evidence.get("curation") == "confirmed"
    )
    print(f"wi-game: {wigame.wigame_id}")
    print(f"documentos: {report['documents']}  oraciones: {report['sentences']}  conceptos: {report['concepts']}")
    print(f"simbolos: {len(system.symbols)}")
    print(f"relaciones: {len(system.relations)}")
    print(f"s-expressions evaluadas: {len(results)}")
    print(f"candidatos: {len(system.candidates)}")
    print(f"auto-confirmados: {confirmed}")
    true_cells = sum(1 for row in wigame.Vi.values for cell in row if cell == "true")
    print(f"hechos en V_i: {true_cells}")
    print(
        "tiempos: populator {populator_seconds}s  sia {sia_seconds}s  runtime {runtime_seconds}s  deduce {deduce_seconds}s".format(
            **report
        )
    )
    print(f"memoria pico: {report['peak_memory_mb']} MB")
    if args.dump:
        Path(args.dump).write_text(wigame.to_yaml(), encoding="utf-8")
        print(f"dump: {args.dump}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
