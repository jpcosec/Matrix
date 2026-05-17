"""Registration helpers for WiGame proposition and fact updates."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..core.fact import Fact
from ..core.proposition import Proposition
from ..core.sense_value import SenseValue
from ..matrices.si_matrix import SiMatrix
from ..matrices.vi_matrix import ViMatrix


if TYPE_CHECKING:
    from .wigame import WiGame


def initialize_vi(wigame: "WiGame") -> ViMatrix:
    """Builds the default truth matrix for a WiGame."""

    return ViMatrix.empty(wigame.li.axis_a, wigame.li.axis_b)


def initialize_si(wigame: "WiGame") -> SiMatrix:
    """Builds the default sense matrix for a WiGame."""

    return SiMatrix.pure(wigame.li.axis_a, wigame.li.axis_b)


def accepts_proposition(wigame: "WiGame", proposition: Proposition) -> bool:
    """Checks whether a proposition belongs to the target WiGame."""

    return proposition.wigame_id == wigame.wigame_id and wigame.li.accepts(proposition)


def register_proposition(
    wigame: "WiGame",
    proposition: Proposition,
    sense: SenseValue | None = None,
) -> None:
    """Registers a proposition and updates the sense matrix."""

    wigame.propositions[proposition.proposition_id] = proposition
    if not wigame.li.accepts(proposition):
        _mark_unsinnig_if_addressable(wigame, proposition)
        return
    wigame.Si.set(
        proposition.subject_symbol_id,
        proposition.object_symbol_id,
        (sense or SenseValue.SINNLOS).value,
    )


def add_fact(
    wigame: "WiGame",
    fact: Fact,
    sense: SenseValue = SenseValue.SINNVOLL,
) -> None:
    """Registers a fact and writes its truth into the WiGame matrices."""

    proposition = fact.proposition
    if not accepts_proposition(wigame, proposition):
        raise ValueError("fact proposition does not fit this WiGame")
    register_proposition(wigame, proposition, sense=sense)
    wigame.facts[fact.fact_id] = fact
    wigame.Vi.set(
        proposition.subject_symbol_id,
        proposition.object_symbol_id,
        fact.truth.value,
    )


def set_sense(
    wigame: "WiGame",
    subject_symbol_id: str,
    object_symbol_id: str,
    sense: SenseValue,
) -> None:
    """Overrides one sense value inside the WiGame."""

    wigame.Si.set(subject_symbol_id, object_symbol_id, sense.value)


def _mark_unsinnig_if_addressable(wigame: "WiGame", proposition: Proposition) -> None:
    """Marks invalid but addressable propositions as `unsinnig`."""

    if (
        proposition.subject_symbol_id in wigame.axis_a
        and proposition.object_symbol_id in wigame.axis_b
    ):
        wigame.Si.set(
            proposition.subject_symbol_id,
            proposition.object_symbol_id,
            SenseValue.UNSINNIG.value,
        )
