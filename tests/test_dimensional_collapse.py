import jax.numpy as jnp
from unified_engine import UnifiedMatrixEngine, Context, Bridge

def test_dimensional_collapse():
    # Setup a system with two contexts and a bridge
    # Context A: [O1, O2] x [P1, P2]
    # Context B: [O3, O4] x [P3, P4]
    
    ctx_a = Context(
        name="A",
        objects=["O1", "O2"],
        properties=["P1", "P2"],
        objects_meta={}, properties_meta={},
        truths={"O1": {"P1": True}, "O2": {"P1": True}} # O1 and O2 share P1
    )
    
    ctx_b = Context(
        name="B",
        objects=["O3", "O4"],
        properties=["P3", "P4"],
        objects_meta={}, properties_meta={},
        truths={"O3": {"P3": True}, "O4": {"P4": True}}
    )
    
    # Bridge: O2 (A) -> O3 (B)
    bridge = Bridge(name="AtoB", from_context="A", to_context="B", 
                    from_objects=["O2"], to_objects=["O3"])
    
    engine = UnifiedMatrixEngine(contexts={"A": ctx_a, "B": ctx_b}, bridges=[bridge])
    
    # 1. Test Single Context Collapse (Similarity Matrix)
    W_a = engine.dimensional_collapse("A")
    # O1 and O2 share P1, so they should be connected
    assert W_a[0, 1] == True
    assert W_a[1, 0] == True
    print("[TEST] Context A collapse successful (O1-O2 connected via P1)")
    
    # 2. Test Recursive Bridge Routing (Multi-hop)
    # Path: O1 -> (P1) -> O2 -> (Bridge) -> O3 -> (P3) -> O4
    W_star = engine.recursive_bridge_routing(start_context="A", steps=2)
    
    # Check if O1 can reach O4
    # Indices: O1=0, O2=1, O3=2, O4=3
    assert W_star[0, 3] == True
    print("[TEST] Recursive routing successful (O1 reached O4 across contexts)")
    
    # 3. Test Inference Plane
    plane = engine.get_collapsed_inference_plane()
    assert len(plane["labels"]) == 4
    assert plane["labels"][0] == "A.O1"
    assert plane["labels"][3] == "B.O4"
    
    print("\n✅ DIMENSIONAL COLLAPSE & RECURSIVE ROUTING VALIDATED.")

if __name__ == "__main__":
    test_dimensional_collapse()
