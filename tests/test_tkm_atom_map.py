import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from unified_engine import UnifiedMatrixEngine, Context, Bridge

def test_tkm_atom_routing_map():
    print("🌐 CONSTRUCTING TKM ATOM ROUTING MAP (GLOBAL OMNIREPRESENTATION)\n")
    
    # 1. Defining Contexts for Atom Categories
    # CATEGORY: COMPUTATION (Logic & Engine)
    comp_ctx = Context(
        name="computation_atoms",
        objects=["MASKS", "ENERGY", "DFA", "OMNI", "AUTOPLASTICITY"],
        properties=["IS_OPERATIONAL", "SUPPORTS_JAX", "IS_RECURSIVE"],
        objects_meta={}, properties_meta={},
        truths={
            "MASKS": {"IS_OPERATIONAL": True},
            "ENERGY": {"IS_OPERATIONAL": True},
            "DFA": {"IS_OPERATIONAL": True, "SUPPORTS_JAX": True, "IS_RECURSIVE": True},
            "OMNI": {"IS_OPERATIONAL": True, "IS_RECURSIVE": True},
            "AUTOPLASTICITY": {"IS_OPERATIONAL": True}
        }
    )
    
    # CATEGORY: PHILOSOPHY (Meaning & Context)
    phil_ctx = Context(
        name="philosophy_atoms",
        objects=["SIGN_SYMBOL", "CONTEXT", "SENSE_STATUS"],
        properties=["IS_TRACTARIAN", "GOVERNS_MEANING"],
        objects_meta={}, properties_meta={},
        truths={
            "SIGN_SYMBOL": {"IS_TRACTARIAN": True, "GOVERNS_MEANING": True},
            "CONTEXT": {"IS_TRACTARIAN": True, "GOVERNS_MEANING": True},
            "SENSE_STATUS": {"IS_TRACTARIAN": True, "GOVERNS_MEANING": True}
        }
    )

    # CATEGORY: MATHEMATICS (Matrix & Tensors)
    math_ctx = Context(
        name="math_atoms",
        objects=["BOOLEAN_ALGEBRA", "DIM_COLLAPSE", "BLOCK_MATRIX"],
        properties=["USES_SEMIRING", "REDUCES_SPACE"],
        objects_meta={}, properties_meta={},
        truths={
            "BOOLEAN_ALGEBRA": {"USES_SEMIRING": True},
            "DIM_COLLAPSE": {"REDUCES_SPACE": True},
            "BLOCK_MATRIX": {"REDUCES_SPACE": True}
        }
    )

    # 2. Defining Bridges (Routing between Atoms)
    bridges = [
        # Philosophy governs how Computation applies masks
        Bridge("phil_to_comp", "philosophy_atoms", "computation_atoms", 
               ["SENSE_STATUS"], ["MASKS"]),
        
        # Math provides the tools for DFA and Collapse
        Bridge("math_to_comp", "math_atoms", "computation_atoms", 
               ["DIM_COLLAPSE", "BOOLEAN_ALGEBRA"], ["DFA"]),
               
        # Composition: OMNI connects everything back to BLOCK_MATRIX
        Bridge("comp_to_math", "computation_atoms", "math_atoms", 
               ["OMNI"], ["BLOCK_MATRIX"])
    ]

    # 3. Initialize Unified Engine
    engine = UnifiedMatrixEngine(
        contexts={
            "computation_atoms": comp_ctx,
            "philosophy_atoms": phil_ctx,
            "math_atoms": math_ctx
        },
        bridges=bridges
    )

    # 4. Global Analysis
    print(f"📊 TKM MAP STATS:")
    for name in engine.contexts:
        print(f" - Context {name}: E(R) = {engine.get_information_energy(name):.4f}")

    # 5. Recursive Reachability Test (DFA Multi-hop)
    # Question: Does 'SENSE_STATUS' (Phil) eventually reach 'BLOCK_MATRIX' (Math) through 'COMPUTATION'?
    W_star = engine.recursive_bridge_routing(start_context="", steps=3)
    
    all_objs = []
    for c in engine.contexts:
        for o in engine.contexts[c].objects:
            all_objs.append(f"{c}:{o}")
    
    idx_sense = all_objs.index("philosophy_atoms:SENSE_STATUS")
    idx_block = all_objs.index("math_atoms:BLOCK_MATRIX")
    
    print(f"\n🔗 REACHABILITY CHECK:")
    print(f" - From SenseStatus to BlockMatrix: {'CONNECTED ✅' if W_star[idx_sense, idx_block] else 'DISCONNECTED ❌'}")

    # 6. Export Visualization
    from unified_engine import TKMVisualizer
    viz = TKMVisualizer(engine)
    viz.export_knowledge_tree("spec/tkm_atom_routing_tree.yaml")
    print(f"\n[VIZ] Exported Global Atom Map to spec/tkm_atom_routing_tree.yaml")

    assert W_star[idx_sense, idx_block] == True
    print("\n✅ TKM ATOM ROUTING MAP VALIDATED.")

if __name__ == "__main__":
    test_tkm_atom_routing_map()
