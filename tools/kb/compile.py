"""Materializes approved proposals into context-scoped WiGame YAML artifacts.

A WiGame is (axes + relation) **under a context**, so every WiGame id is
``wigame:<context>:<relation>`` and carries ``context_id=ctx:<context>``.
Contexts form a tree: ``ctx:kb`` -> ``ctx:<source>`` -> WiGame leaves.
Cross-context identity is curation, not inference: reviewed entries in
``kb/aliases.yaml`` canonicalize occurrences per context and produce
``RoutingProjection`` links between contexts that share a referent.
"""

from __future__ import annotations

from typing import Any

from src.operational_model import (
    BooleanMatrix,
    Fact,
    LiSpace,
    Proposition,
    RoutingProjection,
    SenseValue,
    TruthValue,
    WiGame,
)

from . import operatoria
from .review import load_decisions, status_of, summary as review_summary
from .store import KB, dump_yaml, fact_id, now, sha256_file, write_json, write_jsonl

ROOT_CONTEXT = "ctx:kb"


def compile_kb(kb: KB, allow_unreviewed: bool = False, max_projection_pairs: int = 2000) -> dict[str, Any]:
    """Builds one WiGame per (context, relation) from approved proposals only."""

    kb.ensure()
    vocab = kb.load_relations()
    dump_yaml(kb.relations_path, {"relations": vocab})

    ledger = load_decisions(kb)
    alias_map = kb.alias_map()
    excluded = {"pending": 0, "rejected": 0}
    facts: list[dict[str, Any]] = []
    for proposal in kb.proposals():
        status = status_of(proposal, ledger)
        if status == "approved" or (allow_unreviewed and status == "pending"):
            facts.append(_materialize(proposal, ledger))
        else:
            excluded[status] = excluded.get(status, 0) + 1

    facts, alias_conflicts = _apply_aliases(facts, alias_map)
    write_jsonl(kb.root / "conflicts_after_alias.jsonl", alias_conflicts)

    algebra = operatoria.algebra_for(kb)
    facts, derived = _apply_algebra(facts, algebra)
    write_jsonl(kb.root / "facts_derived.jsonl", derived)

    for stale in kb.facts_dir.glob("*.jsonl"):
        stale.unlink()
    by_wigame: dict[str, list[dict[str, Any]]] = {}
    for row in facts:
        by_wigame.setdefault(row["wigame_id"], []).append(row)
    for name, group in by_wigame.items():
        write_jsonl(kb.facts_dir / f"{_safe(name)}.jsonl", group)

    for stale in kb.wigames_dir.glob("*.yaml"):
        stale.unlink()
    for stale in kb.projections_dir.glob("*.yaml"):
        stale.unlink()

    wigames: dict[str, dict[str, Any]] = {}
    games_by_context: dict[str, list[str]] = {}
    by_context_relation: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in facts:
        by_context_relation.setdefault((row["context"], row["relation"]), []).append(row)

    for (context, relation), rows in sorted(by_context_relation.items()):
        wigame = _build_wigame(context, relation, rows, vocab)
        path = kb.wigames_dir / f"{_safe(wigame.wigame_id)}.yaml"
        path.write_text(wigame.to_yaml(), encoding="utf-8")
        wigames[wigame.wigame_id] = {
            "path": str(path.relative_to(kb.root.parent)),
            "sha256": sha256_file(path),
            "context_id": wigame.context_id,
            "facts": len(rows),
            "axis_a": len(wigame.axis_a),
            "axis_b": len(wigame.axis_b),
        }
        games_by_context.setdefault(context, []).append(wigame.wigame_id)

    contexts = _write_contexts(kb, games_by_context)
    projections, projections_truncated = _write_projections(kb, by_context_relation, max_projection_pairs)
    shared = _shared_symbols(facts)
    dump_yaml(kb.shared_path, {"shared_symbols": shared})

    manifest = {
        "generated_at": now(),
        "kb_root": str(kb.root),
        "root_context": ROOT_CONTEXT,
        "relations": {
            relation: {"name": spec.get("name", relation), "transitive": bool(spec.get("transitive", False))}
            for relation, spec in sorted(vocab.items())
        },
        "review": review_summary(kb),
        "excluded": excluded,
        "contexts": contexts,
        "projections": projections,
        "projections_truncated": projections_truncated,
        "shared_symbols": {
            relation: {axis: {symbol: contexts for symbol, contexts in sorted(entries.items())}}
            for relation, axes in sorted(shared.items())
            for axis, entries in sorted(axes.items())
        },
        "alias_conflicts": len(alias_conflicts),
        "aliases_applied": len(alias_map),
        "derived_facts": len(derived),
        "algebra": {relation: profile for relation, profile in sorted(algebra.items()) if any(profile.values())},
        "wigames": wigames,
        "totals": {
            "facts": sum(item["facts"] for item in wigames.values()),
            "wigames": len(wigames),
            "contexts": len(games_by_context),
            "projections": len(projections),
        },
    }
    dump_yaml(kb.manifest_path, manifest)
    write_json(
        kb.root / "compile_report.json",
        {"wigames": wigames, "totals": manifest["totals"], "excluded": excluded, "contexts": contexts},
    )
    return manifest


def _materialize(proposal: dict[str, Any], ledger: dict[str, Any]) -> dict[str, Any]:
    decision = ledger["decisions"].get(proposal["proposal_id"], {})
    return {
        "fact_id": fact_id(
            proposal["context"], proposal["relation"], proposal["subject"], proposal["object"], proposal["truth"]
        ),
        "proposal_id": proposal["proposal_id"],
        "context": proposal["context"],
        "context_id": proposal["context_id"],
        "wigame_id": proposal["wigame_id"],
        "relation": proposal["relation"],
        "subject": proposal["subject"],
        "object": proposal["object"],
        "subject_sign": proposal["subject_sign"],
        "object_sign": proposal["object_sign"],
        "truth": proposal["truth"],
        "sources": proposal.get("sources", []),
        "provenance": proposal.get("provenance", []),
        "review": {
            "decision": decision.get("decision", "unreviewed"),
            "reviewer": decision.get("reviewer"),
            "reviewed_at": decision.get("reviewed_at"),
        },
    }


def _apply_aliases(
    facts: list[dict[str, Any]], alias_map: dict[tuple[str, str], str]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Canonicalizes occurrences per context and re-dedupes the merged slots."""

    if not alias_map:
        return facts, []
    for row in facts:
        row["subject"] = alias_map.get((row["context"], row["subject"]), row["subject"])
        row["object"] = alias_map.get((row["context"], row["object"]), row["object"])
        row["wigame_id"] = f"wigame:{row['context']}:{row['relation']}"
        row["fact_id"] = fact_id(row["context"], row["relation"], row["subject"], row["object"], row["truth"])

    slots: dict[tuple[str, str, str, str], list[dict[str, Any]]] = {}
    for row in facts:
        slots.setdefault((row["context"], row["relation"], row["subject"], row["object"]), []).append(row)

    merged: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    for (context, relation, subject, object_id), group in sorted(slots.items()):
        truths = {row["truth"] for row in group}
        if len(truths) > 1:
            conflicts.append(
                {
                    "reason": "alias_merge_conflict",
                    "context": context,
                    "wigame_id": f"wigame:{context}:{relation}",
                    "relation": relation,
                    "subject": subject,
                    "object": object_id,
                    "truths": sorted(truths),
                    "proposal_ids": [row["proposal_id"] for row in group],
                }
            )
            continue
        chosen = max(group, key=lambda row: row.get("confidence") or 0)
        provenance = [entry for row in group for entry in row.get("provenance", [])]
        merged.append({**chosen, "provenance": provenance})
    return merged, conflicts


def _shared_symbols(facts: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, list[str]]]]:
    """Symbols that appear in >=2 contexts, per relation and axis.

    Cross-context identity in descriptive corpora lives on the object axis
    (ingredients, dependencies); subjects are usually context-specific. This
    digest makes that sharing queryable without abusing RoutingProjection
    (which projects subjects only).
    """

    seen: dict[tuple[str, str, str], set[str]] = {}
    for row in facts:
        seen.setdefault((row["relation"], "subject", row["subject"]), set()).add(row["context"])
        seen.setdefault((row["relation"], "object", row["object"]), set()).add(row["context"])
    shared: dict[str, dict[str, dict[str, list[str]]]] = {}
    for (relation, axis, symbol), contexts in sorted(seen.items()):
        if len(contexts) < 2:
            continue
        shared.setdefault(relation, {}).setdefault(axis, {})[symbol] = sorted(contexts)
    return shared


def _write_contexts(kb: KB, games_by_context: dict[str, list[str]]) -> dict[str, Any]:
    """Writes the context tree and returns its serialized form."""

    payload: dict[str, Any] = {
        "root": ROOT_CONTEXT,
        "contexts": {
            ROOT_CONTEXT: {
                "parent": None,
                "subcontexts": [f"ctx:{context}" for context in sorted(games_by_context)],
                "wigames": [],
                "sources": [],
            }
        },
    }
    for context, wigame_ids in sorted(games_by_context.items()):
        payload["contexts"][f"ctx:{context}"] = {
            "parent": ROOT_CONTEXT,
            "subcontexts": [],
            "wigames": sorted(wigame_ids),
            "sources": [context],
        }
    dump_yaml(kb.contexts_path, payload)
    return payload


def _write_projections(
    kb: KB,
    by_context_relation: dict[tuple[str, str], list[dict[str, Any]]],
    max_pairs: int,
) -> tuple[dict[str, dict[str, Any]], bool]:
    """Links contexts that share a canonical subject referent under one relation.

    Pairs are O(contexts^2) per relation, so generation is capped: the cap is a
    deliberate stress/eng production guard, reported in the manifest.
    """

    by_relation: dict[str, dict[str, set[str]]] = {}
    for (context, relation), rows in sorted(by_context_relation.items()):
        by_relation.setdefault(relation, {})[context] = {row["subject"] for row in rows}

    pairs: list[tuple[str, str, str, list[str]]] = []
    for relation, contexts in sorted(by_relation.items()):
        names = sorted(contexts)
        for source in names:
            for target in names:
                if source == target:
                    continue
                shared = sorted(contexts[source] & contexts[target])
                if shared:
                    pairs.append((source, target, relation, shared))

    truncated = len(pairs) > max_pairs
    if truncated:
        step = max(1, len(pairs) // max_pairs)
        pairs = pairs[::step][:max_pairs]

    written: dict[str, dict[str, Any]] = {}
    for source, target, relation, shared in pairs:
        contexts = by_relation[relation]
        projection = RoutingProjection.empty(
            source_wigame_id=f"wigame:{source}:{relation}",
            source_axis=sorted(contexts[source]),
            target_wigame_id=f"wigame:{target}:{relation}",
            target_axis=sorted(contexts[target]),
            relation_id="projects_to",
        )
        projection.matrix_id = f"proj:{source}:{target}:{relation}"
        for symbol in shared:
            projection.link(symbol, symbol)
        name = f"proj__{_safe(source)}__{_safe(target)}__{_safe(relation)}.yaml"
        path = kb.projections_dir / name
        dump_yaml(path, projection.to_dict())
        written[projection.matrix_id] = {
            "path": str(path.relative_to(kb.root.parent)),
            "source": projection.source_wigame_id,
            "target": projection.target_wigame_id,
            "shared_subjects": shared,
        }
    return written, truncated


def _apply_algebra(
    facts: list[dict[str, Any]], algebra: dict[str, dict[str, bool]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Applies relation algebra declared by the domain operatoria.

    transitive -> derived reachability rows (closure)
    commutative -> derived symmetric rows
    """

    derived: list[dict[str, Any]] = []
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in facts:
        groups.setdefault((row["context"], row["relation"]), []).append(row)

    for (context, relation), rows in sorted(groups.items()):
        profile = algebra.get(relation, {})
        wigame_id = f"wigame:{context}:{relation}"
        existing_true = {
            (row["subject"], row["object"]) for row in rows if row["truth"] == "true"
        }
        existing_any = {(row["subject"], row["object"]) for row in rows}

        if profile.get("commutative"):
            for subject, obj in sorted(existing_true):
                slot = (obj, subject)
                if slot not in existing_any:
                    derived.append(_derived_row(context, relation, wigame_id, obj, subject, "commutative"))
                    existing_any.add(slot)

        if profile.get("transitive"):
            nodes = sorted({node for row in rows for node in (row["subject"], row["object"])})
            adjacency = BooleanMatrix.filled(nodes, nodes, False)
            for subject, obj in existing_true:
                adjacency.set(subject, obj, True)
            closure = adjacency.transitive_closure()
            for subject in nodes:
                for obj in nodes:
                    if subject == obj or not closure.get(subject, obj):
                        continue
                    if (subject, obj) in existing_true:
                        continue
                    derived.append(_derived_row(context, relation, wigame_id, subject, obj, "transitive_closure"))

    return facts + derived, derived


def _derived_row(
    context: str, relation: str, wigame_id: str, subject: str, obj: str, rule: str
) -> dict[str, Any]:
    return {
        "fact_id": fact_id(context, relation, subject, obj, "true") + ":derived",
        "proposal_id": None,
        "context": context,
        "context_id": f"ctx:{context}",
        "wigame_id": wigame_id,
        "relation": relation,
        "subject": subject,
        "object": obj,
        "subject_sign": subject,
        "object_sign": obj,
        "truth": "true",
        "sources": [],
        "provenance": [],
        "derived": rule,
        "review": {"decision": "derived", "reviewer": "operatoria", "reviewed_at": None},
    }


def _build_wigame(context: str, relation: str, rows: list[dict[str, Any]], vocab: dict[str, dict[str, Any]]) -> WiGame:
    subjects = sorted({row["subject"] for row in rows})
    objects = sorted({row["object"] for row in rows})
    spec = vocab.get(relation, {})
    li = LiSpace(
        li_id=f"li:{context}:{relation}",
        axis_a=subjects,
        axis_b=objects,
        relation_id=relation,
        metadata={"relation_name": spec.get("name", relation), "context": context},
    )
    wigame = WiGame(
        wigame_id=f"wigame:{context}:{relation}",
        li=li,
        context_id=f"ctx:{context}",
        metadata={
            "context": context,
            "relation_name": spec.get("name", relation),
            "origin": "wikipedia-kb-fanout",
            "sources": sorted({source for row in rows for source in row.get("sources", [])}),
        },
    )
    for row in rows:
        proposition = Proposition(
            relation_id=relation,
            subject_symbol_id=row["subject"],
            object_symbol_id=row["object"],
            wigame_id=wigame.wigame_id,
            proposition_id=f"prop:{row['fact_id']}",
        )
        truth = TruthValue.TRUE if row["truth"] == "true" else TruthValue.FALSE
        fact = Fact(
            proposition=proposition,
            truth=truth,
            fact_id=row["fact_id"],
            evidence={
                "provenance": row.get("provenance", []),
                "review": row.get("review", {}),
                "context": context,
            },
        )
        wigame.add_fact(fact, sense=SenseValue.SINNVOLL)
    return wigame


def _safe(name: str) -> str:
    return name.replace(":", "__").replace("/", "_").replace("->", "_to_")
