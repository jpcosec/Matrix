"""Tests for the controlled-Spanish parser of the SHRDLU REPL."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.append(str(_REPO_ROOT))

from pipeline.run import build_system

from prototypes.shrdlu.dialog_state import DialogState
from prototypes.shrdlu.spanish import Clarification, parse_es

CORPUS = str(_REPO_ROOT / "corpus" / "vegetales")


@pytest.fixture(scope="module")
def dialog():
    system, _, _ = build_system(CORPUS, "vegetales")
    return DialogState(focus_wigame="wigame:vegetales", system=system)


def mini_dialog() -> DialogState:
    """Dialog over a tiny one-context world, so every sign resolves once."""

    from src.operational_model import LogicalSystem, SExpressionRuntime

    system = LogicalSystem()
    runtime = SExpressionRuntime(system)
    runtime.evaluate("(create relation has_property has_property)")
    for name in ("x", "y", "z", "w"):
        runtime.evaluate(f"(create symbol {name}@c {name})")
    runtime.evaluate("(create li li:c has_property (axis-a x@c) (axis-b y@c z@c w@c))")
    runtime.evaluate("(create wigame wigame:c:has_property li:c)")
    return DialogState(focus_wigame="wigame:c:has_property", system=system)


def test_single_option_question_resolves(dialog):
    assert parse_es("¿la lechuga tiene hoja_lisa?", dialog) == (
        "(ask has_property lechuga@01_lechugas hoja_lisa@01_lechugas)"
    )


def test_ambiguous_sign_returns_clarification(dialog):
    parsed = parse_es("¿la lechuga tiene hoja?", dialog)

    assert isinstance(parsed, Clarification)
    assert len(parsed.options) == 3
    assert parsed.options[0] == "(ask has_property lechuga@01_lechugas hoja@01_lechugas)"
    assert "1)" in parsed.question


def test_answer_resolves_pending_clarification(dialog):
    dialog.pending = Clarification(question="?", options=["(ask has_property x@c y@c)"])
    resolved = dialog.answer("1")

    assert resolved == "(ask has_property x@c y@c)"
    assert dialog.pending is None


def test_assert_and_why_patterns():
    dialog = mini_dialog()

    assert parse_es("x tiene y", dialog) == "(assert wigame:c:has_property (has_property x@c y@c))"
    assert parse_es("¿por qué x tiene y?", dialog) == (
        "(why wigame:c:has_property (has_property x@c y@c))"
    )


def test_retract_pattern():
    dialog = mini_dialog()

    assert parse_es("x ya no tiene y", dialog) == (
        "(retract wigame:c:has_property (has_property x@c y@c))"
    )


def test_bare_why_asks_about_the_last_turn():
    dialog = mini_dialog()
    parse_es("x tiene y", dialog)

    assert parse_es("¿por qué?", dialog) == "(why wigame:c:has_property (has_property x@c y@c))"


def test_bare_why_without_a_turn_is_not_understood():
    dialog = mini_dialog()

    with pytest.raises(ValueError):
        parse_es("why?", dialog)


def test_define_pattern():
    dialog = mini_dialog()

    assert parse_es("si x tiene y entonces x tiene z", dialog) == (
        "(define (if (has_property x@c y@c) (has_property x@c z@c)))"
    )


def test_conjunctive_define_pattern():
    dialog = mini_dialog()

    assert parse_es("si x tiene y y x tiene z entonces x tiene w", dialog) == (
        "(define (if (and (has_property x@c y@c) (has_property x@c z@c)) (has_property x@c w@c)))"
    )


def test_ellipsis_repeats_last_subject_and_verb():
    dialog = mini_dialog()
    dialog.remember_turn("check", "x@c", "y@c")

    assert parse_es("¿y z?", dialog) == "(ask has_property x@c z@c)"


def test_unknown_sign_asks_for_confirmation():
    dialog = mini_dialog()
    parsed = parse_es("¿q tiene y?", dialog)

    assert isinstance(parsed, Clarification)
    assert "no está en el vocabulario" in parsed.question


def test_candidate_commands(dialog):
    assert parse_es("candidatos", dialog) == f"(return candidates wigame:vegetales curation:proposed)"
    assert parse_es("aprueba cand:abc", dialog) == "(promote cand:abc)"
    assert parse_es("rechaza cand:abc sin fuente", dialog) == '(reject cand:abc "sin fuente")'


def test_show_wigame(dialog):
    # The focus is a corpus context, not a WiGame: every fact group is listed.
    assert parse_es("show wigame", dialog) == "(return facts)"
