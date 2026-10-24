"""Read-only probes of the official Matrix tree, independent of other variants.

These record observed behavior, including discrepancies; they do not repair it.
All constructed worlds are ephemeral. Output goes to stdout.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "Matrix" / "Matrix"))

from src.operational_model import (
    Context, Fact, LiSpace, LogicalSystem, Name, Proposition, Relation,
    SenseValue, SExpressionRuntime, Symbol, Thing, TruthValue, ViMatrix, WiGame,
)
from src.operational_model.system.hypertensor import assemble_block_matrix
from src.external_formats.owl.owl_converter import OWLConverter


def world():
    system = LogicalSystem()
    system.register_relation(Relation("r", "r"))
    for symbol in ("a", "b"):
        system.register_thing(Thing(Symbol(symbol), Name(symbol)))
    wi = WiGame("w", LiSpace("li", ["a"], ["b"], "r"), context_id="c")
    system.register_wigame(wi)
    context = Context("c")
    context.route_to_wigame("w")
    system.register_context(context)
    return system, wi


def main():
    report = {}
    matrix = ViMatrix(["a"], ["t", "f", "u"], [["true", "false", "∅"]])
    report["truth_bitmask"] = {
        "input": matrix.values, "observed": matrix.to_row_bitmasks(),
        "expected_if_only_true_is_active": [1],
    }

    system, wi = world()
    wi.set_sense("a", "b", SenseValue.UNSINNIG)
    runtime = SExpressionRuntime(system)
    check = runtime.evaluate("(check wigame:w (r a b))")
    assertion = runtime.evaluate("(assert wigame:w (r a b))")
    report["masked_assertion"] = {
        "check": {"status": check.status, "sense": check.sinn},
        "assert": {"status": assertion.status, "sense": assertion.sinn},
        "sense_after_assert": wi.Si.get("a", "b"), "truth_after_assert": wi.Vi.get("a", "b"),
    }

    system, wi = world()
    wi.add_fact(Fact(Proposition("r", "a", "b", "w"), TruthValue.TRUE))
    wi.set_sense("a", "b", SenseValue.UNSINNIG)
    block = assemble_block_matrix(system)
    report["local_mask_vs_block_mask"] = {
        "local_applicable": wi.get_status("a", "b").applicable,
        "block_operational_value": block.evaluate_operational("c").get("w::a", "w::b"),
    }

    converter = OWLConverter()
    owl = """@prefix ex: <https://example.org/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
ex:Class a owl:Class . ex:item a ex:Class .
"""
    converted = converter.owl_to_sexprs(owl)
    runtime = SExpressionRuntime(LogicalSystem())
    statuses = [(expr, runtime.evaluate(expr).status) for expr in converted.sexprs]
    report["turtle_import"] = {"stats": converted.stats, "runtime_results": statuses}

    from rdflib import Graph
    exported = converter.sexprs_to_owl(["(assert wigame:w (r a b))"])
    report["turtle_export_single_fact"] = {"triples": len(Graph().parse(data=exported, format="turtle"))}

    wi = WiGame("old_smoke_fixture", LiSpace("l", ["a"], ["b"], "r"), metadata={"context_id": "c"})
    report["our_original_smoke_context_metadata"] = {
        "metadata_context_id": wi.metadata["context_id"], "actual_context_id_field": wi.context_id,
        "interpretation": "neural conditioning worked, but the fixture did not populate Matrix's context_id field",
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
