import pytest
from unified_engine import UnifiedMatrixEngine, Context
from tkm_orchestrator import TKMOrchestrator

def test_tkm_orchestration_flow():
    # 1. Setup minimal engine
    ctx = Context(
        name="biology",
        objects=["ID_DOG"],
        properties=["PROP_BARKS"],
        objects_meta={"ID_DOG": {}},
        properties_meta={"PROP_BARKS": {}},
        truths={"ID_DOG": {"PROP_BARKS": True}}
    )
    engine = UnifiedMatrixEngine(contexts={"biology": ctx})
    engine.registry.add_sign("ID_DOG", "perro")
    engine.registry.add_sign("PROP_BARKS", "ladra")
    
    orchestrator = TKMOrchestrator(engine)
    
    # 2. Test MAP_SEMANTIC (Synonym)
    # Text: "El can ladra"
    llm_response_synonym = {
        "action": "MAP_SEMANTIC",
        "subject": {"id": "ID_DOG", "is_new": False, "sign": "can"},
        "property": {"id": "PROP_BARKS", "is_new": False, "sign": "ladra"},
        "value": True
    }
    orchestrator.process_llm_response(llm_response_synonym, "biology")
    
    assert "can" in engine.registry.get_signs("ID_DOG")
    assert engine.registry.get_symbol("can") == "ID_DOG"
    
    # 3. Test EXPAND_SCHEMA (New axis)
    # Text: "El perro corre"
    llm_response_expand = {
        "action": "EXPAND_SCHEMA",
        "subject": {"id": "ID_DOG", "is_new": False, "sign": "perro"},
        "property": {"id": "PROP_RUNS", "is_new": True, "sign": "corre", "rationale": "Nueva actividad"},
        "value": True
    }
    orchestrator.process_llm_response(llm_response_expand, "biology")
    
    assert "PROP_RUNS" in engine.contexts["biology"].properties
    assert engine.Vi["biology"][0, 1] == 2 # True in JAX matrix
    
    # 4. Test Mode G (Integration Check)
    # Trying to set a fact that is already known (Sinnlos/Tautology)
    # In our engine, setting the same value might not be 'sinnlos' yet, 
    # but we can test the warning logic if we define it as such.
    # For now, let's test a case that would be 'unsinnig' if we had schema constraints.
    
    # Let's add a constraint: only animals can bark.
    engine.contexts["biology"].properties_meta["PROP_BARKS"]["applies_to"] = ["ID_DOG"]
    
    # Add a new object that is NOT a dog
    engine.add_object("biology", "ID_ROCK", "piedra")
    
    # LLM tries to say "La piedra ladra"
    llm_response_unsinnig = {
        "action": "MAP_IDENTITY",
        "subject": {"id": "ID_ROCK", "is_new": False, "sign": "piedra"},
        "property": {"id": "PROP_BARKS", "is_new": False, "sign": "ladra"},
        "value": True
    }
    
    print("\n[TEST] Expecting UNSINNIG warning for G-mode:")
    orchestrator.process_llm_response(llm_response_unsinnig, "biology", mode="G")
    
    # Value should not be updated in truths if rejected (our set_fact currently skips on G-warning)
    assert "ID_ROCK" not in engine.contexts["biology"].truths or \
           "PROP_BARKS" not in engine.contexts["biology"].truths["ID_ROCK"]

    print("\n✅ TKM ORCHESTRATION VALIDATED.")

if __name__ == "__main__":
    test_tkm_orchestration_flow()
