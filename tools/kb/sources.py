"""Deterministic source acquisition, chunking, and worker-prompt generation."""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from .store import KB, REPO_ROOT, now, sha256_text, slugify, write_json


def rel(path: Path) -> str:
    """Returns a repo-relative path string for provenance and prompts."""

    try:
        return str(Path(path).relative_to(REPO_ROOT))
    except ValueError:
        return str(path)

USER_AGENT = "matrix-kb-fanout/0.1 (local research harness)"


def fetch_wikipedia(title: str, lang: str = "en", intro_only: bool = False) -> dict[str, Any]:
    """Fetches plaintext, revision id, and canonical URL for one article."""

    query = {
        "action": "query",
        "prop": "extracts|revisions",
        "explaintext": 1,
        "rvprop": "ids|timestamp",
        "format": "json",
        "formatversion": 2,
        "redirects": 1,
        "titles": title,
    }
    if intro_only:
        query["exintro"] = 1
    url = f"https://{lang}.wikipedia.org/w/api.php?" + urllib.parse.urlencode(query)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    pages = payload.get("query", {}).get("pages", [])
    if not pages or "missing" in pages[0]:
        raise ValueError(f"wikipedia page not found: {title!r} ({lang})")
    page = pages[0]
    text = re.sub(r"\n{3,}", "\n\n", (page.get("extract") or "").strip())
    if not text:
        raise ValueError(f"wikipedia page has no plaintext extract: {title!r}")
    revision = (page.get("revisions") or [{}])[0]
    canonical = page.get("title", title)
    return {
        "slug": slugify(canonical),
        "title": canonical,
        "lang": lang,
        "url": f"https://{lang}.wikipedia.org/wiki/{urllib.parse.quote(canonical.replace(' ', '_'))}",
        "revid": revision.get("revid"),
        "rev_timestamp": revision.get("timestamp"),
        "license": "CC BY-SA 4.0",
        "fetched_at": now(),
        "chars": len(text),
        "sha256": sha256_text(text),
        "text": text,
    }


def write_source(kb: KB, payload: dict[str, Any]) -> dict[str, Any]:
    """Persists a fetched source as metadata JSON plus plaintext."""

    kb.ensure()
    slug = payload["slug"]
    text = payload.pop("text")
    (kb.sources_dir / f"{slug}.txt").write_text(text + "\n", encoding="utf-8")
    write_json(kb.sources_dir / f"{slug}.json", payload)
    return payload


_SENTENCE = re.compile(r"(?<=[.!?])\s+")


def chunk_text(text: str, max_chars: int = 1500) -> list[str]:
    """Splits text into paragraph/sentence chunks bounded by max_chars."""

    if max_chars < 200:
        raise ValueError("max_chars must be >= 200")
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    buffer = ""
    for paragraph in paragraphs:
        units = [paragraph] if len(paragraph) <= max_chars else _split_long(paragraph, max_chars)
        for unit in units:
            candidate = f"{buffer}\n\n{unit}".strip() if buffer else unit
            if len(candidate) <= max_chars:
                buffer = candidate
            else:
                if buffer:
                    chunks.append(buffer)
                buffer = unit
    if buffer:
        chunks.append(buffer)
    return chunks


def _split_long(paragraph: str, max_chars: int) -> list[str]:
    sentences = _SENTENCE.split(paragraph)
    units: list[str] = []
    buffer = ""
    for sentence in sentences:
        candidate = f"{buffer} {sentence}".strip() if buffer else sentence
        if len(candidate) <= max_chars:
            buffer = candidate
        else:
            if buffer:
                units.append(buffer)
            buffer = sentence
            while len(buffer) > max_chars:
                units.append(buffer[:max_chars])
                buffer = buffer[max_chars:]
    if buffer:
        units.append(buffer)
    return [u for u in units if u.strip()]


def build_work(kb: KB, slug: str, max_chars: int = 1500) -> list[dict[str, Any]]:
    """Writes chunk files and returns the work index for one source."""

    kb.ensure()
    text = kb.source_text(slug)
    work_source = kb.work_dir / slug
    work_source.mkdir(parents=True, exist_ok=True)
    entries: list[dict[str, Any]] = []
    for index, chunk in enumerate(chunk_text(text, max_chars=max_chars)):
        chunk_id = f"{slug}/{index:03d}"
        chunk_path = work_source / f"{index:03d}.txt"
        chunk_path.write_text(chunk + "\n", encoding="utf-8")
        entries.append(
            {
                "chunk_id": chunk_id,
                "index": index,
                "source": slug,
                "chars": len(chunk),
                "chunk_path": rel(chunk_path),
                "sha256": sha256_text(chunk),
                "output_path": rel(kb.candidates_dir / slug / f"{index:03d}.jsonl"),
            }
        )
    write_json(work_source / "index.json", {"source": slug, "max_chars": max_chars, "chunks": entries})
    return entries


def build_prompts(kb: KB, slug: str, relations: dict[str, dict[str, Any]]) -> list[Path]:
    """Writes one self-contained worker prompt per chunk."""

    index = json.loads((kb.work_dir / slug / "index.json").read_text(encoding="utf-8"))
    meta = kb.source_meta(slug)
    vocabulary = "\n".join(
        f"- `{rel}` — {spec.get('name', rel)}" for rel, spec in sorted(relations.items())
    )
    written: list[Path] = []
    for chunk in index["chunks"]:
        chunk_text_value = (REPO_ROOT / chunk["chunk_path"]).read_text(encoding="utf-8").strip()
        prompt = _prompt(meta, chunk, vocabulary, chunk_text_value)
        path = kb.work_dir / slug / f"{chunk['index']:03d}.prompt.md"
        path.write_text(prompt, encoding="utf-8")
        chunk["prompt_path"] = rel(path)
        written.append(path)
    write_json(kb.work_dir / slug / "index.json", index)
    return written


def _prompt(meta: dict[str, Any], chunk: dict[str, Any], vocabulary: str, text: str) -> str:
    out = chunk["output_path"]
    return f"""# KB extraction worker — {chunk['chunk_id']}

You extract factual propositions from one text chunk into JSONL.

## Source provenance (copy into every row)
- source: `{meta['slug']}`
- url: {meta['url']}
- revid: {meta['revid']}
- chunk_id: `{chunk['chunk_id']}`
- sha256: `{chunk['sha256']}`

## Allowed relations (use the exact id)
{vocabulary}

## Output contract
Write **only** valid JSONL, one object per line, to:
`{out}`

Each line MUST have exactly these keys:
```json
{{"relation":"es","subject":"dog","object":"mammal","truth":true,"sentence":"The dog is a mammal.","source":"{meta['slug']}","chunk_id":"{chunk['chunk_id']}","revid":{meta['revid']},"confidence":0.9}}
```

Hard rules:
1. `sentence` MUST be copied verbatim from the chunk (substring match).
2. `subject` and `object` MUST appear literally (case-insensitive) inside `sentence`.
3. `relation` MUST be one of the allowed ids.
4. `truth` MUST be a boolean; `confidence` a number in [0,1].
5. One proposition per line. No prose, no markdown fences, no comments.
6. Skip uncertain, metaphorical, quoted, or list-only content.
7. Emit at most 12 rows. Prefer precision over recall.
8. If nothing is extractable, write an empty file.

## Chunk text
```
{text}
```
"""


def prepare(kb: KB, slug: str, max_chars: int, relations: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Chunks one source and writes prompts; returns a dispatch summary."""

    chunks = build_work(kb, slug, max_chars=max_chars)
    prompts = build_prompts(kb, slug, relations)
    summary = {
        "source": slug,
        "chunks": len(chunks),
        "prompts": len(prompts),
        "dispatch": [
            {
                "chunk_id": chunk["chunk_id"],
                "prompt": chunk.get("prompt_path", rel(kb.work_dir / slug / f"{chunk['index']:03d}.prompt.md")),
                "output": chunk["output_path"],
            }
            for chunk in chunks
        ],
    }
    return summary
