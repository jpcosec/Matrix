"""Ingest per-context declarations into Matrix WiGames."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any

from populator import build_contexts, read_documents
from populator.contexts import ContextIndex

from .decompose import Declaration, decompose

RELATION_FLAGS = {
    "part_of": "transitive:true",
    "precedes": "transitive:true",
    "causes": "transitive:true",
    "spouse": "commutative:true",
}


@dataclass
class IngestReport:
    """What one ingestion pass created and what it refused."""

    contexts: int = 0
    symbols: int = 0
    wigames: int = 0
    asserted: int = 0
    rejected: list[tuple[str, str]] = field(default_factory=list)
    by_relation: Counter = field(default_factory=Counter)


def ingest_contexts(
    system: Any,
    runtime: Any,
    contexts: list[ContextIndex],
    declarations: list[Declaration],
) -> IngestReport:
    """Creates contexts, symbols, relations and one WiGame per (context, relation)."""

    report = IngestReport()
    documents = {context.chunk.ctx_id: context.chunk.document_id for context in contexts}
    signs = {
        sign.symbol_id: sign
        for context in contexts
        for sign in context.signs.values()
    }
    used_symbols = sorted({declaration.a for declaration in declarations} | {declaration.b for declaration in declarations})
    for context in contexts:
        runtime.evaluate(f"(create context {context.chunk.ctx_id})")
        report.contexts += 1
    for symbol_id in used_symbols:
        sign = signs.get(symbol_id)
        surface = sign.sign if sign is not None else symbol_id.split("@")[0]
        runtime.evaluate(f"(create symbol {symbol_id} {_surface(surface)})")
        report.symbols += 1
    for relation in sorted({declaration.relation for declaration in declarations}):
        flags = RELATION_FLAGS.get(relation, "")
        command = f"(create relation {relation} {relation} {flags})".replace(" )", ")")
        runtime.evaluate(command)

    worlds: dict[tuple[str, str], list[Declaration]] = {}
    for declaration in declarations:
        worlds.setdefault((declaration.ctx_id, declaration.relation), []).append(declaration)

    for (ctx_id, relation), items in sorted(worlds.items()):
        li_id = f"li:{ctx_id}:{relation}"
        wigame_id = f"wigame:{ctx_id}:{relation}"
        axis_a = " ".join(sorted({item.a for item in items}))
        axis_b = " ".join(sorted({item.b for item in items}))
        runtime.evaluate(f"(create li {li_id} {relation} (axis-a {axis_a}) (axis-b {axis_b}))")
        created = runtime.evaluate(f"(create wigame {wigame_id} {li_id} context:{ctx_id})")
        if created.status == "accept":
            report.wigames += 1
        for item in items:
            sexpr = f"({relation} {item.a} {item.b})"
            evidence = _evidence(item, documents.get(ctx_id, ""))
            result = runtime.evaluate(
                f"(assert {wigame_id} {sexpr} evidence:{json.dumps(evidence, separators=(',', ':'))})"
            )
            report.by_relation[relation] += 1
            if result.status == "accept":
                report.asserted += 1
            else:
                report.rejected.append((sexpr, result.reason or result.status))
    return report


def build_world(
    corpus_dir: str | Path,
    unit: str = "document",
    lang: str = "en",
    backend: Any = None,
    limit: int | None = None,
) -> tuple:
    """Builds a system whose WiGames are the (context, relation) language games."""

    from src.operational_model import LogicalSystem, SExpressionRuntime

    documents = read_documents(corpus_dir)
    contexts = build_contexts(documents, unit=unit, lang=lang)
    if limit is not None:
        contexts = contexts[:limit]
    declarations: list[Declaration] = []
    for context in contexts:
        declarations.extend(decompose(context, lang=lang, backend=backend))
    system = LogicalSystem()
    runtime = SExpressionRuntime(system)
    report = ingest_contexts(system, runtime, contexts, declarations)
    return system, runtime, contexts, declarations, report


def _evidence(declaration: Declaration, document_id: str) -> dict[str, Any]:
    return {
        "tier": "observed",
        "curation": "confirmed",
        "prov": [
            {
                "document_id": document_id,
                "span": [declaration.span[0], declaration.span[1]],
                "extractor": f"decompose/{declaration.source}",
                "confidence": 1.0,
            }
        ],
    }


def _surface(surface: str) -> str:
    return "_".join(surface.split()) or "sign"


def main(argv: list[str] | None = None) -> int:
    """Runs the ingestion CLI over a corpus directory."""

    parser = argparse.ArgumentParser(description="Ingest per-context declarations into WiGames.")
    parser.add_argument("corpus_dir")
    parser.add_argument("--lang", choices=["es", "en"], default="en")
    parser.add_argument("--unit", choices=["document", "section"], default="document")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args(argv)

    system, runtime, contexts, declarations, report = build_world(
        args.corpus_dir, unit=args.unit, lang=args.lang, limit=args.limit
    )
    print(f"contextos: {report.contexts}  simbolos: {report.symbols}  wigames: {report.wigames}")
    print(f"declaraciones: {len(declarations)}  afirmadas: {report.asserted}  rechazadas: {len(report.rejected)}")
    print("por relación: " + ", ".join(f"{relation}={count}" for relation, count in sorted(report.by_relation.items())))
    for sexpr, reason in report.rejected[:5]:
        print(f"- rechazada {sexpr}: {reason}")
    print(f"contextos registrados: {len(system.contexts)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
