"""Focused tests for status evaluation migrated from legacy runtime."""

from src.operational_model.core.fact import Fact
from src.operational_model.core.li_space import LiSpace
from src.operational_model.core.proposition import Proposition
from src.operational_model.core.sense_value import SenseValue
from src.operational_model.core.truth_value import TruthValue
from src.operational_model.system.wigame import WiGame


def _make_wigame(subjects, terms, relation="R"):
    li = LiSpace(
        li_id="li1", axis_a=list(subjects), axis_b=list(terms), relation_id=relation
    )
    return WiGame(wigame_id="wg1", li=li)


def test_status_sinnvoll():
    wg = _make_wigame(["a1", "a2"], ["p1", "p2"])
    prop = Proposition(
        relation_id="R", subject_symbol_id="a1", object_symbol_id="p1", wigame_id="wg1"
    )
    fact = Fact(proposition=prop, truth=TruthValue.TRUE)
    wg.add_fact(fact, sense=SenseValue.SINNVOLL)
    status = wg.get_status("a1", "p1")
    assert status.status == "sinnvoll"
    assert status.truth == TruthValue.TRUE.value
    assert status.applicable is True


def test_status_sinnlos_tautology():
    wg = _make_wigame(["a1", "a2"], ["p1"])
    prop1 = Proposition(
        relation_id="R", subject_symbol_id="a1", object_symbol_id="p1", wigame_id="wg1"
    )
    prop2 = Proposition(
        relation_id="R", subject_symbol_id="a2", object_symbol_id="p1", wigame_id="wg1"
    )
    wg.add_fact(
        Fact(proposition=prop1, truth=TruthValue.TRUE), sense=SenseValue.SINNVOLL
    )
    wg.add_fact(
        Fact(proposition=prop2, truth=TruthValue.TRUE), sense=SenseValue.SINNVOLL
    )
    status = wg.get_status("a1", "p1")
    assert status.status == "sinnlos"
    assert status.discriminative is False


def test_status_unsinnig():
    wg = _make_wigame(["a1"], ["p1"])
    wg.set_sense("a1", "p1", SenseValue.UNSINNIG)
    status = wg.get_status("a1", "p1")
    assert status.status == "unsinnig"
    assert status.applicable is False


def test_status_missing_coordinate():
    wg = _make_wigame(["a1"], ["p1"])
    status = wg.get_status("a1", "nonexistent")
    assert status.status == "unsinnig"
    assert status.applicable is False
