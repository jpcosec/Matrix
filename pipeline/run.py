"""CLI driver that populates a logical system from a text corpus."""

from __future__ import annotations

import argparse
from pathlib import Path

from populator import build_corpus, read_documents

from .bridge import auto_confirm_candidates, corpus_to_sexprs


def build_system(
    corpus_dir: str | Path,
    wigame_id: str = "vegetales",
) -> "tuple":
    """Builds the logical system, runtime and evaluation results for a corpus."""

    from src.operational_model import LogicalSystem, OperationResult, SExpressionRuntime, deduce

    documents = read_documents(corpus_dir)
    corpus = build_corpus(documents)
    sexprs = corpus_to_sexprs(corpus, wigame_id, documents=documents)
    system = LogicalSystem()
    runtime = SExpressionRuntime(system)
    results: list[OperationResult] = []
    for sexpr in sexprs:
        result = runtime.evaluate(sexpr)
        results.append(result)
        if sexpr.startswith("(create") and result.status != "accept":
            raise RuntimeError(f"create failed: {sexpr} -> {result}")
    for candidate_id in auto_confirm_candidates(system):
        runtime.evaluate(f"(promote {candidate_id})")
    deduce(system, f"wigame:{wigame_id}")
    return system, runtime, results


def main(argv: list[str] | None = None) -> int:
    """Runs the corpus to WiGame pipeline from the command line."""

    parser = argparse.ArgumentParser(description="Populate a Matrix WiGame from a text corpus.")
    parser.add_argument("corpus_dir")
    parser.add_argument("--wigame", default="vegetales")
    parser.add_argument("--dump", default=None, help="write the resulting WiGame to YAML")
    args = parser.parse_args(argv)

    system, _, results = build_system(args.corpus_dir, args.wigame)
    wigame = system.wigames[f"wigame:{args.wigame}"]
    confirmed = sum(
        1 for candidate in system.candidates.values() if candidate.evidence.get("curation") == "confirmed"
    )
    print(f"wi-game: {wigame.wigame_id}")
    print(f"simbolos: {len(system.symbols)}")
    print(f"relaciones: {len(system.relations)}")
    print(f"s-expressions evaluadas: {len(results)}")
    print(f"candidatos: {len(system.candidates)}")
    print(f"auto-confirmados: {confirmed}")
    true_cells = sum(1 for row in wigame.Vi.values for cell in row if cell == "true")
    print(f"hechos en V_i: {true_cells}")
    if args.dump:
        Path(args.dump).write_text(wigame.to_yaml(), encoding="utf-8")
        print(f"dump: {args.dump}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
