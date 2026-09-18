"""AROMA-based projection candidates between two corpus worlds."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from populator import Corpus, build_corpus, read_documents
from sia.aroma import Hierarchy, aroma, hierarchy_from_levels
from sia.cohesion import cohesion_pair
from sia.contingency import contingency
from sia.hierarchy import build_hierarchy
from sia.intensity import phi_entropic

DEFAULT_PHI_R = 0.85
AUTO_PROMOTE_PHI = 0.99


def match_corpora(
    corpus_a: Corpus,
    corpus_b: Corpus,
    wigame_a: str,
    wigame_b: str,
    phi_r: float = DEFAULT_PHI_R,
    alpha: float = 2.0,
) -> list[str]:
    """Returns `candidate projection` S-expressions for matching hierarchy nodes."""

    h1 = corpus_hierarchy(corpus_a, alpha)
    h2 = corpus_hierarchy(corpus_b, alpha)
    sexprs: list[str] = []
    for match in aroma(h1, h2, phi_r=phi_r, alpha=alpha):
        terms_a = sorted(h1.terms[match.a])
        terms_b = sorted(h2.terms[match.b])
        class_match = len(terms_a) > 1 or len(terms_b) > 1
        pairs = [[source, target] for source in terms_a for target in terms_b]
        evidence: dict[str, Any] = {
            "tier": "statistical",
            "curation": "proposed",
            "stats": {"phi": float(match.phi), "class_match": class_match},
        }
        body = " ".join(f"({source} {target})" for source, target in pairs)
        payload = json.dumps(evidence, separators=(",", ":"))
        sexprs.append(
            f"(candidate projection wigame:{wigame_a} (wigame:{wigame_b} {body}) evidence:{payload})"
        )
    return sexprs


def corpus_hierarchy(corpus: Corpus, alpha: float = 2.0) -> Hierarchy:
    """Builds the implicative hierarchy of one corpus as AROMA nodes."""

    counts = contingency(corpus.X)
    cohesion = cohesion_pair(phi_entropic(counts, alpha))
    levels = build_hierarchy(cohesion)
    return hierarchy_from_levels(list(corpus.concepts), levels)


def match_directories(
    dir_a: str | Path,
    dir_b: str | Path,
    wigames: tuple[str, str],
    lang: str | None = "es",
    phi_r: float = DEFAULT_PHI_R,
) -> "tuple":
    """Builds both worlds on one system and returns the evaluated candidate results."""

    from pipeline.run import build_system
    from src.operational_model import LogicalSystem, SExpressionRuntime

    wigame_a, wigame_b = wigames
    documents_a = read_documents(dir_a)
    documents_b = read_documents(dir_b)
    corpus_a = build_corpus(documents_a, lang=lang)
    corpus_b = build_corpus(documents_b, lang=lang)
    system = LogicalSystem()
    build_system(dir_a, wigame_a, corpus=corpus_a, documents=documents_a, lang=lang, system=system)
    build_system(dir_b, wigame_b, corpus=corpus_b, documents=documents_b, lang=lang, system=system)
    runtime = SExpressionRuntime(system)
    sexprs = match_corpora(corpus_a, corpus_b, wigame_a, wigame_b, phi_r=phi_r)
    results = [runtime.evaluate(sexpr) for sexpr in sexprs]
    promoted = 0
    for result in results:
        candidate = system.candidates.get(result.payload["candidate_id"])
        if candidate is None:
            continue
        if candidate.evidence.get("stats", {}).get("phi", 0.0) >= AUTO_PROMOTE_PHI:
            runtime.evaluate(f"(promote {candidate.candidate_id})")
            promoted += 1
    return system, runtime, results, promoted


def main(argv: list[str] | None = None) -> int:
    """Runs the AROMA matching CLI over two corpora directories."""

    parser = argparse.ArgumentParser(description="Propose world projections between two corpora.")
    parser.add_argument("dir_a")
    parser.add_argument("dir_b")
    parser.add_argument("--wigames", nargs=2, default=["a", "b"], metavar=("A", "B"))
    parser.add_argument("--lang", choices=["es", "en"], default="es")
    parser.add_argument("--phi-r", type=float, default=DEFAULT_PHI_R)
    args = parser.parse_args(argv)

    system, runtime, results, promoted = match_directories(
        args.dir_a, args.dir_b, tuple(args.wigames), lang=args.lang, phi_r=args.phi_r
    )
    print(f"candidatos de proyección: {len(results)}")
    print(f"auto-promovidos (phi >= {AUTO_PROMOTE_PHI}): {promoted}")
    for result in results[:5]:
        candidate = system.candidates[result.payload["candidate_id"]]
        payload = candidate.payload
        print(f"- {candidate.candidate_id} source={payload['source_wigame']} target={payload['target_wigame']} "
              f"pairs={len(payload['pairs'])} phi={candidate.evidence.get('stats', {}).get('phi'):.3f}")
    print(json.dumps(runtime.evaluate(f"(return projections wigame:{args.wigames[0]})").payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
