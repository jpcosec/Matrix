import pytest
import yaml
from src.operational_model import (
    WiGame, Fact, Proposition, LiSpace, TruthValue, SenseValue
)

def test_wigame_full_roundtrip():
    # Build a complex WiGame
    li = LiSpace("li1", ["a"], ["b"], "R", metadata={"li_meta": 1})
    wigame = WiGame("wg1", li, context_id="ctx1", metadata={"wg_meta": "v1"})
    
    prop = Proposition("R", "a", "b", "wg1", "p1")
    fact = Fact(prop, TruthValue.TRUE, "f1", evidence={"src": "manual"})
    
    wigame.add_fact(fact)
    wigame.set_sense("a", "b", SenseValue.SINNVOLL)
    
    # Round-trip
    payload = wigame.to_yaml()
    restored = WiGame.from_yaml(payload)
    
    # Assertions
    assert restored.wigame_id == wigame.wigame_id
    assert restored.context_id == wigame.context_id
    assert restored.metadata == wigame.metadata
    assert restored.li.li_id == wigame.li.li_id
    assert restored.li.metadata == wigame.li.metadata
    
    assert "f1" in restored.facts
    restored_fact = restored.facts["f1"]
    assert restored_fact.truth == fact.truth
    assert restored_fact.evidence == fact.evidence
    assert restored_fact.proposition.proposition_id == fact.proposition.proposition_id
    
    assert restored.Vi.get("a", "b") == TruthValue.TRUE.value
    assert restored.Si.get("a", "b") == SenseValue.SINNVOLL.value

def test_serialization_compatibility_fallbacks():
    # Test that legacy keys like 'ejeA', 'relacion' still work
    legacy_payload = """
wigame_id: wg_legacy
ejeA: [o1]
ejeB: [p1]
relacion: is_a
contexto: ctx_legacy
Li:
  li_id: li_legacy
Vi:
  matrix_id: vi1
  rows: [o1]
  columns: [p1]
  values: ['1']
Si:
  matrix_id: si1
  rows: [o1]
  columns: [p1]
  values: ['V']
"""
    wigame = WiGame.from_yaml(legacy_payload)
    assert wigame.wigame_id == "wg_legacy"
    assert wigame.axis_a == ["o1"]
    assert wigame.relation_id == "is_a"
    assert wigame.context_id == "ctx_legacy"
