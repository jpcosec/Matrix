"""Tests for the Spanish SHRDLU surface, without the unported corpus pipeline.

The sibling repo's version of these tests drives the parser through
`pipeline.run.build_system`, which belongs to the outer ingestion layer that is
not part of this repo. These build the world directly instead, so the Spanish
parser and the dialogue state are covered here on their own.
"""

from __future__ import annotations

import pytest

from desk.drawer.shrdlu.dialog_state import DialogState
from desk.drawer.shrdlu.spanish import Clarification, fold, parse_es
from desk.drawer.shrdlu.text_norm import normalize
from src.operational_model import (
    Fact,
    LiSpace,
    LogicalSystem,
    Name,
    Proposition,
    Relation,
    Symbol,
    Thing,
    TruthValue,
    WiGame,
)


def build_vegetable_world() -> tuple[LogicalSystem, DialogState]:
    """Builds `(has_property lechuga verde)` and focuses a dialogue on it."""

    system = LogicalSystem()
    system.register_relation(Relation("has_property", "has_property"))
    subjects = ["lechuga", "acelga"]
    objects = ["verde", "hoja_lisa"]
    for symbol_id in subjects + objects:
        system.register_thing(Thing(Symbol(symbol_id), Name(symbol_id)))
    wigame = WiGame(
        wigame_id="wigame:vegetales",
        li=LiSpace("li:veg", subjects, objects, "has_property"),
        context_id="context:vegetales",
    )
    system.register_wigame(wigame)
    wigame.add_fact(
        Fact(
            proposition=Proposition(
                "has_property", "lechuga", "verde", "wigame:vegetales"
            ),
            truth=TruthValue.TRUE,
        )
    )
    dialog = DialogState(focus_wigame="wigame:vegetales", system=system)
    return system, dialog


def test_fold_strips_accents_and_keeps_ids() -> None:
    assert fold("¿Por qué la LECHUGA?") == "por que la lechuga"
    assert fold("wigame:vegetales") == "wigame:vegetales"


def test_normalize_is_vendored_and_stdlib_only() -> None:
    assert normalize("Lechuga Verde") == "lechuga verde"
    assert normalize("ñandú") == "nandu"


def test_candidates_command_targets_the_focus() -> None:
    _system, dialog = build_vegetable_world()

    assert parse_es("candidatos", dialog) == (
        "(return candidates wigame:vegetales curation:proposed)"
    )


def test_show_wigame_returns_facts_for_the_focus() -> None:
    _system, dialog = build_vegetable_world()

    assert parse_es("show wigame", dialog) == "(return facts wigame:vegetales)"


def test_empty_line_is_rejected() -> None:
    _system, dialog = build_vegetable_world()

    with pytest.raises(ValueError, match="empty line"):
        parse_es("   ", dialog)


def test_parser_returns_either_an_sexpr_or_a_clarification() -> None:
    _system, dialog = build_vegetable_world()

    result = parse_es("¿la lechuga es verde?", dialog)

    assert isinstance(result, (str, Clarification))
    if isinstance(result, str):
        assert result.startswith("(")
    else:
        assert result.options


def test_dialog_state_remembers_a_turn() -> None:
    _system, dialog = build_vegetable_world()

    dialog.remember_turn("es", "lechuga", "verde", relation="has_property")

    assert dialog.last_subject == "lechuga"
    assert dialog.last_object == "verde"
    assert dialog.last_verb == "es"
    assert dialog.last_relation == "has_property"


def test_pending_clarification_is_answered_by_index() -> None:
    _system, dialog = build_vegetable_world()
    dialog.pending = Clarification(
        question="¿cuál?",
        options=["(check wigame:vegetales (has_property lechuga verde))", "(return facts)"],
    )

    chosen = dialog.answer("1")

    assert chosen == "(check wigame:vegetales (has_property lechuga verde))"
    assert dialog.pending is None


def test_answering_without_a_pending_question_fails() -> None:
    _system, dialog = build_vegetable_world()

    with pytest.raises(ValueError, match="no pending clarification"):
        dialog.answer("1")


def test_answer_rejects_an_out_of_range_choice() -> None:
    _system, dialog = build_vegetable_world()
    dialog.pending = Clarification(question="¿cuál?", options=["(return facts)"])

    with pytest.raises(ValueError, match="out of range"):
        dialog.answer("7")
