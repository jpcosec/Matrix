"""Shape diagnosis for a WiGame: rejecting degenerate, over-wide worlds.

The widest world you can build is the one with a wildcard relation whose objects
swallow the relation itself:

    (* pedrito es_hermano_de_maria)

Measured, that world scores worse than the factored one while costing twice the
cells (E=0.5278 over 18 cells against E=0.5556 over 9). The problem is not the
score though, it is the *shape*: `es_hermano_de_maria` packs a relation and an
object into a single symbol, so `maria` stops being indexable. You can no longer
ask who Pedrito is a brother of, because the answer is inside a string.

`information_energy` measures a world. This module judges its form.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .logical_system import LogicalSystem
    from .wigame import WiGame

#: Relation ids that assert nothing: any proposition would be admissible.
WILDCARD_RELATION_IDS = frozenset({"*", "", "_", "any", "rel", "relation"})

#: Infixes that betray an object holding more than one fact.
CONJUNCTIVE_MARKERS = ("_y_", "_and_", "_e_", "+")

SEVERITY_ERROR = "error"
SEVERITY_WARNING = "warning"


@dataclass(frozen=True)
class ShapeFinding:
    """One diagnosed defect in the shape of a WiGame."""

    kind: str
    severity: str
    subject: str
    explanation: str
    details: dict[str, Any] = field(default_factory=dict)


def _wildcard_relation(wigame: "WiGame") -> list[ShapeFinding]:
    """Flags a relation id that constrains nothing."""

    relation_id = wigame.relation_id
    if relation_id.strip().lower() not in WILDCARD_RELATION_IDS:
        return []
    return [
        ShapeFinding(
            kind="wildcard_relation",
            severity=SEVERITY_ERROR,
            subject=relation_id,
            explanation=(
                f"relation id {relation_id!r} admits any proposition, so the world "
                "states no move shape and cannot discriminate"
            ),
            details={"relation_id": relation_id},
        )
    ]


def _packed_objects(wigame: "WiGame", known_symbols: set[str]) -> list[ShapeFinding]:
    """Flags axis labels that embed another registered symbol."""

    findings: list[ShapeFinding] = []
    for label in wigame.axis_b:
        embedded = sorted(
            symbol_id
            for symbol_id in known_symbols
            if symbol_id != label
            and len(symbol_id) > 1
            and re.search(rf"(?:^|_){re.escape(symbol_id)}(?:_|$)", label)
        )
        if not embedded:
            continue
        findings.append(
            ShapeFinding(
                kind="packed_object",
                severity=SEVERITY_ERROR,
                subject=label,
                explanation=(
                    f"object {label!r} embeds the registered symbol(s) "
                    f"{', '.join(embedded)}; that argument is trapped in a string "
                    "and is no longer indexable"
                ),
                details={"embedded": embedded},
            )
        )
    return findings


def _conjunctive_objects(wigame: "WiGame") -> list[ShapeFinding]:
    """Flags axis labels that pack more than one fact into one cell."""

    findings: list[ShapeFinding] = []
    for label in wigame.axis_b:
        marker = next((m for m in CONJUNCTIVE_MARKERS if m in label), None)
        if marker is None:
            continue
        findings.append(
            ShapeFinding(
                kind="conjunctive_object",
                severity=SEVERITY_WARNING,
                subject=label,
                explanation=(
                    f"object {label!r} joins several claims on {marker!r}; one cell "
                    "should carry one fact"
                ),
                details={"marker": marker},
            )
        )
    return findings


def _non_discriminative_columns(wigame: "WiGame") -> list[ShapeFinding]:
    """Flags columns that hold for every subject and so separate nothing."""

    return [
        ShapeFinding(
            kind="non_discriminative_column",
            severity=SEVERITY_WARNING,
            subject=column,
            explanation=(
                f"column {column!r} is tautological: it holds for every subject and "
                "adds no discriminative power (D_i)"
            ),
            details={},
        )
        for column in wigame.tautological_columns()
    ]


def _sparsity(wigame: "WiGame", min_density: float) -> list[ShapeFinding]:
    """Flags a world whose cells are almost all empty."""

    cells = len(wigame.axis_a) * len(wigame.axis_b)
    if cells == 0:
        return []
    density = len(wigame.facts) / cells
    if density >= min_density:
        return []
    return [
        ShapeFinding(
            kind="sparse_world",
            severity=SEVERITY_WARNING,
            subject=wigame.wigame_id,
            explanation=(
                f"only {len(wigame.facts)} fact(s) over {cells} cells "
                f"(density {density:.4f} < {min_density}); the axes are wider than "
                "the knowledge in them"
            ),
            details={"facts": len(wigame.facts), "cells": cells, "density": density},
        )
    ]


def diagnose_shape(
    wigame: "WiGame",
    system: "LogicalSystem" | None = None,
    *,
    min_density: float = 0.1,
) -> list[ShapeFinding]:
    """Diagnoses the form of one WiGame.

    Passing `system` enables packed-object detection, which needs the registry of
    known symbols to tell `es_hermano_de_maria` from an ordinary label.
    """

    known_symbols = set(system.things) if system is not None else set()
    findings: list[ShapeFinding] = []
    findings.extend(_wildcard_relation(wigame))
    if known_symbols:
        findings.extend(_packed_objects(wigame, known_symbols))
    findings.extend(_conjunctive_objects(wigame))
    findings.extend(_non_discriminative_columns(wigame))
    findings.extend(_sparsity(wigame, min_density))
    return findings


def is_well_shaped(
    wigame: "WiGame",
    system: "LogicalSystem" | None = None,
    *,
    min_density: float = 0.1,
) -> bool:
    """Reports whether the world carries no `error` level finding."""

    return not any(
        finding.severity == SEVERITY_ERROR
        for finding in diagnose_shape(wigame, system, min_density=min_density)
    )
