import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from unified_engine import UnifiedMatrixEngine, Context
from tkm_orchestrator import TKMOrchestrator

def test_whitepaper_self_ingestion():
    print("🚀 STARTING SELF-REFERENTIAL STRESS TEST: WHITE PAPER INGESTION\n")
    
    # 1. Initialize empty 'Metatheory' context
    meta_ctx = Context(
        name="TKM_Metatheory",
        objects=[],
        properties=[],
        objects_meta={},
        properties_meta={},
        truths={}
    )
    engine = UnifiedMatrixEngine(contexts={"TKM_Metatheory": meta_ctx})
    orchestrator = TKMOrchestrator(engine)
    
    # 2. Key Propositions extracted from the Whitepaper
    propositions = [
        "TKM utiliza 4 máscaras estructurales (Vi, Si, Oi, Di).",
        "E(R) mide la densidad de conocimiento de un contexto.",
        "El motor utiliza JAX para el Colapso Dimensional.",
        "El modo G prioriza la integridad del grafo canónico.",
        "El modo M prioriza la fidelidad al texto episódico.",
        "La Máquina de Conocimiento Tractariana es autoplástica."
    ]
    
    # 3. Simulated LLM Responses (Grounding decisions)
    # In a real scenario, these would come from an actual LLM call.
    llm_simulations = [
        {
            "action": "EXPAND_SCHEMA",
            "subject": {"id": "ID_TKM", "is_new": True, "sign": "TKM"},
            "property": {"id": "PROP_USES_MASKS", "is_new": True, "sign": "utiliza máscaras", "rationale": "Base architectural feature"},
            "value": True
        },
        {
            "action": "EXPAND_SCHEMA",
            "subject": {"id": "ID_ER_FORMULA", "is_new": True, "sign": "E(R)"},
            "property": {"id": "PROP_MEASURES_DENSITY", "is_new": True, "sign": "mide densidad", "rationale": "Information energy metric"},
            "value": True
        },
        {
            "action": "EXPAND_SCHEMA",
            "subject": {"id": "ID_JAX_ENGINE", "is_new": True, "sign": "JAX"},
            "property": {"id": "PROP_DOES_COLLAPSE", "is_new": True, "sign": "hace colapso dimensional", "rationale": "Mathematical operation"},
            "value": True
        },
        {
            "action": "EXPAND_SCHEMA",
            "subject": {"id": "ID_MODE_G", "is_new": True, "sign": "Modo G"},
            "property": {"id": "PROP_PRIORITIZES_INTEGRITY", "is_new": True, "sign": "prioriza integridad", "rationale": "Canonical constraint"},
            "value": True
        },
        {
            "action": "EXPAND_SCHEMA",
            "subject": {"id": "ID_MODE_M", "is_new": True, "sign": "Modo M"},
            "property": {"id": "PROP_PRIORITIZES_FIDELITY", "is_new": True, "sign": "prioriza fidelidad", "rationale": "Surface text mapping"},
            "value": True
        },
        {
            "action": "MAP_IDENTITY",
            "subject": {"id": "ID_TKM", "is_new": False, "sign": "Máquina de Conocimiento"},
            "property": {"id": "PROP_IS_AUTOPLASTIC", "is_new": True, "sign": "es autoplástica", "rationale": "System behavior"},
            "value": True
        }
    ]
    
    # 4. Ingestion Loop
    for i, prop_text in enumerate(propositions):
        print(f"--- Ingesting Fact {i+1}: '{prop_text}' ---")
        # In real use: response = call_llm(orchestrator.get_ingestion_prompt(prop_text, "TKM_Metatheory"))
        orchestrator.process_llm_response(llm_simulations[i], "TKM_Metatheory", mode="M")
    
    # 5. Validation of Self-Representation
    ctx = engine.contexts["TKM_Metatheory"]
    print(f"\n📊 METATHEORY CONTEXT STATS:")
    print(f" - Objects: {len(ctx.objects)} ({', '.join(ctx.objects)})")
    print(f" - Properties: {len(ctx.properties)} ({', '.join(ctx.properties)})")
    
    energy = engine.get_information_energy("TKM_Metatheory")
    print(f" - Information Energy E(R): {energy:.4f}")
    
    # 6. Visualization
    from unified_engine import TKMVisualizer
    viz = TKMVisualizer(engine)
    viz.export_context_matrix("TKM_Metatheory", "spec/whitepaper_self_logic.yaml")
    print(f"\n[VIZ] Exported Metatheory Matrix to spec/whitepaper_self_logic.yaml")
    
    assert energy > 0
    assert "ID_TKM" in ctx.objects
    assert "PROP_USES_MASKS" in ctx.properties
    
    print("\n✅ SELF-REFERENTIAL STRESS TEST COMPLETED SUCCESSFULLY.")

if __name__ == "__main__":
    test_whitepaper_self_ingestion()
