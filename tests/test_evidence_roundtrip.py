"""Round-trip tests for evidence, derived facts and rules through YAML."""

from __future__ import annotations

from src.operational_model import (
    Fact,
    LiSpace,
    LogicalSystem,
    Proposition,
    Relation,
    SExpressionRuntime,
    TruthValue,
    WiGame,
)
from src.operational_model.core.evidence import append_history, make_evidence


def build_world() -> tuple[LogicalSystem, WiGame, Fact, Fact]:
    """Builds a two-fact world with one observed and one derived fact."""

    system = LogicalSystem()
    system.register_relation(Relation("es", "es"))
    wigame = WiGame(
        wigame_id="wigame:w",
        li=LiSpace(li_id="li:w", axis_a=["a"], axis_b=["b", "c"], relation_id="es"),
    )
    system.register_wigame(wigame)
    observed = Fact(
        Proposition("es", "a", "b", "wigame:w"),
        TruthValue.TRUE,
        evidence=make_evidence(
            tier="observed",
            prov=[
                {
                    "document_id": "doc.md",
                    "span": [0, 12],
                    "extractor": "populator@0.1",
                    "confidence": 0.9,
                }
            ],
        ),
    )
    append_history(observed.evidence, "assert", by="jp", note="manual")
    system.add_fact(observed)
    derived = Fact(
        Proposition("es", "a", "c", "wigame:w"),
        TruthValue.TRUE,
        evidence=make_evidence(
            tier="inferred",
            derived_from=[observed.fact_id],
            rule="(if (es a b) (es a c))",
        ),
    )
    system.add_fact(derived)
    return system, wigame, observed, derived


def test_evidence_survives_yaml_roundtrip():
    _, wigame, observed, derived = build_world()

    restored = WiGame.from_yaml(wigame.to_yaml())

    assert set(restored.facts) == {observed.fact_id, derived.fact_id}
    assert restored.facts[observed.fact_id].evidence == observed.evidence
    assert restored.facts[derived.fact_id].evidence == derived.evidence
    assert restored.facts[derived.fact_id].evidence["derived_from"] == [observed.fact_id]
    assert restored.facts[derived.fact_id].evidence["rule"] == "(if (es a b) (es a c))"
    assert restored.facts[observed.fact_id].evidence["prov"][0]["document_id"] == "doc.md"
    assert restored.facts[observed.fact_id].evidence["history"][-1]["action"] == "assert"


def test_why_payload_is_identical_after_reload():
    system, wigame, _, _ = build_world()
    before = SExpressionRuntime(system).evaluate("(why wigame:w (es a c))").payload

    restored = WiGame.from_yaml(wigame.to_yaml())
    restored_system = LogicalSystem()
    restored_system.register_wigame(restored)
    after = SExpressionRuntime(restored_system).evaluate("(why wigame:w (es a c))").payload

    assert before == after
    assert [node["tier"] for node in after["chain"]] == ["inferred", "observed"]


def test_truth_matrix_survives_reload():
    _, wigame, _, _ = build_world()

    restored = WiGame.from_yaml(wigame.to_yaml())

    assert restored.Vi.get("a", "b") == TruthValue.TRUE.value
    assert restored.Vi.get("a", "c") == TruthValue.TRUE.value
    assert restored.Si.get("a", "c") == "sinnvoll"
