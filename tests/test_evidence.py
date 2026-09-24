"""Tests for the fact evidence schema."""

from __future__ import annotations

import pytest

from src.operational_model import Fact, Proposition, TruthValue
from src.operational_model.core.evidence import (
    append_history,
    make_evidence,
    validate_evidence,
)


def build_fact(evidence: dict | None = None) -> Fact:
    """Builds a fact over a throwaway proposition."""

    payload = {} if evidence is None else evidence
    return Fact(Proposition("es", "a", "b", "wigame:w"), TruthValue.TRUE, evidence=payload)


def test_fact_without_evidence_gets_defaults():
    fact = build_fact()

    assert fact.evidence["tier"] == "observed"
    assert fact.evidence["curation"] == "confirmed"
    assert fact.evidence["history"] == []


def test_extra_evidence_keys_are_preserved_with_defaults():
    fact = build_fact({"src": "manual"})

    assert fact.evidence["src"] == "manual"
    assert fact.evidence["tier"] == "observed"
    assert fact.evidence["curation"] == "confirmed"


def test_make_evidence_rejects_unknown_tier_and_curation():
    with pytest.raises(ValueError):
        make_evidence(tier="bogus")
    with pytest.raises(ValueError):
        make_evidence(curation="bogus")


def test_validate_evidence_accepts_well_formed_prov():
    evidence = make_evidence(
        tier="statistical",
        curation="proposed",
        prov=[
            {
                "document_id": "recetas/ragout.md",
                "span": [412, 468],
                "extractor": "populator@0.1",
                "confidence": 0.97,
            }
        ],
    )

    validate_evidence(evidence)


def test_validate_evidence_rejects_malformed_prov():
    with pytest.raises(ValueError):
        validate_evidence({"prov": "not-a-list"})
    with pytest.raises(ValueError):
        validate_evidence({"prov": [{"document_id": "d"}]})
    with pytest.raises(ValueError):
        validate_evidence({"prov": [{"document_id": "d", "span": [1], "extractor": "x", "confidence": 1.0}]})


def test_append_history_adds_timestamped_entry():
    evidence = make_evidence()
    append_history(evidence, "confirm", by="jp", note="checked against source")

    entry = evidence["history"][-1]
    assert entry["action"] == "confirm"
    assert entry["by"] == "jp"
    assert entry["note"] == "checked against source"
    assert entry["at"].endswith("Z")
