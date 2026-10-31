"""Tests for the external_formats OWL and UNL interface addons."""
# ruff: noqa: ANN201

from __future__ import annotations

from src.external_formats.unl.unl_graph import UNLGraph, UNLRelation, UniversalWord
from src.external_formats.unl.unl_converter import UNLConverter


# ── UNL Graph unit tests ───────────────────────────────────────────


def test_unl_graph_from_triples() -> None:
    graph = UNLGraph.from_triples([
        ("agt", "eat", "dog"),
        ("obj", "eat", "food"),
    ])
    assert len(graph.words) == 3
    assert len(graph.relations) == 2
    assert graph.word("dog") is not None


def test_unl_graph_from_text() -> None:
    graph = UNLGraph.from_unl_text(
        "agt(eat, dog)\nobj(eat, food)\n@entry.eat\n@pl.dog"
    )
    assert len(graph.words) == 3
    assert len(graph.relations) == 2
    assert graph.entry_word_id == "eat"
    eat_attrs = sorted(graph.word("eat").attributes)
    assert eat_attrs == ["@entry"]


def test_unl_graph_scope() -> None:
    graph = UNLGraph.from_unl_text("agt:01(kill, Peter)\nobj:01(kill, Mary)")
    assert len(graph.relations) == 2
    for r in graph.relations:
        assert r.scope == "01"


def test_unl_graph_roundtrip() -> None:
    text = "agt(eat, dog)\nobj(eat, food)\n@entry.eat\n"
    graph = UNLGraph.from_unl_text(text)
    restored = graph.to_unl_text()
    assert "agt(eat, dog)" in restored
    assert "@entry.eat" in restored


def test_unl_relation_hierarchy() -> None:
    rel = UNLRelation(type="icl", source="mammal", target="dog")
    assert rel.parent == "aoj"
    assert rel.label == "subclass"


def test_unl_relation_unknown() -> None:
    rel = UNLRelation(type="xyz", source="a", target="b")
    assert rel.label == "xyz"
    assert rel.parent is None


# ── UNL Converter tests ────────────────────────────────────────────


def test_unl_converter_basic() -> None:
    graph = UNLGraph.from_unl_text("agt(eat, dog)\nobj(eat, food)")
    conv = UNLConverter()
    result = conv.unl_to_sexprs(graph)
    assert len(result.sexprs) > 0
    assert any("create symbol eat" in s for s in result.sexprs)
    assert any("create relation agent" in s for s in result.sexprs)
    assert any("(assert" in s and "agent" in s and "eat" in s for s in result.sexprs)


def test_unl_converter_sense_vs_truth() -> None:
    graph = UNLGraph.from_unl_text("icl(mammal, dog)\nagt(eat, dog)")
    conv = UNLConverter()
    result = conv.unl_to_sexprs(graph)
    ingest_sexprs = [s for s in result.sexprs if s.startswith("(ingest")]
    assert_sexprs = [s for s in result.sexprs if s.startswith("(assert")]
    assert any("subclass" in s for s in ingest_sexprs)
    assert any("agent" in s for s in assert_sexprs)


def test_unl_converter_attributes() -> None:
    graph = UNLGraph.from_unl_text("agt(eat, dog)\n@past.eat\n@pl.dog")
    conv = UNLConverter()
    result = conv.unl_to_sexprs(graph)
    attr_sexprs = [s for s in result.sexprs if "attr" in s]
    assert len(attr_sexprs) == 2


def test_unl_converter_roundtrip() -> None:
    graph = UNLGraph.from_unl_text("agt(eat, dog)\nobj(eat, food)")
    conv = UNLConverter()
    result = conv.unl_to_sexprs(graph)
    back = conv.sexprs_to_unl(result.sexprs)
    assert len(back.words) >= 3


def test_unl_converter_custom_wigame() -> None:
    graph = UNLGraph.from_unl_text("agt(eat, dog)")
    conv = UNLConverter()
    result = conv.unl_to_sexprs(graph, wigame_id="wigame:test")
    assert all("wigame:test" in s for s in result.sexprs if "wigame" in s)
    assert result.wigame_id == "wigame:test"


def test_unl_converter_stats() -> None:
    graph = UNLGraph.from_unl_text("agt(eat, dog)\nobj(eat, food)")
    conv = UNLConverter()
    result = conv.unl_to_sexprs(graph)
    assert result.stats["words"] >= 3
    assert result.stats["sexprs"] > 0


# ── OWL Converter tests ────────────────────────────────────────────


def test_owl_converter_without_rdflib() -> None:
    from src.external_formats.owl.owl_converter import OWLConverter

    conv = OWLConverter()
    result = conv.owl_to_sexprs("", fmt="turtle")
    assert result.sexprs == []
    stub = conv.sexprs_to_owl([])
    assert "@prefix owl:" in stub


def test_owl_converter_sexpr_to_turtle() -> None:
    from src.external_formats.owl.owl_converter import OWLConverter

    conv = OWLConverter()
    result = conv.sexprs_to_owl(["(create symbol lechuga lechuga)"])
    assert result.startswith("@prefix") or result.startswith("@")
