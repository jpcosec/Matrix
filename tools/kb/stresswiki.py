"""Real-corpus stress generator: Wikipedia categories as contexts.

Deterministic, no LLM:

- fetch a Wikipedia category's members (paginated), then each article's
  categories and outgoing links;
- contexts are **categories** (a domain/language game);
- referents are **articles**; the referent's true profile is its own category set;
- inside context C, each member M asserts its other shared categories, so the
  same referent appears in many contexts and accumulates constraints.

This is the real analogue of the synthetic generator: same measurements, real
topology (shared categories, real surnames as homonym surfaces).
"""

from __future__ import annotations

import json
import random
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from .store import KB, dump_yaml, load_yaml, slugify, write_jsonl

USER_AGENT = "matrix-kb-stress/0.1 (local research harness; contact: local-user)"
RETRY_DELAYS = (1.0, 3.0, 8.0, 20.0)
PACE_S = 0.4


def _api(lang: str, params: dict[str, Any]) -> dict[str, Any]:
    params = {"format": "json", "formatversion": 2, **params}
    url = f"https://{lang}.wikipedia.org/w/api.php?" + urllib.parse.urlencode(params)
    last_error: Exception | None = None
    for delay in (0.0,) + RETRY_DELAYS:
        if delay:
            time.sleep(delay)
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=60) as response:
                payload = json.load(response)
            time.sleep(PACE_S)
            return payload
        except urllib.error.HTTPError as error:
            last_error = error
            if error.code not in (429, 500, 502, 503, 504):
                raise
        except Exception as error:  # transient network failure
            last_error = error
    raise RuntimeError(f"wikipedia api failed after retries: {last_error}")


def fetch_category_members(category: str, lang: str, limit: int) -> list[str]:
    """Returns article titles in a category, paginated."""

    titles: list[str] = []
    continuation: dict[str, Any] = {}
    while len(titles) < limit:
        payload = _api(
            lang,
            {
                "action": "query",
                "list": "categorymembers",
                "cmtitle": category if category.startswith("Category:") else f"Category:{category}",
                "cmtype": "page",
                "cmlimit": 500,
                **continuation,
            },
        )
        for item in payload.get("query", {}).get("categorymembers", []):
            if item.get("ns") == 0:
                titles.append(item["title"])
                if len(titles) >= limit:
                    break
        continuation = payload.get("continue", {})
        if not continuation:
            break
    return titles


def fetch_page_data(titles: list[str], lang: str) -> dict[str, dict[str, list[str]]]:
    """Returns {title: {"categories": [...], "links": [...]}} in batches of 50."""

    data: dict[str, dict[str, list[str]]] = {}
    for start in range(0, len(titles), 50):
        batch = titles[start : start + 50]
        categories: dict[str, list[str]] = {title: [] for title in batch}
        links: dict[str, list[str]] = {title: [] for title in batch}
        for prop, store, extra in (
            ("categories", categories, {"clshow": "!hidden"}),
            ("links", links, {"plnamespace": 0}),
        ):
            continuation: dict[str, Any] = {}
            while True:
                payload = _api(
                    lang,
                    {
                        "action": "query",
                        "prop": prop,
                        "titles": "|".join(batch),
                        "redirects": 1,
                        f"{prop[0]}limit": "max",
                        **extra,
                        **continuation,
                    },
                )
                for page in payload.get("query", {}).get("pages", []):
                    title = page.get("title")
                    if title not in store or "missing" in page:
                        continue
                    key = "category" if prop == "categories" else "title"
                    for item in page.get(prop, []):
                        value = item.get(key, "")
                        if value and value not in store[title]:
                            store[title].append(value)
                continuation = payload.get("continue", {})
                if not continuation:
                    break
        for title in batch:
            data[title] = {
                "categories": sorted(categories.get(title, [])),
                "links": sorted(links.get(title, [])),
            }
    return data


def generate_wikipedia(
    kb: KB,
    *,
    category: str,
    lang: str = "en",
    limit: int = 300,
    max_contexts: int = 200,
    attrs_per_member: int = 6,
    min_members: int = 2,
    seed: int = 7,
) -> dict[str, Any]:
    """Materializes real category contexts + ground truth into a KB directory."""

    kb.ensure()
    cache_path = kb.root / "raw_wiki.json"
    if cache_path.exists():
        cached = json.loads(cache_path.read_text(encoding="utf-8"))
        titles = cached["titles"]
        data = cached["data"]
    else:
        titles = fetch_category_members(category, lang, limit)
        data = fetch_page_data(titles, lang)
        cache_path.write_text(json.dumps({"titles": titles, "data": data}), encoding="utf-8")

    # referent profile = its own categories (normalized), bounded deterministically
    profiles: dict[str, list[str]] = {}
    for title, payload in data.items():
        categories = [slugify(item.replace("Category:", "")) for item in payload["categories"]]
        profiles[slugify(title)] = sorted(dict.fromkeys([c for c in categories if c]))[: attrs_per_member * 3]

    # contexts = categories with enough members inside the universe
    members_by_category: dict[str, list[str]] = {}
    for title, profile in profiles.items():
        for cat in profile:
            members_by_category.setdefault(cat, []).append(title)
    contexts = sorted(
        [cat for cat, members in members_by_category.items() if len(members) >= min_members],
        key=lambda cat: (-len(members_by_category[cat]), cat),
    )[:max_contexts]

    dump_yaml(
        kb.root / "wiki_source.yaml",
        {
            "category": category,
            "lang": lang,
            "articles": len(titles),
            "contexts": len(contexts),
            "referents": len(profiles),
        },
    )

    occurrences: list[dict[str, Any]] = []
    total_rows = 0
    for context in contexts:
        members = members_by_category[context]
        sentences: list[str] = []
        rows: list[dict[str, Any]] = []
        for member in members:
            asserted = [cat for cat in profiles[member] if cat != context][:attrs_per_member]
            for attr in asserted:
                sentence = f"{member} is {attr}."
                sentences.append(sentence)
                rows.append(
                    {
                        "relation": "es",
                        "subject": member,
                        "object": attr,
                        "truth": True,
                        "sentence": sentence,
                        "source": context,
                        "chunk_id": f"{context}/000",
                        "revid": 1,
                        "confidence": 0.9,
                    }
                )
            occurrences.append(
                {"context": context, "surface": member.rsplit("_", 1)[-1], "referent": member, "asserted": asserted}
            )
        (kb.work_dir / context).mkdir(parents=True, exist_ok=True)
        (kb.work_dir / context / "000.txt").write_text("\n".join(sentences) + "\n", encoding="utf-8")
        write_jsonl(kb.candidates_dir / context / "000.jsonl", rows)
        total_rows += len(rows)

    dump_yaml(
        kb.root / "stress_truth.yaml",
        {
            "referents": {ref: {"surface": ref.rsplit("_", 1)[-1], "profile": profile} for ref, profile in profiles.items()},
            "occurrences": occurrences,
            "source": {"kind": "wikipedia-category", "category": category, "lang": lang},
        },
    )
    return {
        "articles": len(titles),
        "contexts": len(contexts),
        "referents": len(profiles),
        "rows": total_rows,
        "category": category,
        "lang": lang,
    }


def load_truth(kb: KB) -> dict[str, Any]:
    return load_yaml(kb.root / "stress_truth.yaml")


DBPEDIA_ENDPOINT = "https://dbpedia.org/sparql"


def _sparql(query: str, endpoint: str = DBPEDIA_ENDPOINT) -> list[dict[str, Any]]:
    """Runs one SPARQL query with retries; returns result bindings."""

    url = endpoint + "?" + urllib.parse.urlencode({"query": query, "format": "application/sparql-results+json"})
    last_error: Exception | None = None
    for delay in (0.0,) + RETRY_DELAYS:
        if delay:
            time.sleep(delay)
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/sparql-results+json"})
            with urllib.request.urlopen(request, timeout=120) as response:
                payload = json.load(response)
            return payload["results"]["bindings"]
        except urllib.error.HTTPError as error:
            last_error = error
            if error.code not in (429, 500, 502, 503, 504):
                raise
        except Exception as error:
            last_error = error
    raise RuntimeError(f"sparql query failed after retries: {last_error}")


def fetch_dbpedia_profiles(category: str, limit: int, endpoint: str) -> dict[str, list[str]]:
    """Returns {person_slug: [category_slug, ...]} from one DBpedia query."""

    seed = "http://dbpedia.org/resource/Category:" + urllib.parse.quote(category.replace(" ", "_"))
    seed_slug = slugify(category)
    query = f"""
SELECT ?person ?category WHERE {{
  {{ SELECT DISTINCT ?person WHERE {{ ?person dct:subject <{seed}> }} ORDER BY ?person LIMIT {int(limit)} }}
  ?person dct:subject ?category .
}}"""
    profiles: dict[str, list[str]] = {}
    for binding in _sparql(query, endpoint):
        person = slugify(binding["person"]["value"].rsplit("/", 1)[-1])
        category_slug = slugify(binding["category"]["value"].rsplit("/", 1)[-1].replace("Category:", ""))
        if not person or not category_slug or category_slug == seed_slug:
            continue
        bucket = profiles.setdefault(person, [])
        if category_slug not in bucket:
            bucket.append(category_slug)
    return {person: sorted(categories) for person, categories in profiles.items()}


def _emit(
    kb: KB,
    profiles: dict[str, list[str]],
    *,
    max_contexts: int,
    attrs_per_member: int,
    min_members: int,
    seed: int = 7,
) -> dict[str, Any]:
    """Writes chunks/candidates/truth from referent profiles (shared by sources)."""

    rng = random.Random(seed)
    members_by_category: dict[str, list[str]] = {}
    for person, profile in profiles.items():
        for category in profile:
            members_by_category.setdefault(category, []).append(person)
    contexts = sorted(
        [cat for cat, members in members_by_category.items() if len(members) >= min_members],
        key=lambda cat: (-len(members_by_category[cat]), cat),
    )[:max_contexts]

    occurrences: list[dict[str, Any]] = []
    total_rows = 0
    for context in contexts:
        sentences: list[str] = []
        rows: list[dict[str, Any]] = []
        for member in members_by_category[context]:
            options = [cat for cat in profiles[member] if cat != context]
            asserted = sorted(rng.sample(options, min(attrs_per_member, len(options)))) if options else []
            for attr in asserted:
                sentence = f"{member} is {attr}."
                sentences.append(sentence)
                rows.append(
                    {
                        "relation": "es",
                        "subject": member,
                        "object": attr,
                        "truth": True,
                        "sentence": sentence,
                        "source": context,
                        "chunk_id": f"{context}/000",
                        "revid": 1,
                        "confidence": 0.9,
                    }
                )
            occurrences.append(
                {"context": context, "surface": member.rsplit("_", 1)[-1], "referent": member, "asserted": asserted}
            )
        (kb.work_dir / context).mkdir(parents=True, exist_ok=True)
        (kb.work_dir / context / "000.txt").write_text("\n".join(sentences) + "\n", encoding="utf-8")
        write_jsonl(kb.candidates_dir / context / "000.jsonl", rows)
        total_rows += len(rows)

    dump_yaml(
        kb.root / "stress_truth.yaml",
        {
            "referents": {
                ref: {"surface": ref.rsplit("_", 1)[-1], "profile": profile} for ref, profile in profiles.items()
            },
            "occurrences": occurrences,
        },
    )
    return {
        "contexts": len(contexts),
        "referents": len(profiles),
        "rows": total_rows,
        "members_per_context_mean": round(sum(len(members_by_category[c]) for c in contexts) / len(contexts), 2)
        if contexts
        else 0,
    }


def generate_dbpedia(
    kb: KB,
    *,
    category: str,
    limit: int = 400,
    max_contexts: int = 200,
    attrs_per_member: int = 5,
    min_members: int = 2,
    seed: int = 7,
    endpoint: str = DBPEDIA_ENDPOINT,
) -> dict[str, Any]:
    """Real-corpus generator using DBpedia: one SPARQL query, cached."""

    kb.ensure()
    cache_path = kb.root / "raw_dbpedia.json"
    if cache_path.exists():
        profiles = json.loads(cache_path.read_text(encoding="utf-8"))["profiles"]
    else:
        profiles = fetch_dbpedia_profiles(category, limit, endpoint)
        cache_path.write_text(json.dumps({"profiles": profiles}), encoding="utf-8")

    emitted = _emit(
        kb,
        profiles,
        max_contexts=max_contexts,
        attrs_per_member=attrs_per_member,
        min_members=min_members,
        seed=seed,
    )
    source = {"kind": "dbpedia-category", "category": category, "referents": len(profiles)}
    dump_yaml(kb.root / "wiki_source.yaml", source)
    truth = load_yaml(kb.root / "stress_truth.yaml")
    truth["source"] = source
    dump_yaml(kb.root / "stress_truth.yaml", truth)
    return {**emitted, **source}
