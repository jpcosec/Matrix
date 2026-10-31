"""Fill the LLM decomposition cache for the pairs regime chunks."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from time import perf_counter
from typing import Any

from populator import build_contexts, read_documents

from .curate import FakeBackend, PiBackend
from .decompose import RELATION_FAMILIES, decompose_llm_chunk
from .llm_cache import DEFAULT_CACHE, append_cache, cache_key, read_cache

CORPUS = Path(__file__).resolve().parents[1] / "corpus" / "physicists"


def pairs_contexts(limit: int | None = None, with_sections: bool = False) -> list[Any]:
    """Simple English article plus the English lead (or all sections) of each person."""

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


def fill_cache(
    contexts: list[Any],
    backend: Any,
    path: str | Path = DEFAULT_CACHE,
    workers: int = 4,
) -> dict[str, Any]:
    """Runs one LLM call per uncached chunk, in parallel, and records the stats."""

    cache = read_cache(path)
    pending = [ctx for ctx in contexts if cache_key(ctx) not in cache]
    report: dict[str, Any] = {"chunks": len(contexts), "cached": len(contexts) - len(pending), "filled": 0,
                              "failed": [], "per_chunk": [], "seconds": 0.0}
    start = perf_counter()

    def work(ctx: Any) -> tuple[str, int, int, float, str | None]:
        chunk_start = perf_counter()
        try:
            declarations = decompose_llm_chunk(ctx, backend)
        except Exception as error:  # noqa: BLE001 - a broken chunk must not stop the batch
            return ctx.chunk.ctx_id, 0, 0, perf_counter() - chunk_start, str(error)
        append_cache(ctx, declarations, path=path)
        return ctx.chunk.ctx_id, len(declarations), 0, perf_counter() - chunk_start, None

    if pending:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(work, ctx): ctx for ctx in pending}
            for future in as_completed(futures):
                ctx_id, kept, dropped, seconds, error = future.result()
                if error is not None:
                    report["failed"].append({"ctx_id": ctx_id, "error": error})
                    continue
                report["filled"] += 1
                report["per_chunk"].append(
                    {"ctx_id": ctx_id, "declarations": kept, "seconds": round(seconds, 2)}
                )
    report["seconds"] = round(perf_counter() - start, 2)
    return report


def main(argv: list[str] | None = None) -> int:
    """Fills the cache for the pairs regime."""

    parser = argparse.ArgumentParser(description="Decompose corpus chunks with a small LLM.")
    parser.add_argument("corpus", nargs="?", default="corpus/physicists")
    parser.add_argument("--regime", default="pairs", choices=["pairs"])
    parser.add_argument("--backend", default="pi", choices=["pi", "fake"])
    parser.add_argument("--model", default="deepseek/deepseek-flash")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--with-sections", action="store_true")
    parser.add_argument("--out", default=str(DEFAULT_CACHE))
    args = parser.parse_args(argv)

    contexts = pairs_contexts(limit=args.limit, with_sections=args.with_sections)
    if args.backend == "pi":
        backend: Any = PiBackend(model=args.model, timeout=180, thinking="off")
    else:
        backend = FakeBackend("[]")
    report = fill_cache(contexts, backend, path=args.out, workers=args.workers)
    total_declarations = sum(item["declarations"] for item in report["per_chunk"])
    print(f"chunks: {report['chunks']}  cached: {report['cached']}  filled: {report['filled']}  "
          f"failed: {len(report['failed'])}")
    print(f"declaraciones LLM: {total_declarations}  tiempo: {report['seconds']}s "
          f"({report['seconds'] / max(report['filled'], 1):.2f}s por chunk)")
    for item in report["per_chunk"][:5]:
        print(f"- {item['ctx_id']}: {item['declarations']} declaraciones en {item['seconds']}s")
    for failure in report["failed"][:5]:
        print(f"- fallo {failure['ctx_id']}: {failure['error']}")
    print(f"relaciones permitidas: {len(RELATION_FAMILIES)} familias + rel:<verbo>")
    from .llm_cache import read_cache as _read

    print(f"caché: {len(_read(args.out))} chunks en {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
