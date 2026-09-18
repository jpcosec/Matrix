"""Tests for the candidate curation queue."""

from __future__ import annotations

from src.operational_model import (
    Fact,
    Proposition,
    SenseValue,
    TruthValue,
)
from src.operational_model.system.candidates import (
    promote_candidate,
    register_candidate,
    reject_candidate,
)

from tests.test_operational_model import build_system

ANIMALS = "wigame:animales"


def test_register_candidate_defaults_to_proposed_statistical():
    system = build_system()

    candidate = register_candidate(
        system,
        "fact",
        ANIMALS,
        {"proposition": "(es dog fur)"},
    )

    assert system.candidates[candidate.candidate_id] is candidate
    assert candidate.evidence["curation"] == "proposed"
    assert candidate.evidence["tier"] == "statistical"


def test_promote_fact_writes_truth_and_confirms_evidence():
    system = build_system()
    candidate = register_candidate(
        system,
        "fact",
        ANIMALS,
        {"proposition": "(es dog fur)"},
        {"prov": []},
    )

    result = promote_candidate(system, candidate.candidate_id)

    assert result.status == "accept"
    assert system.wigames[ANIMALS].Vi.get("dog", "fur") == TruthValue.TRUE.value
    assert candidate.evidence["curation"] == "confirmed"
    assert candidate.evidence["tier"] == "confirmed"
    assert candidate.evidence["history"][-1]["action"] == "promote"


def test_promote_fact_rejects_contradiction():
    system = build_system()
    system.add_fact(Fact(Proposition("es", "dog", "fur", ANIMALS), TruthValue.FALSE))
    candidate = register_candidate(system, "fact", ANIMALS, {"proposition": "(es dog fur)"})

    result = promote_candidate(system, candidate.candidate_id)

    assert result.status == "reject"
    assert result.sinn == "widerspruechlich"
    assert candidate.evidence["curation"] == "proposed"
    assert system.wigames[ANIMALS].Vi.get("dog", "fur") == TruthValue.FALSE.value


def test_promote_symbol_registers_thing():
    system = build_system()
    candidate = register_candidate(
        system,
        "symbol",
        ANIMALS,
        {"symbol_id": "cat", "sign": "gato"},
    )

    result = promote_candidate(system, candidate.candidate_id)

    assert result.status == "accept"
    assert "cat" in system.symbols
    assert system.things["cat"].name.sign == "gato"


def test_promote_nonsense_sets_unsinnig_sense():
    system = build_system()
    candidate = register_candidate(
        system,
        "nonsense",
        ANIMALS,
        {"proposition": "(es dog fur)"},
    )

    result = promote_candidate(system, candidate.candidate_id)

    assert result.status == "accept"
    assert system.wigames[ANIMALS].Si.get("dog", "fur") == SenseValue.UNSINNIG.value


def test_promote_rule_registers_rule_and_derives():
    system = build_system()
    candidate = register_candidate(
        system,
        "rule",
        "wigame:caninos",
        {"if": "(es wolf wild)", "then": "(es wolf domestic)"},
    )

    result = promote_candidate(system, candidate.candidate_id)

    assert result.status == "accept"
    assert result.payload["derived"] == ["(es wolf domestic)"]
    assert system.rules
    assert system.wigames["wigame:caninos"].Vi.get("wolf", "domestic") == TruthValue.TRUE.value


def test_promote_class_creates_child_wigame_and_projection():
    system = build_system()
    candidate = register_candidate(
        system,
        "class",
        ANIMALS,
        {"class_id": "caninos_chicos", "symbols": ["dog"], "relation_id": "es"},
    )

    result = promote_candidate(system, candidate.candidate_id)

    assert result.status == "accept"
    child_id = result.payload["wigame_id"]
    assert child_id == "wigame:caninos_chicos"
    assert child_id in system.wigames
    assert system.wigames[child_id].context_id == ANIMALS
    projection = system.projections[result.payload["projection_id"]]
    assert projection.get("dog", "dog") is True


def test_reject_candidate_keeps_it_with_rejected_curation():
    system = build_system()
    candidate = register_candidate(system, "fact", ANIMALS, {"proposition": "(es dog fur)"})

    result = reject_candidate(system, candidate.candidate_id, "not supported by sources")

    assert result.status == "accept"
    assert candidate.evidence["curation"] == "rejected"
    assert candidate.evidence["history"][-1]["note"] == "not supported by sources"
    assert candidate.candidate_id in system.candidates


def test_promote_unknown_candidate_rejects():
    system = build_system()

    result = promote_candidate(system, "cand:missing")

    assert result.status == "reject"
    assert result.sinn == "unsinnig"
