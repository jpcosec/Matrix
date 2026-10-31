"""Tests for the physicists corpus (Simple English + English articles)."""

from __future__ import annotations

import csv
from pathlib import Path

from populator import build_context, chunk_documents, read_documents

CORPUS = Path(__file__).resolve().parents[1] / "corpus" / "physicists"
EN_DIR = CORPUS / "en"


def test_english_directory_has_enough_articles():
    files = sorted(EN_DIR.glob("*.md"))

    assert len(files) >= 80


def test_every_english_article_starts_with_a_title_and_has_sections():
    for path in sorted(EN_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        headings = [
            line
            for line in text.splitlines()
            if line.startswith("## ") or line.startswith("### ")
        ]
        assert text.startswith("# "), path.name
        assert len(headings) >= 2, path.name
        assert "== References ==" not in text, path.name


def test_most_english_articles_have_two_top_level_sections():
    with_two = 0
    for path in sorted(EN_DIR.glob("*.md")):
        top_level = [
            line
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.startswith("## ") and not line.startswith("### ")
        ]
        with_two += len(top_level) >= 2

    assert with_two >= 80


def test_people_csv_carries_the_english_title():
    rows = list(csv.DictReader((CORPUS / "people.csv").open(encoding="utf-8")))

    assert rows
    assert all(row.get("en_title") for row in rows)


def test_curie_article_sections_keep_the_name_and_pronoun():
    chunks = chunk_documents(read_documents(EN_DIR / "Q7186.md"), unit="section")

    assert len(chunks) >= 3
    assert [chunk.ctx_id for chunk in chunks] == [
        f"Q7186#{index}" for index in range(len(chunks))
    ]
    assert all(chunk.metadata["article"] == "Q7186" for chunk in chunks)
    for chunk in chunks:
        context = build_context(chunk, lang="en")
        assert context.signs["marie curie"].kind == "name"
        if f"she@{chunk.ctx_id}" in context.signs:
            assert context.signs["she"].kind == "pronoun"
