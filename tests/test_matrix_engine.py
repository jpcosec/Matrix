import sys
import pytest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / ".." / "src"))
from matrix_engine import Context, MatrixEngine


@pytest.fixture
def context():
    return Context(
        name="test",
        objects={
            "lechuga": {"class": "vegetal"},
            "zanahoria": {"class": "vegetal"},
        },
        properties={
            "hoja": {"applies_to": "vegetal"},
            "hoja.rugosa": {"applies_if": {"requires": {"property": "hoja", "value": True}}},
        },
        truths={
            "lechuga": {"hoja": True, "hoja.rugosa": True},
            "zanahoria": {"hoja": False, "hoja.rugosa": False},
        },
        rules=[]
    )


@pytest.fixture
def engine(context):
    return MatrixEngine(context)


def test_matrix_M_values(engine):
    assert engine.M["lechuga"]["hoja"] is True
    assert engine.M["zanahoria"]["hoja"] is False


def test_matrix_S_applicability(engine):
    assert engine.S["lechuga"]["hoja.rugosa"] is True
    assert engine.S["zanahoria"]["hoja.rugosa"] is False


def test_get_status_sinnvoll_true(engine):
    status = engine.get_status("lechuga", "hoja.rugosa")
    assert status["status"] == "sinnvoll"
    assert status["applicable"] is True
    assert status["truth"] is True


def test_get_status_unsinnig(engine):
    status = engine.get_status("zanahoria", "hoja.rugosa")
    assert status["status"] == "unsinnig_contextual"
    assert status["applicable"] is False


def test_query_single_property(engine):
    result = engine.query(["hoja"])
    assert "lechuga" in result


def test_detect_tautologies(context):
    ctx = Context(
        name="test",
        objects={"a": {}, "b": {}},
        properties={"x": {}},
        truths={"a": {"x": True}, "b": {"x": True}},
        rules=[]
    )
    engine = MatrixEngine(ctx)
    assert "x" in engine.detect_tautologies()
