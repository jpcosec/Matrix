# Physicists corpus

One context per physicist (born 1850-1900) built from Simple English Wikipedia,
with reference facts from Wikidata and the GAP pronoun-resolution validation set.

The people query takes physicists and their subclasses
(`wdt:P106/wdt:P279* wd:Q169470`); the exact `wdt:P106 wd:Q169470` filter keeps
91 people, of whom only 79 have a Simple English article of 300+ characters.

## Contents

- `people.csv` — 89 physicists (`qid,label,title`).
- `articles/<qid>.md` — Simple English Wikipedia extract, first line `# <title>`.
- `excluded.csv` — 14 article(s) dropped for being shorter than 300 chars.
- `facts.jsonl` — reference facts, one line per person, 2802 facts total
  (31.5 per person) over 12 relations:
  born_in, died_in, citizenship, field, award, educated_at, employer, doctoral_advisor, doctoral_student, spouse, notable_work, birth_year.
- `mentions.json` — cross mentions between corpus articles
  (60 articles mention at least one other).
- `gap-validation.tsv` — GAP validation set: 454 rows, i.e. 908 labeled
  (pronoun, antecedent) pairs (each row carries the two candidates A and B).
- `gap_in_corpus.tsv` — 0 GAP row(s) whose URL points to a corpus page. GAP samples
  general-interest Wikipedia pages (TV series, politicians), so no physicist page appears.

## Sources and licenses

- Simple English Wikipedia articles: CC BY-SA 4.0
  (`https://simple.wikipedia.org/w/api.php`, `prop=extracts`).
- Wikidata facts: CC0 1.0 (`https://query.wikidata.org/sparql`).
- GAP coreference dataset: Apache 2.0
  (`https://github.com/google-research-datasets/gap-coreference`).

Downloaded on 2026-09-20 with `python -m corpus.physicists.build`.

## Rebuild

```bash
python -m corpus.physicists.build
```

The script uses only the standard library (`urllib`), waits 0.2 s between
Wikipedia calls, retries transient rate limits, and rewrites every file in this
directory deterministically.
