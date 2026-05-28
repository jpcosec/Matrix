"""UNL (Universal Networking Language) interface for Matrix.

This module provides conversion between UNL semantic graphs and Matrix
s-expressions.  It follows the pipeline described in the whitepaper:

    UNL / semantic graph -> Matrix -> truth / sense matrices

UNL represents the meaning of a sentence as a hypergraph where
Universal Words (UWs) are nodes and semantic relations are edges.
"""

from .unl_converter import UNLConverter
from .unl_graph import UniversalWord, UNLGraph, UNLRelation

__all__ = [
    "UNLConverter",
    "UNLGraph",
    "UNLRelation",
    "UniversalWord",
]
