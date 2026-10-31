"""Tests for the SHRDLU REPL over the vegetales and physicists worlds."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.append(str(_REPO_ROOT))

from pipeline.curate import FakeBackend
from pipeline.run import build_system

from desk.drawer.shrdlu.dialog_state import DialogState
from desk.drawer.shrdlu.repl import Repl

CORPUS = str(_REPO_ROOT / "corpus" / "vegetales")
FOCUS = "wigame:vegetales"


@pytest.fixture
def repl() -> Repl:
    system, runtime, _ = build_system(CORPUS)
    dialog = DialogState(focus_wigame=FOCUS, system=system)
    return Repl(system=system, runtime=runtime, dialog=dialog)


def test_truth_question_answers_yes(repl):
    answer = repl.step("¿la lechuga tiene hoja_lisa?")

    assert answer.startswith("Sí:")
    assert "hoja_lisa@01_lechugas" in answer
    assert "01_lechugas.md" in answer


def test_ambiguous_question_asks_and_answer_resolves(repl):
    question = repl.step("¿la lechuga tiene hoja?")

    assert "1)" in question
    assert repl.step("1") in {"Sí.", "No lo sé (nadie lo ha confirmado)."}


def test_why_question_mentions_because_and_document(repl):
    answer = repl.step("¿por qué la lechuga tiene hoja_lisa?")

    assert "porque" in answer
    assert "01_lechugas.md" in answer
    assert "observed" in answer


def test_retract_reports_the_retracted_fact(repl):
    answer = repl.step("la lechuga ya no tiene hoja_lisa")

    assert "Retirado" in answer
    assert repl.step("¿la lechuga tiene hoja_lisa?") == "No."


def test_unknown_relation_answers_no_knowledge(repl):
    assert repl.step("¿la lechuga tiene raiz?") in {
        "No lo sé (nadie lo ha confirmado).",
        "No.",
    }


def test_candidates_list_is_honest(repl):
    listing = repl.step("candidatos")

    assert listing == "No hay candidatos pendientes." or "cand:" in listing


def test_show_wigame_lists_facts(repl):
    listing = repl.step("show wigame")

    assert "wigame:" in listing
    assert "= true" in listing


def test_sugiere_uses_the_injected_backend():
    from pipeline.convergence import symbol_convergence
    from pipeline.decompose import decompose
    from pipeline.ingest import ingest_contexts
    from populator import build_contexts
    from src.operational_model import LogicalSystem, SExpressionRuntime

    contexts = build_contexts(_load_curie_fixture().generate(0), lang="en")
    declarations = [d for c in contexts for d in decompose(c, lang="en")]
    system = LogicalSystem()
    runtime = SExpressionRuntime(system)
    ingest_contexts(system, runtime, contexts, declarations)
    symbol_convergence(system, contexts, declarations, taut_df=1.0)
    dialog = DialogState(focus_wigame="wigame:curie_0:born_in", system=system)
    repl = Repl(system=system, runtime=runtime, dialog=dialog)
    from src.operational_model.system.candidates import register_candidate

    candidate = register_candidate(
        system,
        "projection",
        "wigame:curie_0:born_in",
        {
            "source_wigame": "wigame:curie_0:born_in",
            "target_wigame": "wigame:curie_6:born_in",
            "pairs": [["she@curie_0", "she@curie_6"]],
        },
    )
    candidate_id = candidate.candidate_id
    curation_before = candidate.evidence["curation"]
    repl.backend = FakeBackend(
        '{"sexpr": "(project wigame:curie_0:born_in wigame:curie_6:born_in (she@curie_0 she@curie_6))", '
        '"prov_index": 0, "keep": true, "comment": "ok"}'
    )

    answer = repl.step(f"sugiere {candidate_id}")

    assert "Propuesta" in answer
    assert system.candidates[candidate_id].evidence["curation"] == curation_before


def test_sugiere_reports_backend_failures():
    class BrokenBackend:
        name = "broken"

        def __call__(self, prompt: str) -> str:
            raise RuntimeError("no model")

    class MinimalSystem:
        candidates = {}

    repl = Repl(system=MinimalSystem(), runtime=None, dialog=DialogState())
    repl.backend = BrokenBackend()

    assert "No pude consultar al backend" in repl.step("sugiere cand:missing")


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
    assert "porque" in repl.step("why?")


def test_unknown_line_is_reported_without_crashing(repl):
    assert "No entiendo" in repl.step("zzz qqq")


def test_build_repl_honours_lang_and_limit():
    from desk.drawer.shrdlu.repl import build_repl

    built = build_repl(CORPUS, "vegetales", lang="es", limit=1)

    assert built.system.symbols
    assert built.documents


def _load_curie_fixture():
    """Loads tests/fixtures/curie_franklin.py by path (matrix/tests shadows tests)."""

    import importlib.util

    path = _REPO_ROOT / "tests" / "fixtures" / "curie_franklin.py"
    spec = importlib.util.spec_from_file_location("curie_franklin_fixture", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
