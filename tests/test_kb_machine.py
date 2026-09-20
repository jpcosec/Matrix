"""Contract tests: operatoria, machines/recipes, closure algebra, and oracles."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest

from tools.kb.compile import compile_kb
from tools.kb.ingest import ingest
from tools.kb.machine import generate_machines
from tools.kb.reach import analyze, analyze_all
from tools.kb.review import decide_filtered
from tools.kb.runtime import query
from tools.kb.store import KB, load_yaml


@pytest.fixture()
def machine_kb(tmp_path: Path) -> KB:
    kb = KB(tmp_path / "kb")
    generate_machines(kb)
    ingest(kb)
    decide_filtered(kb, "approved", "operatoria", note="spec")
    compile_kb(kb)
    return kb


def test_machine_kb_builds_and_verifies(machine_kb: KB) -> None:
    from tools.kb.runtime import verify

    report = verify(machine_kb)
    assert report["ok"] is True
    assert report["checked"] > 100

    manifest = load_yaml(machine_kb.manifest_path)
    assert manifest["derived_facts"] > 0
    assert manifest["algebra"]["precede"]["transitive"] is True
    assert manifest["algebra"]["sustituye_a"]["transitive"] is True


def test_operatoria_is_a_context_in_the_kb(machine_kb: KB) -> None:
    contexts = load_yaml(machine_kb.contexts_path)["contexts"]
    assert "ctx:operatoria" in contexts
    assert "wigame:operatoria:declara" in contexts["ctx:operatoria"]["wigames"]

    result = query(machine_kb, ["(check wigame:operatoria:declara (declara precede transitiva))"])["results"][0]
    assert result["status"] == "accept"
    assert result["payload"]["truth"] == "true"


def test_transitive_closure_is_applied_at_compile(machine_kb: KB) -> None:
    derived = [
        line
        for path in (machine_kb.root / "facts").glob("*precede.jsonl")
        for line in path.read_text(encoding="utf-8").splitlines()
        if '"derived"' in line
    ]
    assert derived, "expected closure-derived precede facts"

    # ragout is a linear chain: picar reaches servir only transitively
    result = query(machine_kb, ["(check wigame:ragout:precede (precede picar servir))"])["results"][0]
    assert result["status"] == "accept"
    assert result["payload"]["truth"] == "true"


def test_recipes_acyclic_and_fsm_cyclic(machine_kb: KB) -> None:
    ragout = analyze(machine_kb, "ragout")
    trafico = analyze(machine_kb, "trafico")
    assert ragout["acyclic"] is True
    assert ragout["cyclic_nodes"] == []
    assert trafico["acyclic"] is False
    assert set(trafico["cyclic_nodes"]) == {"rojo", "verde", "amarillo"}


def test_reachability_matches_bfs_oracle(machine_kb: KB) -> None:
    report = analyze_all(machine_kb)
    assert report["all_agreements"] is True
    assert all(item["bfs_oracle_agreement"] for item in report["results"])


def test_unreachable_and_equivalent_states(machine_kb: KB) -> None:
    trafico = analyze(machine_kb, "trafico")
    assert trafico["initial"] == "rojo"
    assert trafico["initial_source"] == "declared"
    assert trafico["unreachable"] == ["verde_peatonal"]
    assert trafico["equivalent_states"] == [["verde", "verde_peatonal"]]


def test_shared_symbols_across_recipes(machine_kb: KB) -> None:
    shared = load_yaml(machine_kb.shared_path)["shared_symbols"]
    assert shared["usa"]["object"]["cebolla"] == ["guiso", "ragout"]
    assert shared["usa"]["object"]["manteca"] == ["bechamel", "ragout"]


def test_substitution_chain_is_transitive(machine_kb: KB) -> None:
    result = query(machine_kb, ["(check wigame:bechamel:sustituye_a (sustituye_a manteca margarina))"])["results"][0]
    assert result["status"] == "accept"
    assert result["payload"]["truth"] == "true"
