import pytest
import sys
from pathlib import Path
import jax.numpy as jnp

# Ensure we can import from src
sys.path.insert(0, str(Path(__file__).parent / ".." / "src"))

from unified_engine import UnifiedMatrixEngine, TruthValue
from nl_parser import NaturalLanguageParser

def test_wikipedia_solar_system_encoding():
    """
    Encodes Solar System facts from Wikipedia into TKM and validates.
    """
    
    # 1. TKM Schema for Solar System (Complete implementation)
    solar_schema = {
        "contexts": {
            "cosmology": {
                "objects": {
                    "sol": {"class": "star"},
                    "tierra": {"class": "planet"},
                    "jupiter": {"class": "planet"},
                    "ganimedes": {"class": "moon"}
                },
                "properties": {
                    "es.estrella": {"applies_to": "star"},
                    "es.planeta": {"applies_to": "planet"},
                    "es.luna": {"applies_to": "moon"}
                },
                "truths": {
                    "sol": {"es.estrella": True},
                    "tierra": {"es.planeta": True},
                    "jupiter": {"es.planeta": True},
                    "ganimedes": {"es.luna": True}
                }
            },
            "planetary_types": {
                "objects": {
                    "tierra": {"class": "planet"},
                    "jupiter": {"class": "planet"}
                },
                "properties": {
                    "es.rocoso": {"applies_if": {"property": "es.planeta", "context": "cosmology", "value": True}},
                    "es.gigante_gaseoso": {"applies_if": {"property": "es.planeta", "context": "cosmology", "value": True}}
                },
                "truths": {
                    "tierra": {"es.rocoso": True, "es.gigante_gaseoso": False},
                    "jupiter": {"es.rocoso": False, "es.gigante_gaseoso": True}
                }
            },
            "habitability": {
                "objects": {
                    "tierra": {"class": "planet"},
                    "jupiter": {"class": "planet"}
                },
                "properties": {
                    "tiene.agua_liquida": {"applies_if": {"property": "es.rocoso", "context": "planetary_types", "value": True}},
                    "tiene.vida": {"applies_if": {"property": "tiene.agua_liquida", "value": True}}
                },
                "truths": {
                    "tierra": {"tiene.agua_liquida": True, "tiene.vida": True},
                    "jupiter": {"tiene.agua_liquida": False}
                }
            }
        },
        "bridges": [
            {
                "name": "cosmo_to_types",
                "from": "cosmology",
                "to": "planetary_types",
                "from_objects": ["tierra", "jupiter"],
                "to_objects": ["tierra", "jupiter"]
            },
            {
                "name": "types_to_hab",
                "from": "planetary_types",
                "to": "habitability",
                "from_objects": ["tierra", "jupiter"],
                "to_objects": ["tierra", "jupiter"]
            }
        ]
    }

    # Initialize MEEL Engine
    engine = UnifiedMatrixEngine.load_from_dict(solar_schema)
    parser = NaturalLanguageParser()

    # TEST 1: S-Expression Parsing & Status (CDV Format: Concept, Dimension, Value)
    # "(tierra tiene vida)"
    query = "(tierra tiene vida)"
    parsed = parser.parse(query)
    
    # Path: cosmology -> planetary_types -> habitability
    status = engine.get_status_hierarchical(parsed.subject, parsed.relation, parsed.property)
    
    print(f"\n[TEST 1] (tierra tiene vida) Status: {status['status']}")
    assert status["status"] == "sinnvoll"
    assert status["truth_label"] == "TRUE"
    assert "habitability" in status["path"]

    # TEST 2: Unsinnig Detection
    # "(sol tiene vida)" -> Stars cannot have life (no path/sense in habitability context for stars)
    query_sol = "(sol tiene vida)"
    parsed_sol = parser.parse(query_sol)
    status_sol = engine.get_status_hierarchical(parsed_sol.subject, parsed_sol.relation, parsed_sol.property)
    print(f"[TEST 2] (sol tiene vida) Status: {status_sol['status']} (Reason: {status_sol.get('reason')})")
    assert status_sol["status"] == "unsinnig"

    # TEST 3: Information Energy E(R)
    energy = engine.get_information_energy("planetary_types")
    print(f"[TEST 3] Information Energy of 'planetary_types': {energy:.4f}")
    assert energy > 0

    # TEST 4: DFA Reasoning
    # Check if we can reach stable state
    dfa_res = engine.run_dfa_reasoning("cosmology", steps=2)
    print(f"[TEST 4] DFA Reasoning (cosmology) Matrix Active Bits: {jnp.sum(dfa_res)}")
    assert dfa_res.any()

    # TEST 5: Omnirepresentation
    omni = engine.get_omnirepresentation()
    print(f"[TEST 5] Omnirepresentation (Block Matrix) Size: {omni.shape}")
    assert omni.sum() > 0
    
    # NEW TEST: Visualization Export
    from unified_engine import TKMVisualizer
    viz = TKMVisualizer(engine)
    viz.export_knowledge_tree("spec/solar_system_tree.yaml")
    viz.export_context_matrix("habitability", "spec/solar_system_habitability.yaml")
    print(f"\n[VIZ] Exported Solar System Tree and habitability Matrix to spec/")

    print("\n✅ ALL TKM ATOMS VALIDATED WITH WIKIPEDIA DATA.")

if __name__ == "__main__":
    test_wikipedia_solar_system_encoding()
