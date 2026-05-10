import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / ".."))
from src.unified_engine import UnifiedMatrixEngine, TruthValue, NLParser
import yaml
import tempfile
import os


@pytest.fixture
def test_engine():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump({
            "contexts": {
                "test": {
                    "objects": {
                        "a": {"class": "test"},
                        "b": {"class": "test"},
                    },
                    "properties": {
                        "p1": {"applies_to": "test"},
                        "p2": {"applies_to": "test"},
                        "p3": {"applies_if": {"property": "p1", "value": True}}
                    },
                    "truths": {
                        "a": {"p1": True, "p2": False, "p3": True},
                        "b": {"p1": False, "p2": True}
                    }
                }
            },
            "bridges": [],
            "subcontexts": {}
        }, f)
        f.flush()
        engine = UnifiedMatrixEngine.load(f.name)
        os.unlink(f.name)
        return engine


class TestCoreMatrices:
    def test_M_matrix_values(self, test_engine):
        M = test_engine.M["test"]
        assert M[0, 0] == TruthValue.T.value
        assert M[0, 1] == TruthValue.F.value
        assert M[1, 0] == TruthValue.F.value

    def test_S_applicability(self, test_engine):
        S = test_engine.S["test"]
        assert S[0, 2] == True
        assert S[1, 2] == False

    def test_get_status(self, test_engine):
        status = test_engine.get_status("a", "p1")
        assert status["status"] == "sinnvoll"
        assert status["truth_label"] == "TRUE"

        status = test_engine.get_status("b", "p3")
        assert status["status"] == "unsinnig"
        assert status["truth_label"] == "NOT_APPLICABLE"


class TestQueries:
    def test_conjunctive_query(self, test_engine):
        results = test_engine.query(["p1"])
        assert "a" in results
        assert "b" not in results

    def test_query_multiple_props(self, test_engine):
        results = test_engine.query(["p1", "p2"])
        assert len(results) == 0


class TestContextComposition:
    def test_bridge_creation(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({
                "contexts": {
                    "ctx1": {
                        "objects": {"o1": {}, "o2": {}},
                        "properties": {"p1": {}},
                        "truths": {"o1": {"p1": True}, "o2": {"p1": False}}
                    },
                    "ctx2": {
                        "objects": {"r1": {}, "r2": {}},
                        "properties": {"q1": {}},
                        "truths": {"r1": {"q1": True}, "r2": {"q1": True}}
                    }
                },
                "bridges": [{
                    "name": "bridge1",
                    "from": "ctx1",
                    "to": "ctx2",
                    "from_objects": ["o1", "o2"],
                    "to_objects": ["r1", "r2"]
                }],
                "subcontexts": {}
            }, f)
            f.flush()
            engine = UnifiedMatrixEngine.load(f.name)
            os.unlink(f.name)

            bridge = engine.compose("ctx1", "ctx2", "bridge1")
            assert bridge.shape == (2, 2)


class TestSubcontexts:
    def test_subcontext_routing(self, test_engine):
        pass


class TestNLParser:
    def test_basic_parsing(self):
        parser = NLParser()
        result = parser.parse("la lechuga tiene hoja")
        assert result["subject"] == "lechuga"
        assert result["property"] == "hoja"

    def test_verb_detection(self):
        parser = NLParser()
        result = parser.parse("espinaca tiene hoja")
        assert result["relation"] == "has_property"
        assert "hoja" in result["property"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])