"""Integration tests: the Corpus feeds sia.contingency and phi_entropic."""

from __future__ import annotations

from pathlib import Path

import pytest

from populator.extract import read_documents
from populator.matrix import build_corpus
from sia.contingency import contingency
from sia.intensity import phi_entropic


@pytest.fixture(scope="module")
def phi():
    root = Path(__file__).resolve().parents[1] / "corpus" / "vegetales"
    corpus = build_corpus(read_documents(root))
    matrix = phi_entropic(contingency(corpus.X))
    return corpus.concepts, matrix


def intensity(phi, concepts, left: str, right: str) -> float:
    return float(phi[concepts.index(left), concepts.index(right)])


def test_seed_implications_are_admissible(phi):
    concepts, matrix = phi

    assert intensity(matrix, concepts, "lechuga", "hoja") >= 0.85
    assert intensity(matrix, concepts, "zanahoria", "raiz") >= 0.85
    assert intensity(matrix, concepts, "apio", "tallo") >= 0.85


def test_zanahoria_does_not_imply_hoja(phi):
    concepts, matrix = phi

    assert intensity(matrix, concepts, "zanahoria", "hoja") < 0.5


def test_hoja_to_lechuga_is_weaker_than_the_reverse(phi):
    concepts, matrix = phi

    assert intensity(matrix, concepts, "hoja", "lechuga") < intensity(
        matrix, concepts, "lechuga", "hoja"
    )
