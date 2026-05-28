"""Bidirectional OWL <-> Matrix s-expression converter.

Mappings (from the whitepaper)
------------------------------
OWL                                Matrix
--------------------------------------------------------
owl:Class                          -> (create symbol ...)
rdfs:subClassOf                    -> sense proposition
owl:ObjectProperty                 -> (create relation ...)
rdf:type (class assertion)         -> (assert ... (type ...))
owl:ObjectPropertyAssertion        -> (assert ... (R a b))
owl:Restriction                    -> sense constraint
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Any, NamedTuple

_log = logging.getLogger(__name__)

# Optional rdflib backend -- detected at runtime.
_HAS_RDFLIB: bool
try:
    import rdflib  # noqa: F401
    import rdflib.plugins.sparql  # noqa: F401
    _HAS_RDFLIB = True
except ImportError:
    _HAS_RDFLIB = False


class OWLImportResult(NamedTuple):
    """Result of an OWL -> s-expression conversion."""

    sexprs: list[str]
    wigame_id: str
    stats: dict[str, int]


_OWL_NS = {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "owl": "http://www.w3.org/2002/07/owl#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
}

# Minimum tokens expected for various sexpr forms
_MIN_TOKENS_INGEST = 5
_MIN_TOKENS_ASSERT = 5
_MIN_ARGS_CREATE = 2


def _local(uri: object) -> str:
    """Extract a short name from a URI."""
    s = str(uri)
    return s.split("/")[-1].split("#")[-1]


class OWLConverter:
    """Convert between OWL ontologies and Matrix s-expressions.

    The converter never requires rdflib at import time.  When rdflib is
    available it can parse standard OWL serialisations; otherwise the
    caller must pre-parse the ontology.
    """

    # ---- OWL -> s-expressions ------------------------------------------

    def owl_to_sexprs(
        self,
        source: str,
        wigame_id: str = "wigame:owl",
        fmt: str = "turtle",
    ) -> OWLImportResult:
        """Parse an OWL source and emit Matrix s-expressions.

        Args:
            source: OWL serialisation string (Turtle, RDF/XML, ...).
            wigame_id: Target WiGame for imported facts.
            fmt: Source format (``turtle``, ``xml``, ...).

        Returns:
            OWLImportResult with generated s-expressions.
        """
        if not _HAS_RDFLIB:  # noqa: PLC0415
            _log.warning(
                "rdflib not available -- cannot parse OWL; "
                "install with: pip install rdflib"
            )
            return OWLImportResult(sexprs=[], wigame_id=wigame_id, stats={})

        import rdflib  # noqa: PLC0415

        graph = rdflib.Graph()
        graph.parse(data=source, format=fmt)
        return self._from_graph(graph, wigame_id=wigame_id)

    def _from_graph(
        self,
        graph: object,
        wigame_id: str = "wigame:owl",
    ) -> OWLImportResult:
        """Walk an rdflib Graph and emit Matrix s-expressions."""
        import rdflib  # noqa: PLC0415

        RDF = rdflib.Namespace(_OWL_NS["rdf"])
        RDFS = rdflib.Namespace(_OWL_NS["rdfs"])
        OWL = rdflib.Namespace(_OWL_NS["owl"])

        # Collect OWL entities
        classes = self._collect_classes(graph, RDF, OWL)
        individuals = self._collect_individuals(graph, RDF, OWL)
        object_props = self._collect_object_properties(graph, RDF, OWL)

        sexprs: list[str] = []
        seen_symbols: set[str] = set()
        seen_relations: set[str] = set()

        self._emit_symbols(sexprs, seen_symbols, classes)
        self._emit_symbols(sexprs, seen_symbols, individuals)
        self._emit_relations(sexprs, seen_relations, object_props)
        self._emit_subclass_axioms(sexprs, seen_symbols, graph, RDFS, wigame_id)
        self._emit_property_assertions(sexprs, graph, seen_relations, wigame_id)
        self._emit_class_assertions(sexprs, graph, RDF, classes, wigame_id)

        stats = {
            "classes": len(classes),
            "individuals": len(individuals),
            "object_properties": len(object_props),
            "sexprs": len(sexprs),
        }
        _log.info("OWL import stats: %s", stats)
        return OWLImportResult(sexprs=sexprs, wigame_id=wigame_id, stats=stats)

    # -- helpers for _from_graph -----------------------------------

    @staticmethod
    def _collect_classes(graph: Any, RDF: Any, OWL: Any) -> set[Any]:
        return {s for s, p, o in graph if p == RDF.type and o == OWL.Class}

    @staticmethod
    def _collect_individuals(graph: Any, RDF: Any, OWL: Any) -> set[Any]:
        import rdflib  # noqa: PLC0415

        inds: set[Any] = set()
        for s, p, o in graph:
            if p == RDF.type and o == OWL.NamedIndividual:
                inds.add(s)
            elif (p == RDF.type and isinstance(o, rdflib.URIRef)
                  and o not in (OWL.Class, OWL.ObjectProperty)):
                inds.add(s)
        return inds

    @staticmethod
    def _collect_object_properties(graph: Any, RDF: Any,
                                   OWL: Any) -> set[Any]:
        return {s for s, p, o in graph if p == RDF.type and o == OWL.ObjectProperty}

    @staticmethod
    def _emit_symbols(sexprs: list[str], seen: set[str], uris: set[Any]) -> None:
        for uri in uris:
            name = _local(uri)
            if name and name not in seen:
                sexprs.append(f"(create symbol {name} {name})")
                seen.add(name)

    @staticmethod
    def _emit_relations(sexprs: list[str], seen: set[str], uris: set[Any]) -> None:
        for uri in uris:
            name = _local(uri)
            if name and name not in seen:
                sexprs.append(f"(create relation {name} {name})")
                seen.add(name)

    @staticmethod
    def _emit_subclass_axioms(
        sexprs: list[str],
        seen_symbols: set[str],
        graph: Any,
        RDFS: Any,
        wigame_id: str,
    ) -> None:
        import rdflib  # noqa: PLC0415
        for s, p, o in graph:
            if p == RDFS.subClassOf and isinstance(o, rdflib.URIRef):
                child = _local(s)
                parent = _local(o)
                if parent not in seen_symbols:
                    sexprs.append(f"(create symbol {parent} {parent})")
                    seen_symbols.add(parent)
                sexprs.append(f"(ingest {wigame_id} (subclass {child} {parent}))")

    @staticmethod
    def _emit_property_assertions(
        sexprs: list[str],
        graph: Any,
        seen_relations: set[str],
        wigame_id: str,
    ) -> None:
        import rdflib  # noqa: PLC0415
        for s, p, o in graph:
            name = _local(p)
            if (name in seen_relations
                    and isinstance(s, rdflib.URIRef)
                    and isinstance(o, rdflib.URIRef)):
                sexprs.append(f"(assert {wigame_id} ({name} {_local(s)} {_local(o)}))")

    @staticmethod
    def _emit_class_assertions(
        sexprs: list[str],
        graph: Any,
        RDF: Any,
        classes: set[Any],
        wigame_id: str,
    ) -> None:
        for s, p, o in graph:
            if p == RDF.type and o in classes:
                sexprs.append(f"(assert {wigame_id} (type {_local(s)} {_local(o)}))")

    # ---- s-expressions -> OWL -----------------------------------------

    def sexprs_to_owl(
        self,
        sexprs: Sequence[str],
        ontology_iri: str = "http://matrix.engine/ontology",
    ) -> str:
        """Convert Matrix s-expressions to OWL Turtle.

        Args:
            sexprs: S-expression strings (as produced by
                    ``SExpressionRuntime`` commands).
            ontology_iri: Base IRI for the generated ontology.

        Returns:
            OWL ontology serialised as Turtle.
        """
        if not _HAS_RDFLIB:  # noqa: PLC0415
            _log.warning("rdflib not available -- returning stub OWL")
            return self._stub_owl(ontology_iri)

        import rdflib  # noqa: PLC0415

        graph = rdflib.Graph()
        matrix = rdflib.Namespace(f"{ontology_iri}#")
        RDF = rdflib.Namespace(_OWL_NS["rdf"])
        RDFS = rdflib.Namespace(_OWL_NS["rdfs"])
        OWL = rdflib.Namespace(_OWL_NS["owl"])
        XSD = rdflib.Namespace(_OWL_NS["xsd"])

        graph.bind("matrix", matrix)
        graph.bind("owl", OWL)
        graph.bind("rdfs", RDFS)
        graph.bind("xsd", XSD)

        ctx = _EmitContext(
            graph=graph, matrix=matrix,
            RDF=RDF, RDFS=RDFS, OWL=OWL, XSD=XSD,
        )
        for sexpr in sexprs:
            _emit_one(sexpr, ctx)

        return graph.serialize(format="turtle")

    @staticmethod
    def _stub_owl(ontology_iri: str) -> str:
        return f"""@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix : <{ontology_iri}#> .

: a owl:Ontology .
# rdflib not available -- install with: pip install rdflib
"""


# ---- Internal: sexpr -> OWL emission (extracted to reduce arg count) ---


class _EmitContext:
    """Bundle of rdflib namespaces to avoid passing 6 args to every method."""

    def __init__(  # noqa: PLR0913
        self,
        graph: Any,
        matrix: Any,
        RDF: Any,
        RDFS: Any,
        OWL: Any,
        XSD: Any,
    ) -> None:
        self.graph = graph
        self.matrix = matrix
        self.RDF = RDF
        self.RDFS = RDFS
        self.OWL = OWL
        self.XSD = XSD


def _emit_one(sexpr: str, ctx: _EmitContext) -> None:
    """Translate a single s-expression into OWL triples."""
    tokens = sexpr.replace("(", " ").replace(")", " ").split()
    if not tokens:
        return
    cmd = tokens[0]
    args = tokens[1:]

    try:
        min_args = _MIN_ARGS_CREATE
        if cmd == "create" and len(args) >= min_args and args[0] == "symbol":
            _emit_create_symbol(args[1], ctx)
        elif cmd == "create" and len(args) >= min_args and args[0] == "relation":
            _emit_create_relation(args[1], ctx)
        elif cmd == "ingest" and len(args) >= _MIN_TOKENS_INGEST:
            _emit_ingest(args, ctx)
        elif cmd == "assert" and len(args) >= _MIN_TOKENS_ASSERT:
            _emit_assert(args, ctx)
    except (IndexError, ValueError):
        _log.debug("Skipping unparseable s-expression: %s", sexpr)


def _emit_create_symbol(name: str, ctx: _EmitContext) -> None:  # type: ignore[misc]
    ctx.graph.add((ctx.matrix[name], ctx.RDF.type, ctx.OWL.Thing))


def _emit_create_relation(name: str, ctx: _EmitContext) -> None:  # type: ignore[misc]
    import rdflib  # noqa: PLC0415

    ctx.graph.add((ctx.matrix[name], ctx.RDF.type, ctx.OWL.ObjectProperty))
    ctx.graph.add((ctx.matrix[name], ctx.RDFS.label, rdflib.Literal(name)))


def _emit_ingest(args: list[str], ctx: _EmitContext) -> None:  # type: ignore[misc]
    import rdflib  # noqa: PLC0415

    wigame, pred, subj, obj = args[0], args[1], args[2], args[3]
    ctx.graph.add((ctx.matrix[subj], ctx.matrix[pred], ctx.matrix[obj]))
    ctx.graph.add((ctx.matrix[subj], ctx.matrix["wigame"], rdflib.Literal(wigame)))


def _emit_assert(args: list[str], ctx: _EmitContext) -> None:  # type: ignore[misc]
    import rdflib  # noqa: PLC0415

    wigame, pred, subj, obj = args[0], args[1], args[2], args[3]
    if pred == "type":
        ctx.graph.add((ctx.matrix[subj], ctx.RDF.type, ctx.matrix[obj]))
    else:
        ctx.graph.add((ctx.matrix[subj], ctx.matrix[pred], ctx.matrix[obj]))
    ctx.graph.add((ctx.matrix[subj], ctx.matrix["wigame"], rdflib.Literal(wigame)))
