"""OWL (Web Ontology Language) interface for Matrix.

This module provides bidirectional conversion between OWL ontologies and
Matrix s-expressions.  It follows the architecture outlined in the
whitepaper:

    OWL :: classes, properties, restrictions, axioms
         → Matrix :: Things, Relations, Propositions, Facts, Sense

Usage
-----
    from src.external_formats.owl.owl_converter import OWLConverter

    converter = OWLConverter()

    # OWL Turtle/RDF/XML → s-expression list
    sexprs = converter.owl_to_sexprs("turtle_string")

    # Matrix s-expressions → OWL Turtle
    turtle = converter.sexprs_to_owl(["…", "…"])

The converter never requires rdflib at import time; it degrades gracefully
when the library is absent (a helpful message is emitted).
"""

from .owl_converter import OWLConverter, OWLImportResult

__all__ = [
    "OWLConverter",
    "OWLImportResult",
]
