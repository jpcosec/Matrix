"""Synthetic, context-paired text -> explicit RDF assertions -> real Matrix.

This is a controlled fixture compiler, not an extractor of arbitrary prose.
RDF false/sense values use an explicit application schema, not closed-world RDF.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "Matrix" / "Matrix"))

from rdflib import Graph, Literal, Namespace, RDF
from src.operational_model import (
    Fact, LiSpace, LogicalSystem, Name, Proposition, Relation, SenseValue,
    Symbol, Thing, TruthValue, WiGame,
)
from src.operational_model.core.evidence import make_evidence
from src.operational_model.kernel.rule_schema import parse_schema
from src.operational_model.system.deduction import deduce

EX = Namespace("https://example.org/matrix-ncm/")
CONTEXTS = ("botanica", "fabula")
PREDICATES = ("planta", "animal", "fotosintetico", "caminante", "elector", "respirable", "florido")
SURFACES = {
    "planta": "es una planta", "animal": "es un animal",
    "fotosintetico": "hace fotosintesis", "caminante": "puede caminar",
    "elector": "puede votar", "respirable": "respira", "florido": "tiene flores",
}
# None denotes missing truth evidence, never a negative label.
TRUTHS = {
    "botanica": (True, False, None, False, None, True, None),
    "fabula": (False, True, False, None, True, True, None),
}


def export_fixture(context: str, entities: list[str], path: Path) -> None:
    graph = Graph()
    graph.bind("ex", EX)
    for entity in entities + ["ancla"]:
        for pred, truth in zip(PREDICATES, TRUTHS[context]):
            # Anchor prevents all true facts becoming non-discriminating,
            # except respira, deliberately universal in this finite world.
            if entity == "ancla":
                truth = pred == "respirable"
            node = EX[f"{entity}-{pred}"]
            graph.add((node, RDF.type, EX.Assertion))
            for key, value in ((EX.subject, EX[entity]), (EX.predicate, EX.es), (EX.object, EX[pred])):
                graph.add((node, key, value))
            graph.add((node, EX.context, Literal(context)))
            claim = f"el {entity} {SURFACES[pred]}"
            source = f"En {context}, {claim}." if truth else f"En {context}, no es cierto que {claim}."
            if truth is None:
                source = f"Consulta sin evidencia de verdad en {context}: ¿{claim}?"
            graph.add((node, EX.sourceText, Literal(source)))
            if truth is not None:
                graph.add((node, EX.truth, Literal("true" if truth else "false")))
            if context == "botanica" and pred == "elector" and entity != "ancla":
                graph.add((node, EX.sense, Literal("unsinnig")))
    graph.serialize(path, format="turtle")


def import_fixture(path: Path, context: str) -> LogicalSystem:
    """Compile our explicit fixture schema; preserve URI identity and context."""
    graph = Graph().parse(path, format="turtle")
    assertions = sorted(graph.subjects(RDF.type, EX.Assertion), key=str)
    subjects = sorted({str(graph.value(node, EX.subject)) for node in assertions})
    objects = sorted({str(graph.value(node, EX.object)) for node in assertions})
    system = LogicalSystem()
    system.register_relation(Relation(str(EX.es), "es"))
    for symbol in subjects + objects:
        system.register_thing(Thing(Symbol(symbol), Name(symbol)))
    world = WiGame(wigame_id=context, li=LiSpace(
        li_id=f"li:{context}", relation_id=str(EX.es), axis_a=subjects, axis_b=objects,
    ), metadata={"context_id": context})
    system.register_wigame(world)
    for node in assertions:
        if str(graph.value(node, EX.context)) != context:
            raise ValueError("mixed contexts in fixture")
        if graph.value(node, EX.predicate) != EX.es:
            raise ValueError("fixture supports exactly the es relation")
        subject, obj = str(graph.value(node, EX.subject)), str(graph.value(node, EX.object))
        truth = graph.value(node, EX.truth)
        if truth is not None:
            system.add_fact(Fact(
                Proposition(str(EX.es), subject, obj, context), TruthValue(str(truth)),
                evidence=make_evidence(prov=[{
                    "document_id": f"{path.name}#{node}:sourceText", "span": (0, len(str(graph.value(node, EX.sourceText)))),
                    "extractor": "controlled-fixture", "confidence": 1.0,
                }]),
            ))
        sense = graph.value(node, EX.sense)
        if sense is not None:
            world.set_sense(subject, obj, SenseValue(str(sense)))
    premise, conclusion = ("planta", "fotosintetico") if context == "botanica" else ("animal", "caminante")
    schema = parse_schema(f"(if ({EX.es} ?x {EX[premise]}) ({EX.es} ?x {EX[conclusion]}))")
    system.rules.extend(schema.expand(subjects))
    deduce(system, context)
    return system


def build_dataset(output: Path, count: int = 40) -> list[dict]:
    if count < 10:
        raise ValueError("need at least ten entities for grouped splits")
    output.mkdir(parents=True, exist_ok=True)
    entities = [f"litre_{i:03d}" for i in range(count)]
    rows = []
    for context in CONTEXTS:
        ttl = output / f"{context}.ttl"
        export_fixture(context, entities, ttl)
        system = import_fixture(ttl, context)
        world = system.wigames[context]
        for index, entity in enumerate(entities):
            split = "train" if index < int(count * .6) else "validation" if index < int(count * .8) else "test"
            for pred in PREDICATES:
                status = world.get_status(str(EX[entity]), str(EX[pred]))
                rows.append({
                    "id": f"{context}/{entity}/{pred}", "pair_id": f"{entity}/{pred}",
                    "entity": entity, "context": context, "predicate": pred,
                    "text": f"El {entity} {SURFACES[pred]}.", "split": split,
                    "truth": status.truth, "applicable": status.applicable,
                    "sense": status.status, "reason": status.reason,
                    "discriminative": status.discriminative, "source": ttl.name,
                })
    for split in ("train", "validation", "test"):
        with (output / f"{split}.jsonl").open("w") as handle:
            for row in rows:
                if row["split"] == split:
                    handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return rows


if __name__ == "__main__":
    rows = build_dataset(ROOT / "artifacts" / "dataset")
    print(json.dumps({split: sum(r["split"] == split for r in rows) for split in ("train", "validation", "test")}))
