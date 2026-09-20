"""Build the `corpus/physicists/` dataset from Wikidata, Wikipedia and GAP.

The people query takes `wdt:P106/wdt:P279* wd:Q169470`, i.e. physicists and the
occupations that are subclasses of physicist (nuclear, theoretical, ...): the
exact `wdt:P106 wd:Q169470` filter yields 91 people of whom only 79 have a
Simple English article of 300+ characters.
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import re
import time
import unicodedata
import urllib.parse
import urllib.request

BASE = Path(__file__).resolve().parent
ARTICLES = BASE / "articles"
USER_AGENT = "matrix-shrdlu-spec/0.1 (https://github.com/jpcosec/Matrix; matrix-shrdlu@example.com)"
SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
WIKIPEDIA_API = "https://simple.wikipedia.org/w/api.php"
GAP_URL = (
    "https://raw.githubusercontent.com/google-research-datasets/gap-coreference"
    "/master/gap-validation.tsv"
)
GAP_FILENAME = "gap-validation.tsv"
GAP_IN_CORPUS = "gap_in_corpus.tsv"
MIN_ARTICLE_CHARS = 300
PAUSE_SECONDS = 0.2

ENTITY_PROPERTIES = (
    ("P19", "born_in"),
    ("P20", "died_in"),
    ("P27", "citizenship"),
    ("P101", "field"),
    ("P166", "award"),
    ("P69", "educated_at"),
    ("P108", "employer"),
    ("P184", "doctoral_advisor"),
    ("P185", "doctoral_student"),
    ("P26", "spouse"),
    ("P800", "notable_work"),
)
BIRTH_YEAR = ("P569", "birth_year")
RELATION_NAMES = tuple(name for _, name in ENTITY_PROPERTIES) + (BIRTH_YEAR[1],)

PEOPLE_QUERY = """
SELECT ?p ?pLabel ?art ?title WHERE {
  ?p wdt:P106/wdt:P279* wd:Q169470 ;
     wdt:P569 ?dob .
  FILTER(YEAR(?dob) >= 1850 && YEAR(?dob) <= 1900)
  ?art schema:about ?p ;
       schema:isPartOf <https://simple.wikipedia.org/> ;
       schema:name ?title .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
ORDER BY ?pLabel
"""


def main() -> int:
    """Downloads every source and writes the versioned corpus files."""

    BASE.mkdir(parents=True, exist_ok=True)
    ARTICLES.mkdir(parents=True, exist_ok=True)
    for stale in ARTICLES.glob("*.md"):
        stale.unlink()
    people = fetch_people()
    print(f"wikidata people: {len(people)}")
    included, excluded = fetch_articles(people)
    print(f"articles kept: {len(included)}  excluded: {len(excluded)}")
    facts = fetch_facts(included)
    print(f"facts: {sum(len(entry['facts']) for entry in facts.values())} over {len(facts)} people")
    mentions = build_mentions(included)
    print(f"cross mentions: {sum(len(targets) > 0 for targets in mentions.values())} articles")
    gap_rows = fetch_gap(included)
    print(f"gap rows in corpus: {gap_rows}")
    write_people(included)
    write_excluded(excluded)
    write_facts(facts)
    write_mentions(mentions)
    write_readme()
    return 0


def fetch_people() -> list[dict[str, str]]:
    """Returns the physicists born 1850-1900 with a Simple English article."""

    rows = _sparql_csv(PEOPLE_QUERY)
    people = []
    for row in rows:
        qid = _qid(row["p"])
        label = (row.get("pLabel") or row.get("title") or qid).strip()
        title = (row.get("title") or "").strip()
        if not qid or not title:
            continue
        people.append({"qid": qid, "label": label, "title": title})
    return _dedupe_people(people)


def fetch_articles(people: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Downloads one article extract per person and splits kept from excluded."""

    included: list[dict[str, str]] = []
    excluded: list[dict[str, str]] = []
    for person in people:
        page = _fetch_extract(person["title"])
        title = (page or {}).get("title") or person["title"]
        extract = ((page or {}).get("extract") or "").strip()
        if len(extract) < MIN_ARTICLE_CHARS:
            excluded.append({"qid": person["qid"], "title": title, "chars": str(len(extract))})
            continue
        (ARTICLES / f"{person['qid']}.md").write_text(f"# {title}\n\n{extract}\n", encoding="utf-8")
        included.append({"qid": person["qid"], "label": person["label"], "title": title})
    return included, excluded


def fetch_facts(people: list[dict[str, str]]) -> dict[str, dict]:
    """Returns the reference facts for every person, keyed by qid."""

    facts: dict[str, dict] = {
        person["qid"]: {"qid": person["qid"], "label": person["label"], "facts": []}
        for person in people
    }
    values = " ".join(f"wd:{person['qid']}" for person in people)
    relation_by_property = {property_id: relation for property_id, relation in ENTITY_PROPERTIES}
    property_values = " ".join(f"wdt:{property_id}" for property_id, _ in ENTITY_PROPERTIES)
    entity_query = (
        "SELECT ?p ?prop ?v ?vLabel WHERE { "
        f"VALUES ?p {{ {values} }} "
        f"VALUES ?prop {{ {property_values} }} "
        "?p ?prop ?v . "
        'SERVICE wikibase:label { bd:serviceParam wikibase:language "en". } }'
    )
    for row in _sparql_csv(entity_query):
        qid = _qid(row["p"])
        relation = relation_by_property.get(_qid(row.get("prop", "")))
        label = (row.get("vLabel") or "").strip()
        if qid in facts and relation and label:
            facts[qid]["facts"].append(
                {"r": relation, "b_qid": _qid(row["v"]), "b": label}
            )
    time.sleep(PAUSE_SECONDS)
    birth_query = (
        "SELECT ?p ?year WHERE { "
        f"VALUES ?p {{ {values} }} "
        "?p wdt:P569 ?dob . BIND(YEAR(?dob) AS ?year) }"
    )
    for row in _sparql_csv(birth_query):
        qid = _qid(row["p"])
        year = (row.get("year") or "").strip()
        if qid in facts and year:
            facts[qid]["facts"].append({"r": "birth_year", "b_qid": "", "b": year})
    for entry in facts.values():
        entry["facts"].sort(key=lambda fact: (fact["r"], fact["b"]))
    return facts


def build_mentions(people: list[dict[str, str]]) -> dict[str, list[str]]:
    """Returns, per article, the other physicists mentioned in its text."""

    texts = {
        person["qid"]: (ARTICLES / f"{person['qid']}.md").read_text(encoding="utf-8")
        for person in people
        if (ARTICLES / f"{person['qid']}.md").exists()
    }
    patterns = {person["qid"]: _mention_pattern(person["label"]) for person in people}
    mentions: dict[str, list[str]] = {}
    for qid, text in texts.items():
        found = [
            other["qid"]
            for other in people
            if other["qid"] != qid
            and other["qid"] in texts
            and patterns[other["qid"]]
            and patterns[other["qid"]].search(text)
        ]
        mentions[qid] = sorted(set(found))
    return mentions


def fetch_gap(people: list[dict[str, str]]) -> int:
    """Downloads the GAP validation set and keeps the rows about corpus pages."""

    payload = _request(GAP_URL).decode("utf-8")
    (BASE / GAP_FILENAME).write_text(payload, encoding="utf-8")
    titles = {_page_key(person["title"]) for person in people}
    reader = csv.DictReader(io.StringIO(payload), delimiter="\t")
    fieldnames = reader.fieldnames or []
    rows = [row for row in reader if _page_key(row.get("URL", "")) in titles]
    with (BASE / GAP_IN_CORPUS).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def write_people(people: list[dict[str, str]]) -> None:
    """Writes `people.csv` with the included physicists."""

    with (BASE / "people.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["qid", "label", "title"])
        writer.writeheader()
        for person in sorted(people, key=lambda person: person["qid"]):
            writer.writerow(person)


def write_excluded(excluded: list[dict[str, str]]) -> None:
    """Writes `excluded.csv` with the dropped articles."""

    with (BASE / "excluded.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["qid", "title", "chars"])
        writer.writeheader()
        for entry in sorted(excluded, key=lambda entry: entry["qid"]):
            writer.writerow(entry)


def write_facts(facts: dict[str, dict]) -> None:
    """Writes `facts.jsonl`, one JSON object per person."""

    with (BASE / "facts.jsonl").open("w", encoding="utf-8") as handle:
        for qid in sorted(facts):
            handle.write(json.dumps(facts[qid], ensure_ascii=False) + "\n")


def write_mentions(mentions: dict[str, list[str]]) -> None:
    """Writes `mentions.json`."""

    (BASE / "mentions.json").write_text(
        json.dumps(mentions, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_readme() -> None:
    """Writes the corpus README with sources, licenses and counts."""

    people = list(csv.DictReader((BASE / "people.csv").open(encoding="utf-8")))
    excluded = list(csv.DictReader((BASE / "excluded.csv").open(encoding="utf-8")))
    facts = [
        json.loads(line)
        for line in (BASE / "facts.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    mentions = json.loads((BASE / "mentions.json").read_text(encoding="utf-8"))
    gap_rows = list(csv.DictReader((BASE / GAP_FILENAME).open(encoding="utf-8"), delimiter="\t"))
    gap_in_corpus = list(
        csv.DictReader((BASE / GAP_IN_CORPUS).open(encoding="utf-8"), delimiter="\t")
    )
    total_facts = sum(len(entry["facts"]) for entry in facts)
    average = total_facts / len(people) if people else 0.0
    downloaded = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    text = f"""# Physicists corpus

One context per physicist (born 1850-1900) built from Simple English Wikipedia,
with reference facts from Wikidata and the GAP pronoun-resolution validation set.

The people query takes physicists and their subclasses
(`wdt:P106/wdt:P279* wd:Q169470`); the exact `wdt:P106 wd:Q169470` filter keeps
91 people, of whom only 79 have a Simple English article of 300+ characters.

## Contents

- `people.csv` — {len(people)} physicists (`qid,label,title`).
- `articles/<qid>.md` — Simple English Wikipedia extract, first line `# <title>`.
- `excluded.csv` — {len(excluded)} article(s) dropped for being shorter than {MIN_ARTICLE_CHARS} chars.
- `facts.jsonl` — reference facts, one line per person, {total_facts} facts total
  ({average:.1f} per person) over {len(RELATION_NAMES)} relations:
  {", ".join(RELATION_NAMES)}.
- `mentions.json` — cross mentions between corpus articles
  ({sum(len(targets) > 0 for targets in mentions.values())} articles mention at least one other).
- `{GAP_FILENAME}` — GAP validation set: {len(gap_rows)} rows, i.e. 908 labeled
  (pronoun, antecedent) pairs (each row carries the two candidates A and B).
- `{GAP_IN_CORPUS}` — {len(gap_in_corpus)} GAP row(s) whose URL points to a corpus page. GAP samples
  general-interest Wikipedia pages (TV series, politicians), so no physicist page appears.

## Sources and licenses

- Simple English Wikipedia articles: CC BY-SA 4.0
  (`https://simple.wikipedia.org/w/api.php`, `prop=extracts`).
- Wikidata facts: CC0 1.0 (`https://query.wikidata.org/sparql`).
- GAP coreference dataset: Apache 2.0
  (`https://github.com/google-research-datasets/gap-coreference`).

Downloaded on {downloaded} with `python -m corpus.physicists.build`.

## Rebuild

```bash
python -m corpus.physicists.build
```

The script uses only the standard library (`urllib`), waits {PAUSE_SECONDS} s between
Wikipedia calls, retries transient rate limits, and rewrites every file in this
directory deterministically.
"""
    (BASE / "README.md").write_text(text, encoding="utf-8")


def _sparql_csv(query: str) -> list[dict[str, str]]:
    url = SPARQL_ENDPOINT + "?" + urllib.parse.urlencode({"query": query})
    payload = _request(url, accept="text/csv").decode("utf-8")
    return list(csv.DictReader(io.StringIO(payload)))


def _fetch_extract(title: str) -> dict:
    """Fetches one article extract, following redirects and retrying empty answers."""

    params = {
        "action": "query",
        "prop": "extracts",
        "explaintext": "1",
        "exlimit": "1",
        "titles": title,
        "format": "json",
        "redirects": "1",
    }
    page: dict = {}
    for attempt in range(3):
        payload = json.loads(
            _request(WIKIPEDIA_API + "?" + urllib.parse.urlencode(params)).decode("utf-8")
        )
        query = payload.get("query", {})
        pages = query.get("pages", {})
        page = next(iter(pages.values()), {}) if pages else {}
        if not page.get("extract"):
            resolved = title
            for entry in query.get("normalized", []) + query.get("redirects", []):
                if entry.get("from") == resolved:
                    resolved = entry["to"]
            page = pages.get(resolved, page)
        if page.get("extract") or page.get("missing") is not None:
            break
        time.sleep(PAUSE_SECONDS)
    time.sleep(PAUSE_SECONDS)
    return page


def _request(url: str, accept: str = "*/*", attempts: int = 4) -> bytes:
    """Fetches a URL, retrying transient rate limits and server errors."""

    delay = 5.0
    for attempt in range(attempts):
        request = urllib.request.Request(url, headers={"Accept": accept, "User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return response.read()
        except urllib.error.HTTPError as error:
            if error.code not in {429, 500, 502, 503, 504} or attempt == attempts - 1:
                raise
            time.sleep(delay)
            delay *= 3
    raise RuntimeError(f"unreachable: {url}")


def _dedupe_people(people: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: dict[str, dict[str, str]] = {}
    for person in people:
        seen.setdefault(person["qid"], person)
    return [seen[qid] for qid in sorted(seen)]


def _qid(value: str) -> str:
    return (value or "").rstrip("/").rsplit("/", 1)[-1]


def _mention_pattern(label: str) -> re.Pattern[str] | None:
    parts = [part for part in re.split(r"\s+", label.strip()) if part]
    if not parts:
        return None
    surfaces = [label.strip()]
    surname = parts[-1]
    if len(surname) >= 4:
        surfaces.append(surname)
    bodies = "|".join(re.escape(surface) for surface in sorted(set(surfaces), key=len, reverse=True))
    return re.compile(rf"\b(?:{bodies})\b", re.IGNORECASE)


def _page_key(url: str) -> str:
    decoded = unicodedata.normalize("NFC", urllib.parse.unquote(url or ""))
    return decoded.rstrip("/").rsplit("/", 1)[-1].replace("_", " ").strip().lower()


if __name__ == "__main__":
    raise SystemExit(main())
