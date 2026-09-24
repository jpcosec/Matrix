"""Deciding where to cut the hypertensor into closed worlds.

`information_energy()` and `tautological_columns()` were computed and then read by
nobody: the only consumer was `tools/kb/capabilities.py`, which asserts that the
energy is a float. This module turns them into a decision.

The measured result that shapes the criterion, for `grosor_hoja` against
`tiene_parte` + `grosor` over three plants:

    composite    r=grosor_hoja  3x2,  6 cells, E=0.7500, taut=[]
    decomposed   r=tiene_parte  3x2,  6 cells, E=0.6250, taut=['hoja']
                 r=grosor       2x2,  4 cells, E=0.6250, taut=[]

The composite wins there, on both energy and cells. So the rule is not "minimise
entropy": splitting introduces a tautological column (every plant has a leaf), and
that costs discriminative power. What makes the split pay off is **reuse of the
middle term**: the composite grows as `subjects x values`, while the split grows
as `subjects x 1` plus a constant `middle x values`. With three plants that does
not amortise; with three hundred it does.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Sequence

if TYPE_CHECKING:
    from .wigame import WiGame


@dataclass(frozen=True)
class WiGameScore:
    """Measured shape of one world."""

    wigame_id: str
    subjects: int
    objects: int
    cells: int
    facts: int
    density: float
    energy: float
    tautological_columns: tuple[str, ...]
    discriminative_power: float


def score_wigame(wigame: "WiGame") -> WiGameScore:
    """Measures one world: size, density, energy and discriminative power."""

    subjects = len(wigame.axis_a)
    objects = len(wigame.axis_b)
    cells = subjects * objects
    taut = tuple(wigame.tautological_columns())
    discriminative = (objects - len(taut)) / objects if objects else 0.0
    return WiGameScore(
        wigame_id=wigame.wigame_id,
        subjects=subjects,
        objects=objects,
        cells=cells,
        facts=len(wigame.facts),
        density=(len(wigame.facts) / cells) if cells else 0.0,
        energy=wigame.information_energy(),
        tautological_columns=taut,
        discriminative_power=discriminative,
    )


@dataclass(frozen=True)
class PartitionVerdict:
    """The decision between keeping one world or splitting it."""

    choice: str  # "composite" | "decomposed"
    reason: str
    metric: str
    composite: WiGameScore
    parts: tuple[WiGameScore, ...]
    composite_cells: int
    decomposed_cells: int
    reuse: int

    @property
    def splits(self) -> bool:
        """Reports whether the verdict favours splitting."""

        return self.choice == "decomposed"


def middle_term_reuse(parts: Sequence["WiGame"]) -> int:
    """Counts how many subjects funnel through the shared middle term.

    The middle term is the object axis of the first part that is also the subject
    axis of the second. Its reuse is what a split amortises.
    """

    if len(parts) < 2:
        return 0
    shared = [o for o in parts[0].axis_b if o in set(parts[1].axis_a)]
    if not shared:
        return 0
    return len(parts[0].axis_a)


def compare_partition(
    composite: "WiGame",
    parts: Sequence["WiGame"],
) -> PartitionVerdict:
    """Decides whether `composite` is better kept whole or split into `parts`.

    Cells are the cost, discriminative power is the quality, and reuse of the
    middle term is what makes the cost scale sublinearly. A split is chosen when
    it costs no more cells than the composite, or when the reuse of the middle
    term is large enough that the split's growth term is the smaller one.
    """

    composite_score = score_wigame(composite)
    part_scores = tuple(score_wigame(p) for p in parts)
    decomposed_cells = sum(s.cells for s in part_scores)
    reuse = middle_term_reuse(parts)

    # Growth per additional subject: the composite adds one row of `objects`
    # cells, the split adds one row of the (much narrower) middle axis.
    composite_growth = composite_score.objects
    split_growth = part_scores[0].objects if part_scores else composite_growth

    if decomposed_cells <= composite_score.cells:
        return PartitionVerdict(
            choice="decomposed",
            reason=(
                f"splitting costs {decomposed_cells} cells against "
                f"{composite_score.cells}, so it is cheaper outright"
            ),
            metric="cells",
            composite=composite_score,
            parts=part_scores,
            composite_cells=composite_score.cells,
            decomposed_cells=decomposed_cells,
            reuse=reuse,
        )

    if split_growth < composite_growth and reuse > decomposed_cells - composite_score.cells:
        return PartitionVerdict(
            choice="decomposed",
            reason=(
                f"{reuse} subjects reuse the middle term and each new subject costs "
                f"{split_growth} cells instead of {composite_growth}, which amortises "
                f"the {decomposed_cells - composite_score.cells} extra cells"
            ),
            metric="middle_term_reuse",
            composite=composite_score,
            parts=part_scores,
            composite_cells=composite_score.cells,
            decomposed_cells=decomposed_cells,
            reuse=reuse,
        )

    lost = sum(len(s.tautological_columns) for s in part_scores)
    return PartitionVerdict(
        choice="composite",
        reason=(
            f"splitting costs {decomposed_cells} cells against {composite_score.cells} "
            f"and introduces {lost} tautological column(s), lowering discriminative "
            f"power without enough reuse ({reuse}) to pay for it"
        ),
        metric="discriminative_power",
        composite=composite_score,
        parts=part_scores,
        composite_cells=composite_score.cells,
        decomposed_cells=decomposed_cells,
        reuse=reuse,
    )
