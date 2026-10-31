"""Tests for the evaluation of convergence against hand-curated aliases."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from experiments.eval_matrix_kb import evaluate

REAL_KB = Path("/home/jp/proyectos/Matrix/Matrix/examples/kb_wikipedia_10_articles")

TOP_LEVEL_KEYS = {
    "kb",
    "config",
    "world",
    "gold",
    "scores",
    "false_merges",
    "ranking",
    "support",
    "timings",
}

# A minimal KB: two contexts that talk about two different people with the same
# pronoun and the same properties, plus five filler contexts whose
# configurations appear once (so they fall to the corroboration filter). The two
# people share six configurations, enough for the promotion rule, and the gold
# curation says the pronoun of each context is that context's person.
RELATIONS = {
    "es": "physicist",
    "nace_en": "warsaw",
    "premio": "nobel_prize",
    "muere_en": "paris",
    "miembro_de": "royal_society",
    "usa": "method",
}
PEOPLE = {"alpha": ("he", "alpha_person"), "beta": ("he", "beta_person")}
ALIASES = [
    {"context": "alpha", "symbol": "he", "canonical": "alpha_person"},
    {"context": "beta", "symbol": "he", "canonical": "beta_person"},
]


def _proposals() -> list[dict]:
    entries: list[dict] = []
    for ctx_id, (pronoun, name) in PEOPLE.items():
        for relation, obj in RELATIONS.items():
            for subject, sign in ((pronoun, pronoun.capitalize()), (name, name.replace("_", " ").title())):
                entries.append(
                    {
                        "context": ctx_id,
                        "relation": relation,
                        "subject": subject,
                        "subject_sign": sign,
                        "object": obj,
                        "object_sign": obj.replace("_", " "),
                    }
                )
    for index in range(5):
        entries.append(
            {
                "context": f"g{index}",
                "relation": "es",
                "subject": f"g{index}_star",
                "subject_sign": f"G{index} Star",
                "object": f"g{index}_thing",
                "object_sign": f"G{index} thing",
            }
        )
    return entries


def _write_kb(root: Path) -> Path:
    kb = root / "kb"
    proposals = kb / "proposals"
    proposals.mkdir(parents=True)
    by_name: dict[str, list[dict]] = {}
    for entry in _proposals():
        by_name.setdefault(f"{entry['context']}__{entry['relation']}", []).append(entry)
    for name, lines in by_name.items():
        payload = "\n".join(json.dumps(line) for line in lines)
        (proposals / f"{name}.jsonl").write_text(payload + "\n", encoding="utf-8")
    (kb / "aliases.yaml").write_text(
        yaml.safe_dump({"aliases": ALIASES}, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    return kb


def test_eval_matrix_kb_synthetic(tmp_path):
    kb = _write_kb(tmp_path)
    out = tmp_path / "out"

    metrics = evaluate(kb, out, min_contexts=2, taut_df=0.30)

    metrics_path = out / "metrics.json"
    assert metrics_path.exists()
    stored = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert set(stored) == set(metrics) and TOP_LEVEL_KEYS <= set(stored)
    assert (out / "report.md").exists()

    assert stored["world"]["contexts"] == 7
    assert stored["world"]["declarations"] == len(_proposals())
    assert stored["gold"]["pairs"] == 2
    assert stored["gold"]["pairs_intra"] == 2
    assert stored["scores"]["promoted_all"]["intra"]["f1"] == pytest.approx(1.0)
    for value in (
        stored["scores"]["promoted_all"]["intra"]["f1"],
        stored["scores"]["promoted_all"]["cross"]["f1"],
        stored["scores"]["promoted_or_proposed_variables"]["intra"]["f1"],
    ):
        assert value is None or 0.0 <= value <= 1.0
    assert stored["ranking"]["queries"] == 4
    assert stored["false_merges"]["count"] >= 1


def test_eval_matrix_kb_real_kb(tmp_path):
    if not REAL_KB.exists():
        pytest.skip("the Matrix example KB is not available")

    metrics = evaluate(REAL_KB, tmp_path / "out", min_contexts=1, taut_df=1.0)

    assert metrics["world"]["contexts"] == 10
    assert metrics["world"]["declarations"] == 699
    assert metrics["gold"]["pairs"] > 0
    value = metrics["scores"]["promoted_all"]["cross"]["f1"]
    assert value is None or 0.0 <= value <= 1.0
