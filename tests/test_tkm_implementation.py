import pytest
import sys
from pathlib import Path
import jax.numpy as jnp

# Ensure we can import from src
sys.path.insert(0, str(Path(__file__).parent / ".." / "src"))

from unified_engine import UnifiedMatrixEngine, TruthValue
from nl_parser import NaturalLanguageParser, LogicalValidator

def test_tkm_hierarchical_s_expression():
    """
    Test the full TKM pipeline:
    1. Parse S-Expression: (come juanico caca)
    2. Grounding: Map signs to symbols in hierarchical contexts.
    3. Sense Validation: Check if 'come' is applicable to 'juanico' in 'biology'.
    4. Truth Evaluation: Check if 'juanico come caca' is factual.
    5. Hierarchical Routing: World -> Biology -> Actions.
    """
    
    tkm_schema = {
        "contexts": {
            "world": {
                "objects": {
                    "juanico": {"class": "entity"},
                    "caca": {"class": "matter"}
                },
                "properties": {
                    "exists": {"applies_to": "entity"},
                    "is_biological": {"applies_to": "entity"}
                },
                "truths": {
                    "juanico": {"exists": True, "is_biological": True},
                    "caca": {"exists": True}
                }
            },
            "biology": {
                "objects": {
                    "juanico": {"class": "organism"}
                },
                "properties": {
                    "can_eat": {"applies_to": "organism"},
                    "needs_energy": {"applies_to": "organism"}
                },
                "truths": {
                    "juanico": {"can_eat": True, "needs_energy": True}
                }
            },
            "actions": {
                "objects": {
                    "juanico": {"class": "actor"}
                },
                "properties": {
                    "come.caca": {"applies_if": {"property": "can_eat", "context": "biology", "value": True}},
                    "come.comida": {"applies_to": "actor"}
                },
                "truths": {
                    "juanico": {"come.caca": True, "come.comida": True}
                }
            }
        },
        "bridges": [
            {
                "name": "world_to_bio",
                "from": "world",
                "to": "biology",
                "from_objects": ["juanico"],
                "to_objects": ["juanico"],
                "relation": "is_a"
            },
            {
                "name": "bio_to_actions",
                "from": "biology",
                "to": "actions",
                "from_objects": ["juanico"],
                "to_objects": ["juanico"],
                "relation": "performs"
            }
        ]
    }

    engine = UnifiedMatrixEngine.load_from_dict(tkm_schema)
    parser = NaturalLanguageParser()
    
    # 1. Test S-Expression Parsing
    query = "(come juanico caca)"
    parsed = parser.parse(query)
    assert parsed.relation == "come"
    assert parsed.subject == "juanico"
    assert parsed.property == "caca"

    # 2. Test Triple Parsing
    query_triple = "juanico come caca"
    parsed_triple = parser.parse(query_triple)
    assert parsed_triple.relation == "come"
    assert parsed_triple.subject == "juanico"
    assert parsed_triple.property == "caca"
    
    # 3. Test Hierarchical Status
    status = engine.get_status_hierarchical("juanico", "come", "caca")
    assert status["status"] == "sinnvoll"
    assert status["truth"] == "T"
    assert status["path"] == ["world", "biology", "actions"]

def test_tkm_unsinnig_detection():
    """
    Test that 'come' applied to something non-biological is 'unsinnig'.
    """
    tkm_schema = {
        "contexts": {
            "world": {
                "objects": {"piedra": {"class": "matter"}},
                "properties": {"is_biological": {"applies_to": "entity"}},
                "truths": {"piedra": {"is_biological": False}}
            },
            "biology": {
                "objects": {},
                "properties": {"can_eat": {"applies_to": "organism"}},
                "truths": {}
            }
        },
        "bridges": []
    }
    
    engine = UnifiedMatrixEngine.load_from_dict(tkm_schema)
    status = engine.get_status_hierarchical("piedra", "come", "comida")
    assert status["status"] == "unsinnig"

if __name__ == "__main__":
    pytest.main([__file__])
