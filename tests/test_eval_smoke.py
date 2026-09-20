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
