"""CLI and helpers that build a Matrix world from a corpus of contexts."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from populator import read_documents

from .ingest import build_world


def build_system(
    corpus_dir: str | Path,
    wigame_id: str = "vegetales",
    *,
    unit: str = "document",
    lang: str | None = None,
    limit: int | None = None,
    batch_size: int = 40,
    backend: Any = None,
    report: dict | None = None,
) -> tuple:
    """Builds the world of one corpus: per-context WiGames plus convergence.

    Wraps :func:`pipeline.ingest.build_world`, which ingests one WiGame per
    ``(context, relation)`` and maintains them in batches
    (:func:`pipeline.convergence.converge_in_batches`). Returns the system, its
    runtime and the ingestion report; the convergence report is left on
    ``system.convergence_report``.
    """

    lang = lang or guess_lang(corpus_dir)
    system, runtime, contexts, declarations, ingest_report = build_world(
        corpus_dir,
        unit=unit,
        lang=lang,
        backend=backend,
        limit=limit,
        batch_size=batch_size,
    )
    if report is not None:
        convergence = system.convergence_report
        report.update(
            {
                "contexts": ingest_report.contexts,
                "symbols": len(system.symbols),
                "wigames": len(system.wigames),
                "facts": sum(len(wigame.facts) for wigame in system.wigames.values()),
                "candidates_by_kind": dict(ingest_report.by_relation),
                "promoted": len(convergence.promoted),
                "proposed": len(convergence.proposed),
                "referents": len(set(convergence.referents.values())),
                "variables": len(convergence.scores),
                "candidate_pairs": convergence.candidates_count,
                "batches": convergence.batches,
            }
        )
    return system, runtime, ingest_report


def guess_lang(corpus_dir: str | Path) -> str:
    """Guesses the stopword list of a corpus from its path."""

    return "es" if "vegetales" in str(corpus_dir).lower() else "en"


def dump_world(system: Any, directory: str | Path) -> int:
    """Writes one YAML file per WiGame."""

    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    written = 0
    for wigame_id, wigame in sorted(system.wigames.items()):
        name = wigame_id.replace(":", "_").replace("/", "_") + ".yaml"
        (root / name).write_text(wigame.to_yaml(), encoding="utf-8")
        written += 1
    return written


def main(argv: list[str] | None = None) -> int:
    """Runs the corpus to world CLI."""

    parser = argparse.ArgumentParser(description="Populate a Matrix world from a text corpus.")
    parser.add_argument("corpus_dir")
    parser.add_argument("--wigame", default=None, help="only keep this world (and its context)")
    parser.add_argument("--unit", choices=["document", "section"], default="document")
    parser.add_argument("--lang", choices=["es", "en"], default="en")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=40)
    parser.add_argument("--dump", default=None, help="write every WiGame to this directory")
    args = parser.parse_args(argv)

    report: dict = {}
    system, _, ingest_report = build_system(
        args.corpus_dir,
        args.wigame or "world",
        unit=args.unit,
        lang=args.lang,
        limit=args.limit,
        batch_size=args.batch_size,
        report=report,
    )
    print(
        f"documentos: {len(read_documents(args.corpus_dir))}  contextos: {report['contexts']}  "
        f"simbolos: {report['symbols']}  wigames: {report['wigames']}  hechos: {report['facts']}"
    )
    print(
        f"variables: {report['variables']}  pares candidatos: {report['candidate_pairs']}  "
        f"promovidos: {report['promoted']}  propuestos: {report['proposed']}  "
        f"referentes: {report['referents']}  lotes: {report['batches']}"
    )
    print("por relación: " + ", ".join(f"{k}={v}" for k, v in sorted(report["candidates_by_kind"].items())))
    if ingest_report.rejected:
        print(f"rechazadas: {len(ingest_report.rejected)} (primeras 3: {ingest_report.rejected[:3]})")
    if args.dump:
        print(f"dump: {dump_world(system, args.dump)} wi-games en {args.dump}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
