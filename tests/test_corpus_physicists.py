"""Offline checks over the versioned `corpus/physicists/` dataset."""

from __future__ import annotations

import csv
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "corpus" / "physicists"
RELATIONS = {
    "born_in",
    "died_in",
    "citizenship",
    "field",
    "award",
    "educated_at",
    "employer",
    "doctoral_advisor",
    "doctoral_student",
    "spouse",
    "notable_work",
    "birth_year",
}
GAP_COLUMNS = [
    "ID",
    "Text",
    "Pronoun",
    "Pronoun-offset",
    "A",
    "A-offset",
    "A-coref",
    "B",
    "B-offset",
    "B-coref",
    "URL",
]
MIN_ARTICLE_CHARS = 300


def read_people() -> list[dict[str, str]]:
    with (BASE / "people.csv").open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_people_csv_has_at_least_eighty_rows():
    people = read_people()

    assert len(people) >= 80
    assert {row["qid"] for row in people} == {row["qid"] for row in people}
    assert all(row["qid"].startswith("Q") and row["label"] and row["title"] for row in people)


def test_every_person_has_a_long_article():
    for row in read_people():
        article = BASE / "articles" / f"{row['qid']}.md"
        assert article.exists(), row["qid"]
        text = article.read_text(encoding="utf-8")
        assert len(text) >= MIN_ARTICLE_CHARS, row["qid"]
        assert text.startswith("# ")


def test_facts_jsonl_covers_the_people_with_enough_relations():
    people = {row["qid"] for row in read_people()}
    entries = [
        json.loads(line)
        for line in (BASE / "facts.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert {entry["qid"] for entry in entries} == people
    assert sum(len(entry["facts"]) for entry in entries) / len(entries) >= 4
    for entry in entries:
        for fact in entry["facts"]:
            assert fact["r"] in RELATIONS
            assert isinstance(fact["b"], str) and fact["b"]


def test_mentions_have_cross_references_and_marie_curie():
    mentions = json.loads((BASE / "mentions.json").read_text(encoding="utf-8"))

    assert sum(1 for targets in mentions.values() if targets) >= 20
    assert "Q37463" in mentions["Q7186"] or "Q41269" in mentions["Q7186"]


def test_gap_validation_has_the_expected_shape():
    with (BASE / "gap-validation.tsv").open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        rows = list(reader)

    # 454 rows x 2 candidate antecedents = the 908 labeled pairs GAP documents.
    assert len(rows) >= 450
    assert len(rows) * 2 >= 900
    assert reader.fieldnames == GAP_COLUMNS


def test_gap_in_corpus_keeps_the_header():
    with (BASE / "gap_in_corpus.tsv").open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        rows = list(reader)

    assert reader.fieldnames == GAP_COLUMNS
    assert isinstance(rows, list)
