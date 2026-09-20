"""Smoke test for the physicists evaluation script."""

from __future__ import annotations

import json

import pytest

from experiments.eval_physicists import run_evaluation

METRIC_KEYS = {"pronoun_convergence", "gap", "qa", "garbage", "timings", "world"}


def test_eval_physicists_smoke(tmp_path):
    from pathlib import Path

    corpus = Path(__file__).resolve().parents[1] / "corpus" / "physicists" / "articles"
    if not corpus.exists():
        pytest.skip("corpus/physicists is not available")

    evaluation = run_evaluation(tmp_path, limit=12)

    metrics_path = tmp_path / "metrics.json"
    assert metrics_path.exists()
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert METRIC_KEYS <= set(metrics)
    assert metrics["world"]["contexts"] == 12
    assert metrics["garbage"]["planted"] > 0
    assert metrics["qa"]["global"]["positive"] > 0
    assert (tmp_path / "report.md").exists()
    assert evaluation.metrics == metrics


def test_eval_physicists_section_smoke(tmp_path):
    from pathlib import Path

    corpus = Path(__file__).resolve().parents[1] / "corpus" / "physicists" / "en"
    if not corpus.exists():
        pytest.skip("corpus/physicists/en is not available")

    evaluation = run_evaluation(tmp_path, limit=6, unit="section", source="en")

    metrics = json.loads((tmp_path / "metrics.json").read_text(encoding="utf-8"))
    assert {"intra_article", "false_merges", "qa_hop", "garbage_converged"} <= set(metrics)
    assert metrics["world"]["contexts"] > 6
    assert evaluation.metrics["world"]["contexts"] == metrics["world"]["contexts"]


def test_eval_physicists_pairs_smoke(tmp_path):
    from pathlib import Path

    simple = Path(__file__).resolve().parents[1] / "corpus" / "physicists" / "articles"
    english = Path(__file__).resolve().parents[1] / "corpus" / "physicists" / "en"
    if not simple.exists() or not english.exists():
        pytest.skip("corpus/physicists is not available")

    evaluation = run_evaluation(tmp_path, limit=6, regime="pairs")

    metrics = json.loads((tmp_path / "metrics.json").read_text(encoding="utf-8"))
    assert {"pairs", "intra_context", "ranking", "qa_pairs", "false_merges"} <= set(metrics)
    assert metrics["pairs"]["people_evaluated"] > 0
    assert "mrr" in metrics["ranking"]
    assert evaluation.metrics["world"]["contexts"] == metrics["world"]["contexts"]
