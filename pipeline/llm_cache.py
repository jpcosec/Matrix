"""Cached LLM decomposition: one JSONL line per chunk, keyed by its text."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import threading
from typing import Any, Callable

from populator.contexts import ContextIndex

from .decompose import Declaration, decompose_llm_chunk

DEFAULT_CACHE = Path(__file__).resolve().parents[1] / "corpus" / "physicists" / "declarations_llm.jsonl"

_LOCK = threading.Lock()


def cache_key(ctx: ContextIndex) -> str:
    """Returns the sha1 of the chunk text."""

    return hashlib.sha1(ctx.chunk.text.encode("utf-8")).hexdigest()


def read_cache(path: str | Path = DEFAULT_CACHE) -> dict[str, dict[str, Any]]:
    """Reads the JSONL cache into ``{key: entry}``."""

    cache: dict[str, dict[str, Any]] = {}
    cache_path = Path(path)
    if not cache_path.exists():
        return cache
    for line in cache_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(entry, dict) and entry.get("key"):
            cache[entry["key"]] = entry
    return cache


def declarations_from_entry(ctx: ContextIndex, entry: dict[str, Any]) -> list[Declaration]:
    """Rebuilds the declarations of one cache entry."""

    declarations: list[Declaration] = []
    for item in entry.get("declarations", []):
        if not isinstance(item, dict):
            continue
        span = item.get("span") or [0, 0]
        declarations.append(
            Declaration(
                ctx_id=ctx.chunk.ctx_id,
                relation=str(item.get("relation", "")),
                a=str(item.get("a", "")),
                b=str(item.get("b", "")),
                a_sign=str(item.get("a_sign", "")),
                b_sign=str(item.get("b_sign", "")),
                sentence_index=int(item.get("sentence_index", 0)),
                span=(int(span[0]), int(span[1])),
                source=str(item.get("source", "llm")),
            )
        )
    return declarations


def cached_decompose(
    ctx: ContextIndex,
    backend: Callable[[str], str] | None,
    path: str | Path = DEFAULT_CACHE,
    lang: str = "en",
) -> list[Declaration]:
    """Returns the chunk's LLM declarations, calling the backend only on a miss."""

    key = cache_key(ctx)
    entry = read_cache(path).get(key)
    if entry is not None:
        return declarations_from_entry(ctx, entry)
    if backend is None:
        return []
    declarations = decompose_llm_chunk(ctx, backend, lang=lang)
    append_cache(ctx, declarations, path=path, key=key)
    return declarations


def append_cache(
    ctx: ContextIndex,
    declarations: list[Declaration],
    path: str | Path = DEFAULT_CACHE,
    key: str | None = None,
) -> dict[str, Any]:
    """Appends one chunk entry to the JSONL cache and returns it."""

    entry = {
        "key": key or cache_key(ctx),
        "ctx_id": ctx.chunk.ctx_id,
        "declarations": [
            {
                "relation": declaration.relation,
                "a": declaration.a,
                "b": declaration.b,
                "a_sign": declaration.a_sign,
                "b_sign": declaration.b_sign,
                "sentence_index": declaration.sentence_index,
                "span": [declaration.span[0], declaration.span[1]],
                "source": declaration.source,
            }
            for declaration in declarations
        ],
    }
    cache_path = Path(path)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        with cache_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry
