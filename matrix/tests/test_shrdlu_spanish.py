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
FOCUS = "wigame:vegetales"


@pytest.fixture(scope="module")
def dialog():
    system, _, _ = build_system(CORPUS)
    return DialogState(focus_wigame=FOCUS, system=system)


@pytest.fixture(scope="module")
def ambiguous_dialog():
    from src.operational_model import Name, Symbol, Thing

    system, _, _ = build_system(CORPUS)
    system.register_thing(Thing(Symbol("lechuga_verde"), Name("lechuga")))
    return DialogState(focus_wigame=FOCUS, system=system)


def test_check_pattern(dialog):
    assert parse_es("¿la lechuga tiene hoja?", dialog) == f"(check {FOCUS} (implies lechuga hoja))"


def test_assert_pattern(dialog):
    assert parse_es("la lechuga implica hoja", dialog) == f"(assert {FOCUS} (implies lechuga hoja))"


def test_why_pattern(dialog):
    assert parse_es("¿por qué la lechuga tiene hoja?", dialog) == f"(why {FOCUS} (implies lechuga hoja))"


def test_retract_pattern(dialog):
    assert parse_es("la lechuga ya no implica hoja", dialog) == f"(retract {FOCUS} (implies lechuga hoja))"


def test_define_pattern(dialog):
    parsed = parse_es("si lechuga implica hoja entonces lechuga implica hoja_lisa", dialog)

    assert parsed == f"(define (if (implies lechuga hoja) (implies lechuga hoja_lisa)))"


def test_ellipsis_repeats_last_subject_and_verb(dialog):
    dialog.remember_turn("check", "lechuga", "hoja")

    assert parse_es("¿y raíz?", dialog) == f"(check {FOCUS} (implies lechuga raiz))"


def test_candidate_commands(dialog):
    assert parse_es("candidatos", dialog) == f"(return candidates {FOCUS} curation:proposed)"
    assert parse_es("aprueba cand:abc", dialog) == "(promote cand:abc)"
    assert parse_es("rechaza cand:abc sin fuente", dialog) == '(reject cand:abc "sin fuente")'


def test_show_wigame(dialog):
    assert parse_es("show wigame", dialog) == f"(return facts {FOCUS})"


def test_ambiguous_sign_returns_clarification(ambiguous_dialog):
    parsed = parse_es("¿la lechuga tiene hoja?", ambiguous_dialog)

    assert isinstance(parsed, Clarification)
    assert len(parsed.options) == 2
    assert "1)" in parsed.question


def test_answer_resolves_pending_clarification(ambiguous_dialog):
    parsed = parse_es("¿la lechuga tiene hoja?", ambiguous_dialog)
    ambiguous_dialog.pending = parsed
    resolved = ambiguous_dialog.answer("1")

    assert resolved.startswith(f"(check {FOCUS}")
    assert ambiguous_dialog.pending is None


def test_conjunctive_define_pattern(dialog):
    parsed = parse_es(
        "si la lechuga tiene hoja y la lechuga tiene verde entonces la lechuga tiene hoja_lisa",
        dialog,
    )

    assert parsed == (
        f"(define (if (and (implies lechuga hoja) (implies lechuga verde)) (implies lechuga hoja_lisa)))"
    )


def test_conjunctive_define_rejects_mismatched_subjects(dialog):
    with pytest.raises(ValueError):
        parse_es(
            "si la lechuga tiene hoja y la espinaca tiene verde entonces la lechuga tiene hoja_lisa",
            dialog,
        )
