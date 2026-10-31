"""Query helpers for WiGame evaluation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..core.sense_value import SenseValue
from ..core.truth_value import TruthValue
from ..routing.search_vector import SearchVector
from .operation_results import StatusResult

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


def get_status(wigame: "WiGame", subject: str, term: str) -> StatusResult:
    """Returns the semantic and truth status of a proposition slot."""
    if subject not in wigame.Vi.row_axis or term not in wigame.Vi.column_axis:
        return StatusResult("unsinnig", None, False, reason="Out of bounds")
    sense = wigame.Si.get(subject, term)
    truth = wigame.Vi.get(subject, term)
    if sense == SenseValue.UNSINNIG.value:
        return StatusResult("unsinnig", truth, False, reason="Sense violation")
    taut = term in wigame.Vi.tautological_columns()
    return StatusResult(
        status="sinnlos" if taut else "sinnvoll",
        truth=truth,
        applicable=True,
        discriminative=not taut,
    )


def information_energy(wigame: "WiGame") -> float:
    """Returns the information energy of this WiGame."""
    Vi, Si = wigame.Vi, wigame.Si
    total = len(Vi.row_axis) * len(Vi.column_axis)
    if total == 0:
        return 0.0
    c = _count_sinnvoll(Si) / total
    i = _count_true_facts(Vi, Si) / total
    o = len(wigame.facts) / total
    m = len(Vi.column_axis)
    d = (m - len(Vi.tautological_columns())) / m if m > 0 else 0.0
    return 0.25 * (c + i + o + d)


def _validate_search_vector(wigame: "WiGame", search_vector: SearchVector) -> None:
    """Ensures the query vector belongs to the requested WiGame."""

    if search_vector.wigame_id != wigame.wigame_id:
        raise ValueError("search vector belongs to a different WiGame")


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


def _count_sinnvoll(Si: Any) -> int:
    """Counts meaningful cells in the sense matrix."""
    sinnvoll_values = {SenseValue.SINNVOLL.value, SenseValue.SINNLOS.value}
    return sum(
        1
        for r in Si.row_axis
        for val in Si.row(r).values()
        if val in sinnvoll_values
    )


def _count_true_facts(Vi: Any, Si: Any) -> int:
    """Counts true and meaningful cells."""
    return sum(
        1
        for r in Vi.row_axis
        for c in Vi.column_axis
        if Vi.get(r, c) == TruthValue.TRUE.value
        and Si.get(r, c) != SenseValue.UNSINNIG.value
    )
