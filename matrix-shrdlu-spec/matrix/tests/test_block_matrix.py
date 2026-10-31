"""Tests for BlockMatrix omnirepresentation."""

from src.operational_model.matrices.block_matrix import BlockMatrix
from src.operational_model.matrices.boolean_matrix import BooleanMatrix
from src.operational_model.matrices.si_matrix import SiMatrix
from src.operational_model.matrices.vi_matrix import ViMatrix


def test_block_matrix_builds_global_and_operational():
    wci = BooleanMatrix.filled(["ctx1"], ["ctx1"], fill=True)
    si = SiMatrix.pure(["ctx1"], ["term1"])
    vi = ViMatrix.empty(["subj1"], ["term1"])

    bm = BlockMatrix(context_matrix=wci, sense_matrix=si, truth_matrix=vi)
    global_m = bm.to_global_matrix()

    assert global_m.row_axis == ["ctx1", "subj1"]
    assert global_m.column_axis == ["ctx1", "term1"]
    assert global_m.get("ctx1", "ctx1") is True
