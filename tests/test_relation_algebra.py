import pytest
from src.operational_model import (
    Fact,
    LiSpace,
    LogicalSystem,
    Proposition,
    Relation,
    TruthValue,
    WiGame,
    Symbol,
    Name,
    Thing
)

def test_commutative_relation_behavior() -> None:
    system = LogicalSystem()
    
    # Register things
    for thing in (
        Thing(Symbol("a"), Name("A")),
        Thing(Symbol("b"), Name("B")),
    ):
        system.register_thing(thing)
    
    # Register a commutative relation
    rel = Relation("linked", "is linked to", commutative=True)
    system.register_relation(rel)
    
    # Create a WiGame where a and b can be both subject and object
    wigame = WiGame(
        wigame_id="wigame:links",
        li=LiSpace(
            li_id="li:links",
            axis_a=["a", "b"],
            axis_b=["a", "b"],
            relation_id="linked",
        ),
    )
    system.register_wigame(wigame)
    
    # Add a fact (linked a b)
    fact = Fact(
        Proposition("linked", "a", "b", "wigame:links"),
        TruthValue.TRUE
    )
    system.add_fact(fact)
    
    # Verify (linked b a) is also TRUE due to commutativity
    status_b_a = wigame.get_status("b", "a")
    assert status_b_a["truth_label"] == "TRUE"

def test_transitive_relation_behavior() -> None:
    system = LogicalSystem()
    
    for thing in (
        Thing(Symbol("a"), Name("A")),
        Thing(Symbol("b"), Name("B")),
        Thing(Symbol("c"), Name("C")),
    ):
        system.register_thing(thing)
        
    rel = Relation("over", "is over", transitive=True)
    system.register_relation(rel)
    
    wigame = WiGame(
        wigame_id="wigame:stack",
        li=LiSpace(
            li_id="li:stack",
            axis_a=["a", "b", "c"],
            axis_b=["a", "b", "c"],
            relation_id="over",
        ),
    )
    system.register_wigame(wigame)
    
    # (over a b)
    system.add_fact(Fact(Proposition("over", "a", "b", "wigame:stack"), TruthValue.TRUE))
    # (over b c)
    system.add_fact(Fact(Proposition("over", "b", "c", "wigame:stack"), TruthValue.TRUE))
    
    # Verify (over a c) is TRUE due to transitivity
    status_a_c = wigame.get_status("a", "c")
    assert status_a_c["truth_label"] == "TRUE"
