"""Tests for the curation verbs exposed through SExpressionRuntime."""

from __future__ import annotations

from src.operational_model import LogicalSystem, SExpressionRuntime, TruthValue
from src.operational_model.system.s_expression_runtime import SExpressionRuntime as Runtime

from tests.test_operational_model import build_system

CANINOS = "wigame:caninos"


def build_runtime() -> tuple[LogicalSystem, Runtime]:
    """Builds the shared test system plus its runtime."""

    system = build_system()
    return system, SExpressionRuntime(system)


def find_fact(system: LogicalSystem, wigame_id: str, sexpr: str):
    """Returns the single fact with the given canonical proposition."""

    for fact in system.wigames[wigame_id].facts.values():
        if fact.proposition.sexpr() == sexpr:
            return fact
    raise AssertionError(f"missing fact {sexpr}")


def test_define_and_why_chain_of_two_levels():
    system, runtime = build_runtime()

    first = runtime.evaluate("(define (if (es wolf wild) (es wolf domestic)))")
    second = runtime.evaluate("(define (if (es wolf domestic) (es dog wild)))")
    chain = runtime.evaluate(f"(why {CANINOS} (es dog wild))")

    assert first.payload["derived"] == ["(es wolf domestic)"]
    assert second.payload["derived"] == ["(es dog wild)"]
    assert [node["proposition"] for node in chain.payload["chain"]] == [
        "(es dog wild)",
        "(es wolf domestic)",
        "(es wolf wild)",
    ]


def test_why_rejects_unknown_fact():
    system, runtime = build_runtime()

    result = runtime.evaluate(f"(why {CANINOS} (es dog wild))")

    assert result.status == "reject"
    assert result.sinn == "unsinnig"


def test_retract_marks_dependents_unknown():
    system, runtime = build_runtime()
    runtime.evaluate("(define (if (es wolf wild) (es wolf domestic)))")
    source = find_fact(system, CANINOS, "(es wolf wild)")
    dependent = find_fact(system, CANINOS, "(es wolf domestic)")

    result = runtime.evaluate(f"(retract {CANINOS} (es wolf wild) 'superseded')")

    assert result.status == "accept"
    assert result.payload["dependents"] == [dependent.fact_id]
    assert system.wigames[CANINOS].Vi.get("wolf", "wild") == TruthValue.FALSE.value
    assert system.wigames[CANINOS].Vi.get("wolf", "domestic") == TruthValue.UNKNOWN.value
    assert dependent.truth == TruthValue.UNKNOWN
    assert source.evidence["history"][-1]["action"] == "retract"


def test_assert_accepts_evidence_atom():
    system, runtime = build_runtime()

    result = runtime.evaluate(
        f"(assert {CANINOS} (es wolf domestic) "
        "evidence:{'tier':'observed','prov':[{'document_id':'d','span':[1,2],"
        "'extractor':'x','confidence':0.9}]})"
    )
    fact = find_fact(system, CANINOS, "(es wolf domestic)")

    assert result.status == "accept"
    assert fact.evidence["tier"] == "observed"
    assert fact.evidence["prov"][0]["document_id"] == "d"


def test_candidate_return_promote_and_reject():
    system, runtime = build_runtime()
    created = runtime.evaluate(
        f"(candidate fact {CANINOS} (es wolf domestic) "
        "evidence:{'stats':{'phi_entropic':0.91}})"
    )

    listed = runtime.evaluate(f"(return candidates {CANINOS} min-phi:0.85)")
    filtered = runtime.evaluate(f"(return candidates {CANINOS} min-phi:0.99)")
    promoted = runtime.evaluate(f"(promote {created.payload['candidate_id']})")
    second = runtime.evaluate(f"(candidate symbol {CANINOS} (lynx lince))")
    rejected = runtime.evaluate(f"(reject {second.payload['candidate_id']} 'duplicate source')")

    assert created.status == "accept"
    assert listed.payload["candidates"][0]["candidate_id"] == created.payload["candidate_id"]
    assert listed.payload["candidates"][0]["evidence"]["curation"] == "proposed"
    assert filtered.payload["candidates"] == []
    assert promoted.status == "accept"
    assert system.wigames[CANINOS].Vi.get("wolf", "domestic") == TruthValue.TRUE.value
    assert rejected.status == "accept"
    assert system.candidates[second.payload["candidate_id"]].evidence["curation"] == "rejected"
