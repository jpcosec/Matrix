"""Loads compiled WiGames/contexts/projections into the runtime for verification."""

from __future__ import annotations

from typing import Any

from src.operational_model import (
    Context,
    LogicalSystem,
    Name,
    Relation,
    RoutingProjection,
    SExpressionRuntime,
    Symbol,
    Thing,
    WiGame,
)

from .review import summary as review_summary
from .store import KB, load_yaml, now, read_json, sha256_file, write_json


def load_system(kb: KB) -> LogicalSystem:
    """Hydrates a LogicalSystem: symbols, relations, WiGames, context tree, projections."""

    system = LogicalSystem()
    for symbol_id, sign in sorted(_symbols(kb).items()):
        system.register_thing(Thing(Symbol(symbol_id), Name(sign)))
    for relation_id, spec in kb.load_relations().items():
        system.register_relation(
            Relation(
                relation_id=relation_id,
                name=spec.get("name", relation_id),
                transitive=bool(spec.get("transitive", False)),
            )
        )
    for path in kb.wigame_paths():
        system.register_wigame(WiGame.from_yaml(path.read_text(encoding="utf-8")))

    contexts = _load_contexts(kb)
    for context_id, payload in contexts.items():
        context = Context(context_id=context_id, metadata={"sources": payload.get("sources", [])})
        for wigame_id in payload.get("wigames", []):
            if wigame_id in system.wigames:
                context.route_to_wigame(wigame_id)
        for subcontext_id in payload.get("subcontexts", []):
            context.route_to_context(subcontext_id)
        system.register_context(context)

    for path in kb.projection_paths():
        system.register_projection(RoutingProjection.from_dict(load_yaml(path)))

    return system


def _symbols(kb: KB) -> dict[str, str]:
    """Flattens the per-context occurrence index into symbol_id -> first sign."""

    flattened: dict[str, str] = {}
    if not kb.symbols_path.exists():
        return flattened
    payload = load_yaml(kb.symbols_path) or {}
    for bucket in (payload.get("contexts") or {}).values():
        for symbol_id, entry in bucket.items():
            signs = entry.get("signs") or [symbol_id]
            flattened.setdefault(symbol_id, signs[0])
    return flattened


def _load_contexts(kb: KB) -> dict[str, Any]:
    if not kb.contexts_path.exists():
        return {}
    return (load_yaml(kb.contexts_path) or {}).get("contexts", {})


def route(
    kb: KB,
    source_wigame_id: str,
    source_terms: list[str],
    path: list[str],
    target_terms: list[str] | None = None,
) -> dict[str, Any]:
    """Multi-hop search across contexts through a path of projections."""

    from src.operational_model.system.logical_system_queries import route_search

    result = route_search(load_system(kb), source_wigame_id, source_terms, path, target_terms)
    return {
        "source_wigame": source_wigame_id,
        "source_hits": result.source_hits,
        "path": path,
        "projected_hits": result.projected_hits,
        "target_hits": result.target_hits,
        "cross_hits": result.cross_hits,
    }


def contexts_view(kb: KB) -> dict[str, Any]:
    """Returns the context tree with wigame membership."""

    contexts = _load_contexts(kb)
    if not contexts:
        return {"root": None, "contexts": {}}
    root = (load_yaml(kb.contexts_path) or {}).get("root")
    return {"root": root, "contexts": contexts}


def query(kb: KB, expressions: list[str]) -> dict[str, Any]:
    """Evaluates canonical s-expressions against the compiled KB."""

    runtime = SExpressionRuntime(load_system(kb))
    results: list[dict[str, Any]] = []
    for expression in expressions:
        result = runtime.evaluate(expression)
        results.append(
            {
                "expression": expression,
                "status": result.status,
                "sinn": result.sinn,
                "reason": result.reason,
                "payload": result.payload,
            }
        )
    return {"results": results}


def verify(kb: KB) -> dict[str, Any]:
    """Re-checks every compiled fact through the canonical runtime."""

    system = load_system(kb)
    runtime = SExpressionRuntime(system)
    problems: list[dict[str, Any]] = []
    checked = 0
    for row in kb.facts():
        expression = f"(check {row['wigame_id']} ({row['relation']} {row['subject']} {row['object']}))"
        result = runtime.evaluate(expression)
        checked += 1
        observed = (result.payload or {}).get("truth")
        if result.status != "accept" or observed != row["truth"]:
            problems.append(
                {
                    "expression": expression,
                    "expected": row["truth"],
                    "observed": observed,
                    "status": result.status,
                    "reason": result.reason,
                }
            )

    wigames = {
        wigame_id: {
            "context_id": wigame.context_id,
            "facts": len(wigame.facts),
            "axis_a": len(wigame.axis_a),
            "axis_b": len(wigame.axis_b),
            "pure": wigame.is_pure(),
        }
        for wigame_id, wigame in sorted(system.wigames.items())
    }
    payload = {
        "verified_at": now(),
        "checked": checked,
        "problems": problems,
        "ok": not problems,
        "contexts": {
            context_id: {
                "wigames": len([route for route in context.routes if route.target_id in system.wigames]),
                "subcontexts": len([route for route in context.routes if route.target_id in system.contexts]),
            }
            for context_id, context in sorted(system.contexts.items())
        },
        "projections": sorted(system.projections),
        "wigames": wigames,
        "artifact_sha256": {str(path.name): sha256_file(path) for path in kb.wigame_paths()},
    }
    write_json(kb.root / "verify_report.json", payload)
    return payload


def report(kb: KB) -> dict[str, Any]:
    """Aggregates store, ingest, compile, and verify reports."""

    manifest = load_yaml(kb.manifest_path) if kb.manifest_path.exists() else None
    payload = {
        "kb_root": str(kb.root),
        "sources": [
            {
                "slug": meta["slug"],
                "title": meta["title"],
                "revid": meta["revid"],
                "chars": meta["chars"],
                "sha256": meta["sha256"],
            }
            for meta in (read_json(path) for path in sorted(kb.sources_dir.glob("*.json")))
        ],
        "ingest": read_json(kb.root / "ingest_report.json") if (kb.root / "ingest_report.json").exists() else None,
        "compile": (manifest or {}).get("totals", {}),
        "contexts": (manifest or {}).get("contexts", {}).get("contexts", {}),
        "projections": (manifest or {}).get("projections", {}),
        "review": review_summary(kb),
        "verify": read_json(kb.root / "verify_report.json") if (kb.root / "verify_report.json").exists() else None,
        "counts": {
            "candidate_files": len(list(kb.candidates_dir.glob("**/*.jsonl"))),
            "proposals": len(kb.proposals()),
            "facts": len(kb.facts()),
            "wigames": len(kb.wigame_paths()),
            "projections": len(kb.projection_paths()),
        },
    }
    return payload
