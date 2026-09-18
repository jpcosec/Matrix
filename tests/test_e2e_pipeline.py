"""End-to-end tests over the populated vegetales WiGame."""

from __future__ import annotations

from pathlib import Path

import pytest

from pipeline import build_system

CORPUS = str(Path(__file__).resolve().parents[1] / "corpus" / "vegetales")
UNKNOWN = "\u2205"


@pytest.fixture
def populated():
    return build_system(CORPUS)


def test_auto_confirmed_rule_reads_true(populated):
    _, runtime, _ = populated

    result = runtime.evaluate("(check wigame:vegetales (implies lechuga hoja))")

    assert result.payload["truth"] == "true"


def test_unconfirmed_rule_stays_unknown(populated):
    _, runtime, _ = populated

    result = runtime.evaluate("(check wigame:vegetales (implies zanahoria hoja))")

    assert result.payload["truth"] in {UNKNOWN, "false"}


def test_why_returns_provenance(populated):
    _, runtime, _ = populated

    chain = runtime.evaluate("(why wigame:vegetales (implies lechuga hoja))").payload["chain"]

    assert chain
    assert chain[0]["tier"] in {"confirmed", "observed"}
    assert chain[0]["prov"]


def test_define_derives_and_why_shows_two_levels(populated):
    _, runtime, _ = populated
    runtime.evaluate("(create symbol verdura_de_hoja verdura_de_hoja)")

    defined = runtime.evaluate("(define (if (implies lechuga hoja) (implies lechuga hoja_lisa)))")
    check = runtime.evaluate("(check wigame:vegetales (implies lechuga hoja_lisa))")
    chain = runtime.evaluate("(why wigame:vegetales (implies lechuga hoja_lisa))").payload["chain"]

    assert defined.payload["derived"] == ["(implies lechuga hoja_lisa)"]
    assert check.payload["truth"] == "true"
    assert len(chain) == 2
    assert chain[0]["derived_from"] == [chain[1]["fact_id"]]
    assert chain[1]["prov"]


def test_retract_turns_derived_fact_unknown(populated):
    _, runtime, _ = populated
    runtime.evaluate("(define (if (implies lechuga hoja) (implies lechuga hoja_lisa)))")
    derived_id = runtime.evaluate("(why wigame:vegetales (implies lechuga hoja_lisa))").payload["chain"][0]["fact_id"]

    retract = runtime.evaluate("(retract wigame:vegetales (implies lechuga hoja) 'revisado')")
    check = runtime.evaluate("(check wigame:vegetales (implies lechuga hoja_lisa))")

    assert derived_id in retract.payload["dependents"]
    assert check.payload["truth"] == UNKNOWN


def test_promote_of_pending_candidate_reads_true(populated):
    _, runtime, _ = populated
    candidates = runtime.evaluate("(return candidates curation:proposed)").payload["candidates"]
    assert candidates
    fact = next(record for record in candidates if record["kind"] == "fact")
    proposition = fact["payload"]["proposition"]

    promoted = runtime.evaluate(f"(promote {fact['candidate_id']})")
    check = runtime.evaluate(f"(check wigame:vegetales {proposition})")

    assert promoted.status == "accept"
    assert check.payload["truth"] == "true"
