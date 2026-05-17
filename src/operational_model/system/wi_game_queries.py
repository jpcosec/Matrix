"""Query helpers for WiGame evaluation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..core.sense_value import SenseValue
from ..core.truth_value import TruthValue
from ..routing.search_vector import SearchVector

if TYPE_CHECKING:
    from .wigame import WiGame


def search(wigame: "WiGame", search_vector: SearchVector) -> list[str]:
    """Searches a WiGame using `Vi` filtered by `Si`."""

    _validate_search_vector(wigame, search_vector)
    requested_terms = search_vector.active_terms(wigame.axis_b)
    candidates = wigame.Vi.subjects_matching(search_vector)
    return [
        subject_symbol_id
        for subject_symbol_id in candidates
        if _terms_are_meaningful(wigame, subject_symbol_id, requested_terms)
    ]


def tautological_columns(wigame: "WiGame") -> list[str]:
    """Returns non-discriminating truth columns for a WiGame."""

    return wigame.Vi.tautological_columns()


def is_pure(wigame: "WiGame") -> bool:
    """Reports whether the WiGame contains no `unsinnig` sense values."""

    return wigame.Si.is_pure()


def _validate_search_vector(wigame: "WiGame", search_vector: SearchVector) -> None:
    """Ensures the query vector belongs to the requested WiGame."""

    if search_vector.wigame_id != wigame.wigame_id:
        raise ValueError("search vector belongs to a different WiGame")


def information_energy(wigame: "WiGame") -> float:
    Vi, Si = wigame.Vi, wigame.Si
    n, m = len(Vi.row_axis), len(Vi.column_axis)
    total = n * m
    if total == 0:
        return 0.0

    sinnvoll_values = {SenseValue.SINNVOLL.value, SenseValue.SINNLOS.value}
    c = (
        sum(
            1
            for row_key in Si.row_axis
            for val in Si.row(row_key).values()
            if val in sinnvoll_values
        )
        / total
    )

    i = (
        sum(
            1
            for row_key in Vi.row_axis
            for col_key in Vi.column_axis
            if Vi.get(row_key, col_key) == TruthValue.TRUE.value
            and Si.get(row_key, col_key) != SenseValue.UNSINNIG.value
        )
        / total
    )

    o = len(wigame.facts) / total

    taut = len(wigame.Vi.tautological_columns())
    d = (m - taut) / m if m > 0 else 0.0

    return 0.25 * (c + i + o + d)


def _terms_are_meaningful(
    wigame: "WiGame",
    subject_symbol_id: str,
    requested_terms: list[str],
) -> bool:
    """Checks whether all requested terms are meaningful for one subject."""

    return all(
        wigame.Si.get(subject_symbol_id, term) != SenseValue.UNSINNIG.value
        for term in requested_terms
    )
