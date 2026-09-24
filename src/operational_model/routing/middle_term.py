"""Object-to-subject composition across the middle term shared by two WiGames.

`RoutingProjection` joins subject axis to subject axis. The join that actually
chains two worlds is the **middle term**: a symbol that is an *object* of the
first world and a *subject* of the second one.

    (debe legumbre guisarse)    W1: axis_a=[legumbre]  axis_b=[guisarse]
    (necesita guisarse fuego)   W2: axis_a=[guisarse]  axis_b=[fuego]

`guisarse` is the middle term, and composing across it yields
`(legumbre, guisarse, fuego)`. This works where
`core.transitive_inference` cannot: that one filters by `relation_id`, so two
different relations never chain.

A leg only holds when its cell is TRUE in `Vi` **and** `sinnvoll` in `Si`. A leg
that is true but senseless breaks the chain, so sense is a gate on routing and
not an afterthought.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..core.sense_value import SenseValue
from ..core.truth_value import TruthValue

if TYPE_CHECKING:
    from ..system.wigame import WiGame


def middle_terms(w1: "WiGame", w2: "WiGame") -> list[str]:
    """Returns the symbols that are objects of `w1` and subjects of `w2`."""

    targets = set(w2.axis_a)
    seen: set[str] = set()
    shared: list[str] = []
    for symbol_id in w1.axis_b:
        if symbol_id in targets and symbol_id not in seen:
            seen.add(symbol_id)
            shared.append(symbol_id)
    return shared


def _leg_holds(wigame: "WiGame", subject_symbol_id: str, object_symbol_id: str) -> bool:
    """Reports whether one leg is both true and meaningful."""

    if subject_symbol_id not in wigame.Vi.row_axis:
        return False
    if object_symbol_id not in wigame.Vi.column_axis:
        return False
    truth = wigame.Vi.get(subject_symbol_id, object_symbol_id)
    if truth != TruthValue.TRUE.value:
        return False
    sense = wigame.Si.get(subject_symbol_id, object_symbol_id)
    return sense == SenseValue.SINNVOLL.value


def compose(w1: "WiGame", w2: "WiGame") -> list[tuple[str, str, str]]:
    """Composes `w1` and `w2` through every shared middle term.

    Returns `(subject_of_w1, middle_term, object_of_w2)` triples for which both
    legs are TRUE and `sinnvoll`. The middle term stays explicit so the route
    remains auditable. No symbol and no relation is created.
    """

    shared = middle_terms(w1, w2)
    if not shared:
        return []

    composed: list[tuple[str, str, str]] = []
    for subject_symbol_id in w1.axis_a:
        for middle_symbol_id in shared:
            if not _leg_holds(w1, subject_symbol_id, middle_symbol_id):
                continue
            for object_symbol_id in w2.axis_b:
                if _leg_holds(w2, middle_symbol_id, object_symbol_id):
                    composed.append(
                        (subject_symbol_id, middle_symbol_id, object_symbol_id)
                    )
    return composed


def compose_pairs(w1: "WiGame", w2: "WiGame") -> list[tuple[str, str]]:
    """Returns `compose` reduced to `(subject_of_w1, object_of_w2)` pairs."""

    seen: set[tuple[str, str]] = set()
    pairs: list[tuple[str, str]] = []
    for subject_symbol_id, _middle, object_symbol_id in compose(w1, w2):
        pair = (subject_symbol_id, object_symbol_id)
        if pair not in seen:
            seen.add(pair)
            pairs.append(pair)
    return pairs
