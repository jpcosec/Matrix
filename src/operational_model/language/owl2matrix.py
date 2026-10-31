"""owl2matrix.py

Converter and parser from Web Ontology Language (OWL / RDF-XML / Functional) 
to Matrix S-Expressions and LogicalSystem primitives.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..system.logical_system import LogicalSystem
    from ..system.operation_results import OperationResult
    from ..system.s_expression_runtime import SExpressionRuntime


@dataclass
class OWLOntologyMapping:
    """Holds extracted symbols, relations, and fact assertions from an OWL source."""

    classes: list[str] = field(default_factory=list)
    properties: list[str] = field(default_factory=list)
    individuals: list[str] = field(default_factory=list)
    subclass_relations: list[tuple[str, str]] = field(default_factory=list)
    fact_assertions: list[tuple[str, str, str]] = field(default_factory=list)

    def to_s_expressions(self, wigame_name: str = "wigame:owl_imported") -> list[str]:
        """Converts the extracted OWL elements into canonical Matrix S-Expressions."""
        sexprs: list[str] = []

        all_symbols = sorted(list(set(self.classes + self.individuals + [s for t in self.fact_assertions for s in (t[0], t[2])])))
        if not all_symbols:
            all_symbols = ["Thing"]

        all_props = sorted(list(set(self.properties + [t[1] for t in self.fact_assertions])))
        if not all_props:
            all_props = ["subclass_of"]

        # 1. Create Relations
        for prop in all_props:
            sexprs.append(f"(create relation {prop} {prop})")

        # 2. Create Symbols
        for sym in all_symbols:
            sexprs.append(f"(create symbol {sym} {sym})")

        # 3. Create Li Space & WiGame
        axis_a = " ".join(all_symbols)
        axis_b = " ".join(all_symbols)
        rel = all_props[0]

        sexprs.append(f"(create li li:owl_space {rel} (axis-a {axis_a}) (axis-b {axis_b}))")
        sexprs.append(f"(create wigame {wigame_name} li:owl_space)")

        # 4. Assert SubClassOf relations
        for sub, sup in self.subclass_relations:
            if "subclass_of" in all_props:
                sexprs.append(f"(assert {wigame_name} (subclass_of {sub} {sup}))")

        # 5. Assert Fact Triples
        for subj, prop, obj in self.fact_assertions:
            sexprs.append(f"(assert {wigame_name} ({prop} {subj} {obj}))")

        return sexprs


class OWL2MatrixParser:
    """Parses OWL XML/RDF documents and compiles them into Matrix LogicalSystems."""

    def __init__(self, runtime: "SExpressionRuntime" | None = None) -> None:
        self.runtime = runtime

    def parse_xml_string(self, xml_content: str) -> OWLOntologyMapping:
        """Parses an RDF/XML OWL ontology content string into an OWLOntologyMapping."""
        mapping = OWLOntologyMapping()

        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            raise ValueError(f"Invalid OWL XML content: {e}") from e

        def get_local_name(uri: str) -> str:
            clean = uri.split("}")[-1] if "}" in uri else uri
            if "#" in clean:
                return clean.split("#")[-1]
            if "/" in clean:
                return clean.split("/")[-1]
            return clean

        def get_ref(elem: ET.Element) -> str:
            for k, v in elem.attrib.items():
                if "about" in k or "resource" in k:
                    return get_local_name(v)
            return ""

        for elem in root.iter():
            tag = get_local_name(elem.tag)
            name = get_ref(elem)

            if tag == "Class" and name:
                mapping.classes.append(name)
            elif tag in ("ObjectProperty", "DatatypeProperty") and name:
                mapping.properties.append(name)
            elif tag == "NamedIndividual" and name:
                mapping.individuals.append(name)

            # Property assertions (child nodes of NamedIndividual)
            for child in elem:
                child_tag = get_local_name(child.tag)
                target = get_ref(child)
                if name and target and child_tag not in ("type", "subClassOf", "Class", "NamedIndividual", "ObjectProperty", "DatatypeProperty"):
                    mapping.properties.append(child_tag)
                    mapping.fact_assertions.append((name, child_tag, target))

        # Deduplicate
        mapping.classes = sorted(list(set(mapping.classes)))
        mapping.properties = sorted(list(set(mapping.properties)))
        mapping.individuals = sorted(list(set(mapping.individuals)))

        return mapping

    def ingest_into_runtime(
        self, xml_content: str, wigame_name: str = "wigame:owl_imported"
    ) -> list["OperationResult"]:
        """Parses OWL XML and evaluates all canonical S-Expressions directly into runtime."""
        if self.runtime is None:
            raise ValueError("Runtime must be provided to ingest OWL into LogicalSystem.")

        mapping = self.parse_xml_string(xml_content)
        sexprs = mapping.to_s_expressions(wigame_name=wigame_name)

        results = []
        for expr in sexprs:
            res = self.runtime.evaluate(expr)
            results.append(res)

        return results
