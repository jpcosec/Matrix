"""Tests for the Spanish SHRDLU REPL over the vegetales corpus."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.append(str(_REPO_ROOT))

from pipeline.run import build_system

from pipeline.curate import FakeBackend

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


def test_sugiere_uses_the_injected_backend(repl):
    candidate_id = repl.step("candidatos").splitlines()[0].split()[1]
    payload = '{"sexpr": "(implies lechuga hoja)", "prov_index": 0, "keep": true, "comment": "ok"}'
    repl.backend = FakeBackend(payload)

    answer = repl.step(f"sugiere {candidate_id}")

    assert "Propuesta" in answer
    assert "(implies lechuga hoja)" in answer
    assert repl.system.candidates[candidate_id].evidence["curation"] == "proposed"


def test_sugiere_reports_backend_failures(repl):
    class BrokenBackend:
        name = "broken"

        def __call__(self, prompt: str) -> str:
            raise RuntimeError("no model")

    candidate_id = repl.step("candidatos").splitlines()[0].split()[1]
    repl.backend = BrokenBackend()

    assert "No pude consultar al backend" in repl.step(f"sugiere {candidate_id}")


def _load_curie_fixture():
    """Loads tests/fixtures/curie_franklin.py by path (matrix/tests shadows tests)."""

    import importlib.util

    path = _REPO_ROOT / "tests" / "fixtures" / "curie_franklin.py"
    spec = importlib.util.spec_from_file_location("curie_franklin_fixture", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_english_question_is_answered_by_routed_queries():
    from pipeline.convergence import symbol_convergence
    from pipeline.decompose import decompose
    from pipeline.ingest import ingest_contexts
    from populator import build_contexts
    from src.operational_model import LogicalSystem, SExpressionRuntime

    documents = _load_curie_fixture().generate(0)
    contexts = build_contexts(documents, lang="en")
    declarations = [d for c in contexts for d in decompose(c, lang="en")]
    system = LogicalSystem()
    runtime = SExpressionRuntime(system)
    ingest_contexts(system, runtime, contexts, declarations)
    symbol_convergence(system, contexts, declarations, taut_df=1.0)
    dialog = DialogState(system=system, focus_wigame="wigame:curie_3:born_in")
    repl = Repl(system=system, runtime=runtime, dialog=dialog)

    answer = repl.step("was Marie Curie born in Warsaw?")

    assert answer.startswith("Sí")
    assert "ruta:" in answer
    assert ".md:" in answer
