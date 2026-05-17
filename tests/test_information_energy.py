"""Focused tests for information energy migrated from legacy runtime."""

from src.operational_model.core.fact import Fact
from src.operational_model.core.li_space import LiSpace
from src.operational_model.core.proposition import Proposition
from src.operational_model.core.sense_value import SenseValue
from src.operational_model.core.truth_value import TruthValue
from src.operational_model.system.wigame import WiGame


def test_information_energy_default():
    li = LiSpace(li_id="li1", axis_a=["a"], axis_b=["p"], relation_id="R")
    wg = WiGame(wigame_id="wg1", li=li)
    e = wg.information_energy()
    assert 0.0 < e <= 1.0


def test_information_energy_full():
    li = LiSpace(li_id="li1", axis_a=["a"], axis_b=["p"], relation_id="R")
    wg = WiGame(wigame_id="wg1", li=li)
    prop = Proposition(
        relation_id="R",
        subject_symbol_id="a",
        object_symbol_id="p",
        wigame_id="wg1",
    )
    fact = Fact(proposition=prop, truth=TruthValue.TRUE)
    wg.add_fact(fact, sense=SenseValue.SINNVOLL)
    e = wg.information_energy()
    assert 0.0 < e <= 1.0


def test_information_energy_partial():
    li = LiSpace(
        li_id="li1",
        axis_a=["a1", "a2"],
        axis_b=["p1", "p2"],
        relation_id="R",
    )
    wg = WiGame(wigame_id="wg1", li=li)
    prop = Proposition(
        relation_id="R",
        subject_symbol_id="a1",
        object_symbol_id="p1",
        wigame_id="wg1",
    )
    fact = Fact(proposition=prop, truth=TruthValue.TRUE)
    wg.add_fact(fact, sense=SenseValue.SINNVOLL)
    e = wg.information_energy()
    assert 0.0 < e < 1.0
