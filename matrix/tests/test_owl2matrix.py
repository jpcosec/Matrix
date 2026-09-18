"""test_owl2matrix.py

Unit tests for the OWL2MatrixParser module.
"""

from src.operational_model import LogicalSystem, SExpressionRuntime
from src.operational_model.language.owl2matrix import OWL2MatrixParser, OWLOntologyMapping


def test_owl2matrix_parser_xml_string() -> None:
    owl_xml = """<?xml version="1.0"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns:owl="http://www.w3.org/2002/07/owl#">
  <owl:Class rdf:about="http://example.org/ontology#Dish"/>
  <owl:Class rdf:about="http://example.org/ontology#Ingredient"/>
  <owl:ObjectProperty rdf:about="http://example.org/ontology#hasIngredient"/>
  <owl:NamedIndividual rdf:about="http://example.org/ontology#RagoutCarne">
    <hasIngredient rdf:resource="http://example.org/ontology#Carne"/>
  </owl:NamedIndividual>
</rdf:RDF>
"""
    parser = OWL2MatrixParser()
    mapping = parser.parse_xml_string(owl_xml)

    assert "Dish" in mapping.classes
    assert "Ingredient" in mapping.classes
    assert "hasIngredient" in mapping.properties
    assert "RagoutCarne" in mapping.individuals
    assert ("RagoutCarne", "hasIngredient", "Carne") in mapping.fact_assertions


def test_owl2matrix_ingest_into_runtime() -> None:
    owl_xml = """<?xml version="1.0"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns:owl="http://www.w3.org/2002/07/owl#">
  <owl:Class rdf:about="http://example.org/ontology#Ragout"/>
  <owl:ObjectProperty rdf:about="http://example.org/ontology#hasIngredient"/>
  <owl:NamedIndividual rdf:about="http://example.org/ontology#RagoutChampinon">
    <hasIngredient rdf:resource="http://example.org/ontology#Champinon"/>
  </owl:NamedIndividual>
</rdf:RDF>
"""
    system = LogicalSystem()
    runtime = SExpressionRuntime(system)
    parser = OWL2MatrixParser(runtime=runtime)

    results = parser.ingest_into_runtime(owl_xml, wigame_name="wigame:owl_demo")
    assert len(results) > 0

    # Query the ingested truth in the runtime
    check_res = runtime.evaluate("(check wigame:owl_demo (hasIngredient RagoutChampinon Champinon))")
    assert check_res.status == "accept"
    assert check_res.payload.get("truth") in (True, "true")
