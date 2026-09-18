"""Tests for LLM-assisted curation (proposals never confirm anything)."""

from __future__ import annotations

import json
from pathlib import Path
import shutil

import pytest

from pipeline.curate import FakeBackend, Proposal, curate_queue, propose
from pipeline.run import build_system
from populator import build_corpus, read_documents

CORPUS = str(Path(__file__).resolve().parents[1] / "corpus" / "vegetales")


@pytest.fixture(scope="module")
def world():
    documents = read_documents(CORPUS)
    corpus = build_corpus(documents, lang="es")
    system, runtime, _ = build_system(CORPUS, "vegetales", corpus=corpus, documents=documents)
    return system, documents


def first_pending(system):
    """Returns the highest-intensity queued fact candidate."""

    candidates = [
        candidate
        for candidate in system.candidates.values()
        if candidate.kind == "fact" and candidate.evidence.get("curation") == "proposed"
    ]
    candidates.sort(key=lambda candidate: -candidate.evidence["stats"]["phi_entropic"])
    return candidates[0]


def test_propose_parses_clean_json(world):
    system, documents = world
    candidate = first_pending(system)
    reply = json.dumps(
        {"sexpr": "(implies lechuga hoja)", "prov_index": 0, "keep": True, "comment": "respaldado"}
    )

    proposal = propose(system, candidate.candidate_id, FakeBackend(reply), documents)

    assert proposal.sexpr == "(implies lechuga hoja)"
    assert proposal.prov_index == 0
    assert proposal.keep is True
    assert proposal.comment == "respaldado"
    assert candidate.evidence["llm"]["backend"] == "fake"


def test_propose_parses_json_surrounded_by_prose(world):
    system, documents = world
    candidate = first_pending(system)
    reply = (
        "Claro, esta es mi propuesta:\n"
        '{"sexpr": "(implies lechuga hoja)", "prov_index": 1, "keep": false, "comment": "dudoso"}\n'
        "Espero que sirva."
    )

    proposal = propose(system, candidate.candidate_id, FakeBackend(reply), documents)

    assert proposal.sexpr == "(implies lechuga hoja)"
    assert proposal.prov_index == 1
    assert proposal.keep is False


def test_propose_never_changes_curation(world):
    system, documents = world
    before = {candidate.candidate_id: candidate.evidence["curation"] for candidate in system.candidates.values()}

    curate_queue(system, FakeBackend('{"sexpr": "", "prov_index": 0, "keep": true, "comment": ""}'), documents, limit=3)

    after = {candidate.candidate_id: candidate.evidence["curation"] for candidate in system.candidates.values()}
    assert before == after


def test_curate_queue_writes_llm_evidence(world):
    system, documents = world
    reply = json.dumps({"sexpr": "(implies a b)", "prov_index": 0, "keep": True, "comment": "ok"})

    proposals = curate_queue(system, FakeBackend(reply), documents, limit=3)

    assert len(proposals) == 3
    assert all(isinstance(proposal, Proposal) for proposal in proposals)
    for proposal in proposals:
        candidate = system.candidates[proposal.candidate_id]
        assert candidate.evidence["llm"]["sexpr"] == "(implies a b)"
        assert candidate.evidence["curation"] == "proposed"


def test_propose_rejects_unknown_candidate(world):
    system, documents = world

    with pytest.raises(KeyError):
        propose(system, "cand:missing", FakeBackend("{}"), documents)


@pytest.mark.skipif(shutil.which("pi") is None, reason="the pi CLI is not installed")
def test_pi_backend_returns_a_valid_proposal(world):
    from pipeline.curate import PiBackend

    system, documents = world
    candidate = first_pending(system)

    proposal = propose(system, candidate.candidate_id, PiBackend(), documents)

    assert isinstance(proposal, Proposal)
    assert candidate.evidence["llm"]["backend"].startswith("pi:")
    assert candidate.evidence["curation"] == "proposed"
