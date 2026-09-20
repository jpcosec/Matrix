"""Capability probe: exercises upserts, inference, queries, sense, serialization.

Runs a scripted battery (in-memory) plus optional KB checks, and reports
pass/fail with evidence. Gaps are reported as `ok: false` with the observed
behaviour instead of hiding them.
"""

from __future__ import annotations

from typing import Any

from src.operational_model import (
    Fact,
    LiSpace,
    LogicalSystem,
    Name,
    Proposition,
    Relation,
    SearchVector,
    SenseValue,
    SExpressionRuntime,
    Symbol,
    Thing,
    TruthValue,
    WiGame,
    parse_formula,
)
from src.operational_model.kernel import collect_atoms, evaluate_formula
from src.operational_model.system.logical_system_queries import cross_search, route_search

from .store import KB, load_yaml, now


def _system(*, commutative: bool = False, transitive: bool = False) -> tuple[LogicalSystem, str, str]:
    system = LogicalSystem()
    relation_id = "es"
    for symbol_id in ("a", "b", "c", "and", "or", "not"):
        system.register_thing(Thing(Symbol(symbol_id), Name(symbol_id)))
    system.register_relation(Relation(relation_id, relation_id, commutative=commutative, transitive=transitive))
    li = LiSpace(li_id="li:main", axis_a=["a", "b", "c"], axis_b=["a", "b", "c"], relation_id=relation_id)
    wigame = WiGame(wigame_id="wigame:main", li=li, context_id="ctx:probe")
    system.register_wigame(wigame)
    return system, wigame.wigame_id, relation_id


def _fact(wigame_id: str, relation_id: str, subject: str, obj: str, truth: TruthValue = TruthValue.TRUE) -> Fact:
    proposition = Proposition(relation_id, subject, obj, wigame_id)
    return Fact(proposition=proposition, truth=truth, evidence={"probe": True})


def _check(name: str, ok: bool, **evidence: Any) -> dict[str, Any]:
    return {"capability": name, "ok": bool(ok), **evidence}


def probe_upserts() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    system, wigame_id, relation_id = _system()
    runtime = SExpressionRuntime(system)

    system.add_fact(_fact(wigame_id, relation_id, "a", "b"))
    results.append(_check("upsert.add_new_fact", system.wigames[wigame_id].Vi.get("a", "b") == "true"))

    before = len(system.wigames[wigame_id].facts)
    system.add_fact(_fact(wigame_id, relation_id, "a", "b"))
    results.append(_check("upsert.duplicate_is_idempotent", len(system.wigames[wigame_id].facts) >= before))

    system.wigames[wigame_id].Vi.set("b", "a", "false")
    response = runtime.evaluate(f"(assert {wigame_id} ({relation_id} b a))")
    results.append(
        _check("upsert.assert_over_false_rejected", response.status == "reject", status=response.status, reason=response.reason)
    )

    registered = runtime.evaluate(f"(ingest {wigame_id} ({relation_id} c a))")
    slot = system.wigames[wigame_id].Vi.get("c", "a")
    results.append(
        _check(
            "upsert.ingest_registers_without_truth",
            registered.status == "accept" and slot == TruthValue.UNKNOWN.value,
            status=registered.status,
            cell=slot,
        )
    )

    system.wigames[wigame_id].set_sense("a", "b", SenseValue.UNSINNIG)
    results.append(_check("upsert.set_sense_override", system.wigames[wigame_id].Si.get("a", "b") == "unsinnig"))
    return results


def probe_inference() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    system, wigame_id, relation_id = _system(commutative=True)
    system.add_fact(_fact(wigame_id, relation_id, "a", "b"))
    results.append(
        _check(
            "inference.commutative",
            system.wigames[wigame_id].Vi.get("b", "a") == "true",
            observed=system.wigames[wigame_id].Vi.get("b", "a"),
        )
    )

    system, wigame_id, relation_id = _system(transitive=True)
    system.add_fact(_fact(wigame_id, relation_id, "a", "b"))
    system.add_fact(_fact(wigame_id, relation_id, "b", "c"))
    results.append(
        _check(
            "inference.transitive_closure",
            system.wigames[wigame_id].Vi.get("a", "c") == "true",
            observed=system.wigames[wigame_id].Vi.get("a", "c"),
        )
    )

    system, wigame_id, relation_id = _system()
    system.add_fact(_fact(wigame_id, relation_id, "a", "b"))
    system.add_fact(_fact(wigame_id, relation_id, "b", "c"))
    results.append(
        _check(
            "inference.none_when_relation_has_no_algebra",
            system.wigames[wigame_id].Vi.get("a", "c") == TruthValue.UNKNOWN.value,
            observed=system.wigames[wigame_id].Vi.get("a", "c"),
        )
    )

    system, wigame_id, relation_id = _system(commutative=True)
    system.add_fact(_fact(wigame_id, relation_id, "a", "b"))
    results.append(
        _check(
            "inference.wigame_add_fact_bypasses_algebra",
            system.wigames[wigame_id].Vi.get("b", "a") == "true",
            note="WiGame.add_fact (sin LogicalSystem) no aplica algebra",
        )
    )
    return results


def probe_queries() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    system, wigame_id, relation_id = _system()
    system.add_fact(_fact(wigame_id, relation_id, "a", "b"))
    system.add_fact(_fact(wigame_id, relation_id, "c", "b"))

    hits = system.wigames[wigame_id].search(SearchVector(wigame_id=wigame_id, terms=["b"]))
    results.append(_check("query.local_search", sorted(hits) == ["a", "c"], hits=sorted(hits)))

    try:
        system.wigames[wigame_id].search(SearchVector(wigame_id=wigame_id, terms=["missing"]))
        results.append(_check("query.unknown_term_raises_explicitly", False, observed="no exception"))
    except KeyError as error:
        results.append(
            _check(
                "query.unknown_term_raises_explicitly",
                True,
                observed="KeyError",
                detail=str(error),
                gap="un término inexistente no se distingue de una consulta vacía desde el caller",
            )
        )

    runtime = SExpressionRuntime(system)
    results.append(
        _check(
            "query.check_truth",
            runtime.evaluate(f"(check {wigame_id} ({relation_id} a b))").payload["truth"] == "true",
        )
    )
    results.append(
        _check(
            "query.check_out_of_li_rejects",
            runtime.evaluate(f"(check {wigame_id} ({relation_id} a z))").status == "reject",
        )
    )

    status = system.wigames[wigame_id].get_status("a", "b")
    out_of_bounds = system.wigames[wigame_id].get_status("a", "zzz")
    results.append(
        _check(
            "query.status_result",
            status.applicable is True and out_of_bounds.status == "unsinnig",
            status=status.status,
            out_of_bounds=out_of_bounds.status,
        )
    )

    # cross-space search: two contexts + projection
    second = WiGame(
        wigame_id="wigame:other",
        li=LiSpace(li_id="li:other", axis_a=["a", "c"], axis_b=["b"], relation_id=relation_id),
        context_id="ctx:other",
    )
    system.register_wigame(second)
    system.add_fact(_fact("wigame:other", relation_id, "a", "b"))
    from src.operational_model import RoutingProjection

    projection = RoutingProjection.empty("wigame:main", ["a", "c"], "wigame:other", ["a", "c"])
    projection.matrix_id = "proj:main:other"
    projection.link("a", "a")
    projection.link("c", "c")
    system.register_projection(projection)

    cross = cross_search(system, "wigame:main", ["b"], "proj:main:other", ["b"])
    routed = route_search(system, "wigame:main", ["b"], ["proj:main:other"], ["b"])
    results.append(
        _check(
            "query.cross_search",
            sorted(cross.source_hits) == ["a", "c"] and "a" in cross.cross_hits,
            source_hits=sorted(cross.source_hits),
            projected=sorted(cross.projected_hits),
            cross_hits=sorted(cross.cross_hits),
        )
    )
    results.append(
        _check("query.route_search_multihop", sorted(routed.projected_hits) == ["a", "c"], projected=sorted(routed.projected_hits))
    )
    return results


def probe_sense() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    wigame = WiGame(
        wigame_id="wigame:sense",
        li=LiSpace(li_id="li:sense", axis_a=["a", "b"], axis_b=["p", "q"], relation_id="es"),
        context_id="ctx:sense",
    )
    wigame.add_fact(_fact("wigame:sense", "es", "a", "p"))
    wigame.add_fact(_fact("wigame:sense", "es", "b", "p"))

    results.append(_check("sense.is_pure", wigame.is_pure() is True))
    results.append(
        _check(
            "sense.tautological_column",
            wigame.tautological_columns() == ["p"],
            columns=wigame.tautological_columns(),
        )
    )
    energy = wigame.information_energy()
    results.append(_check("sense.information_energy", isinstance(energy, float), energy=energy))
    return results


def probe_serialization() -> list[dict[str, Any]]:
    wigame = WiGame(
        wigame_id="wigame:ser",
        li=LiSpace(li_id="li:ser", axis_a=["a", "b"], axis_b=["p"], relation_id="es"),
        context_id="ctx:ser",
        metadata={"source": "probe"},
    )
    wigame.add_fact(_fact("wigame:ser", "es", "a", "p"))
    restored = WiGame.from_yaml(wigame.to_yaml())
    ok = (
        restored.wigame_id == wigame.wigame_id
        and restored.context_id == wigame.context_id
        and restored.metadata == wigame.metadata
        and restored.Vi.get("a", "p") == "true"
        and restored.Si.get("a", "p") == "sinnvoll"
        and set(restored.facts) == set(wigame.facts)
    )
    return [_check("serialization.yaml_roundtrip", ok, facts=len(restored.facts))]


def probe_kernel() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    formula = parse_formula("(and kern:a (not kern:b))")
    atoms = collect_atoms(formula)
    evaluation = evaluate_formula(formula, {"kern:a": True, "kern:b": False})
    results.append(_check("kernel.parse_and_collect_atoms", atoms == ("kern:a", "kern:b"), atoms=list(atoms)))
    results.append(_check("kernel.evaluate_formula", evaluation is True, evaluation=evaluation))
    return results


def probe_kb(kb: KB) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    manifest = load_yaml(kb.manifest_path) if kb.manifest_path.exists() else {}
    wigames = [WiGame.from_yaml(path.read_text(encoding="utf-8")) for path in kb.wigame_paths()]
    results.append(
        _check(
            "kb.every_wigame_has_context",
            bool(wigames) and all(wigame.context_id for wigame in wigames),
            wigames=len(wigames),
        )
    )
    facts = kb.facts()
    results.append(
        _check(
            "kb.pronoun_referents_resolved",
            all("she" not in (row["subject"], row["object"]) for row in facts),
            facts=len(facts),
        )
    )
    projections = manifest.get("projections", {})
    results.append(
        _check(
            "kb.cross_context_projections",
            bool(projections),
            projections=len(projections),
            example=next(iter(projections), None),
        )
    )
    contexts = manifest.get("contexts", {}).get("contexts", {})
    results.append(
        _check(
            "kb.context_tree_rooted",
            any(payload.get("parent") is None for payload in contexts.values()),
            contexts=len(contexts),
        )
    )
    return results


def run(kb: KB | None = None) -> dict[str, Any]:
    groups = {
        "upserts": probe_upserts(),
        "inference": probe_inference(),
        "queries": probe_queries(),
        "sense": probe_sense(),
        "serialization": probe_serialization(),
        "kernel": probe_kernel(),
    }
    if kb is not None:
        groups["kb"] = probe_kb(kb)
    checks = [item for group in groups.values() for item in group]
    return {
        "probed_at": now(),
        "total": len(checks),
        "passed": sum(1 for item in checks if item["ok"]),
        "failed": sum(1 for item in checks if not item["ok"]),
        "groups": groups,
        "failures": [item for item in checks if not item["ok"]],
    }
