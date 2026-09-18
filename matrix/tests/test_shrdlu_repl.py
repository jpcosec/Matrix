"""Tests for the Spanish SHRDLU REPL over the vegetales corpus."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.append(str(_REPO_ROOT))

from pipeline.run import build_system

from prototypes.shrdlu.dialog_state import DialogState
from prototypes.shrdlu.repl import Repl

CORPUS = str(_REPO_ROOT / "corpus" / "vegetales")
FOCUS = "wigame:vegetales"


@pytest.fixture
def repl() -> Repl:
    system, runtime, _ = build_system(CORPUS)
    dialog = DialogState(focus_wigame=FOCUS, system=system)
    return Repl(system=system, runtime=runtime, dialog=dialog)


def test_truth_question_answers_yes(repl):
    assert repl.step("¿la lechuga tiene hoja?") == "Sí."


def test_ellipsis_question_answers_no_knowledge(repl):
    repl.step("¿la lechuga tiene hoja?")

    assert repl.step("¿y raíz?").startswith("No")


def test_why_question_mentions_because_and_document(repl):
    answer = repl.step("¿por qué la lechuga tiene hoja?")

    assert "porque" in answer
    assert "01_lechugas.md" in answer
    assert "confirmed" in answer


def test_define_confirms_and_checks_derived_rule(repl):
    answer = repl.step("si lechuga implica hoja entonces lechuga implica hoja_lisa")

    assert "Regla añadida" in answer
    assert repl.step("¿lechuga implica hoja_lisa?") == "Sí."


def test_retract_reports_dependents(repl):
    repl.step("si lechuga implica hoja entonces lechuga implica hoja_lisa")
    answer = repl.step("la lechuga ya no implica hoja")

    assert "Retirado" in answer
    assert "Dependientes" in answer


def test_ambiguity_asks_and_answer_resolves(repl):
    repl.runtime.evaluate("(create symbol lechuga_verde lechuga)")
    question = repl.step("¿la lechuga tiene hoja?")

    assert "1)" in question
    assert repl.step("1") == "Sí."


def test_candidates_and_promote(repl):
    listing = repl.step("candidatos")

    assert "cand:" in listing
    candidate_id = listing.splitlines()[0].split()[1]
    assert repl.step(f"aprueba {candidate_id}").startswith("Confirmado")


def test_show_wigame_lists_facts(repl):
    listing = repl.step("show wigame")

    assert FOCUS in listing
    assert "= true" in listing
