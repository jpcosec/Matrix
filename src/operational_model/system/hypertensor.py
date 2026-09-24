"""Assembling the block hypertensor from a live LogicalSystem.

`matrices.block_matrix.BlockMatrix` already implements the omnirepresentation
`WCi + Si + Vi` and `to_global_matrix()` folds it into one labelled matrix:

        contexts   facts
    ctx [  WCi   |  Si  ]
    sub [  Si^T  |  Vi  ]

What was missing is anybody building it from a real system. This module walks the
`Context` routing tree for `WCi` and stacks the routed worlds for `Si` and `Vi`.

Axis labels are prefixed with the owning `wigame_id` so two worlds that share a
symbol never collide in the global axes. The prefix is reversible, which is the
point: the hypertensor must not lose the indexing of symbols.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..core.route_target_kind import RouteTargetKind
from ..core.sense_value import SenseValue
from ..matrices.block_matrix import BlockMatrix
from ..matrices.boolean_matrix import BooleanMatrix
from ..matrices.si_matrix import SiMatrix
from ..matrices.vi_matrix import ViMatrix

if TYPE_CHECKING:
    from .logical_system import LogicalSystem

SEPARATOR = "::"


def qualify(wigame_id: str, symbol_id: str) -> str:
    """Returns the globally unique label for a symbol inside one world."""

    return f"{wigame_id}{SEPARATOR}{symbol_id}"


def unqualify(label: str) -> tuple[str, str]:
    """Splits a global label back into `(wigame_id, symbol_id)`."""

    wigame_id, separator, symbol_id = label.partition(SEPARATOR)
    if not separator:
        raise ValueError(f"label {label!r} is not qualified")
    return wigame_id, symbol_id


def routed_wigame_ids(system: "LogicalSystem", context_ids: list[str]) -> list[str]:
    """Returns the worlds reachable from the given contexts, in a stable order."""

    seen: set[str] = set()
    ordered: list[str] = []
    for context_id in context_ids:
        context = system.contexts.get(context_id)
        if context is None:
            continue
        for route in context.routes:
            if route.target_kind != RouteTargetKind.WIGAME:
                continue
            if route.target_id in seen or route.target_id not in system.wigames:
                continue
            seen.add(route.target_id)
            ordered.append(route.target_id)
    return ordered


def context_matrix(system: "LogicalSystem", context_ids: list[str]) -> BooleanMatrix:
    """Builds `WCi`: which context routes to which other context."""

    matrix = BooleanMatrix.filled(
        row_axis=list(context_ids), column_axis=list(context_ids), fill=False
    )
    for context_id in context_ids:
        context = system.contexts.get(context_id)
        if context is None:
            continue
        for route in context.routes:
            if route.target_kind != RouteTargetKind.CONTEXT:
                continue
            if route.target_id in context_ids:
                matrix.set(context_id, route.target_id, True)
    return matrix


def assemble_block_matrix(
    system: "LogicalSystem",
    context_ids: list[str] | None = None,
    wigame_ids: list[str] | None = None,
) -> BlockMatrix:
    """Assembles the block hypertensor for the routed part of `system`.

    `context_ids` defaults to every registered context, `wigame_ids` to the worlds
    those contexts route to, falling back to every world when no route exists.
    """

    contexts = sorted(system.contexts) if context_ids is None else list(context_ids)
    if wigame_ids is not None:
        worlds = list(wigame_ids)
    else:
        worlds = routed_wigame_ids(system, contexts) or sorted(system.wigames)

    subject_labels: list[str] = []
    object_labels: list[str] = []
    for wigame_id in worlds:
        wigame = system.wigames[wigame_id]
        subject_labels.extend(qualify(wigame_id, s) for s in wigame.axis_a)
        object_labels.extend(qualify(wigame_id, o) for o in wigame.axis_b)

    truth = ViMatrix.empty(subject_labels, object_labels)
    for wigame_id in worlds:
        wigame = system.wigames[wigame_id]
        for subject in wigame.axis_a:
            for obj in wigame.axis_b:
                truth.set(
                    qualify(wigame_id, subject),
                    qualify(wigame_id, obj),
                    wigame.Vi.get(subject, obj),
                )

    # Si in the block layout is context x facts: a context marks the object
    # columns of every world it routes to.
    sense = SiMatrix.pure(contexts, object_labels)
    for column in object_labels:
        for context_id in contexts:
            sense.set(context_id, column, SenseValue.UNSINNIG.value)
    for context_id in contexts:
        context = system.contexts.get(context_id)
        if context is None:
            continue
        for route in context.routes:
            if route.target_kind != RouteTargetKind.WIGAME:
                continue
            if route.target_id not in worlds:
                continue
            wigame = system.wigames[route.target_id]
            for obj in wigame.axis_b:
                sense.set(context_id, qualify(route.target_id, obj), SenseValue.SINNVOLL.value)

    return BlockMatrix(
        context_matrix=context_matrix(system, contexts),
        sense_matrix=sense,
        truth_matrix=truth,
    )


def assemble_global_matrix(
    system: "LogicalSystem",
    context_ids: list[str] | None = None,
    wigame_ids: list[str] | None = None,
) -> BooleanMatrix:
    """Returns the single global matrix for the routed part of `system`."""

    return assemble_block_matrix(system, context_ids, wigame_ids).to_global_matrix()
