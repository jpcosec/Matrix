"""Command line surface for the Wikipedia KB fan-out harness."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.kb.compile import compile_kb  # noqa: E402
from tools.kb.ingest import ingest  # noqa: E402
from tools.kb.review import (  # noqa: E402
    annotate,
    apply_file,
    decide,
    decide_filtered,
    render_pending,
    reset,
    summary,
)
from tools.kb.runtime import contexts_view, query, report, route, verify  # noqa: E402
from tools.kb.sources import fetch_wikipedia, prepare, write_source  # noqa: E402
from tools.kb.store import KB, load_yaml, now, write_json  # noqa: E402

DEFAULT_REVIEWER = os.environ.get("KB_REVIEWER", os.environ.get("USER", "unreviewed"))


def _print(payload: object) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def _proposal_view(kb: KB, status: str, relation: str | None, limit: int | None, compact: bool) -> list[dict]:
    rows = annotate(kb, kb.proposals())
    if status != "all":
        rows = [row for row in rows if row["status"] == status]
    if relation:
        rows = [row for row in rows if row["relation"] == relation]
    rows.sort(key=lambda row: (row["relation"], row["subject"], row["object"]))
    if limit:
        rows = rows[:limit]
    if not compact:
        return rows
    return [
        {
            "proposal_id": row["proposal_id"],
            "proposition": f"({row['relation']} {row['subject']} {row['object']})",
            "truth": row["truth"],
            "status": row["status"],
            "confidence": row["confidence"],
            "evidence": (row.get("provenance") or [{}])[0].get("sentence", "")[:160],
        }
        for row in rows
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tools.kb", description="Wikipedia -> WiGame KB fan-out harness")
    parser.add_argument("--kb", default="kb", help="KB directory (default: kb)")
    sub = parser.add_subparsers(dest="command", required=True)

    fetch = sub.add_parser("fetch", help="fetch a Wikipedia article into the KB")
    fetch.add_argument("title")
    fetch.add_argument("--lang", default="en")
    fetch.add_argument("--intro-only", action="store_true")

    prep = sub.add_parser("prepare", help="chunk sources and write worker prompts")
    prep.add_argument("--source", help="source slug (default: all)")
    prep.add_argument("--max-chars", type=int, default=1500)

    ingest_cmd = sub.add_parser("ingest", help="validate candidate JSONL into reviewable proposals")
    ingest_cmd.add_argument("--min-confidence", type=float, default=0.0)
    ingest_cmd.add_argument("--resolve", choices=["drop", "last", "true", "false"], default="drop")

    proposals = sub.add_parser("proposals", help="list proposals with their review status")
    proposals.add_argument("--status", choices=["pending", "approved", "rejected", "all"], default="pending")
    proposals.add_argument("--relation")
    proposals.add_argument("--limit", type=int)
    proposals.add_argument("--full", action="store_true", help="include provenance (default: compact)")

    review = sub.add_parser("review", help="review gate over pending proposals")
    review_sub = review.add_subparsers(dest="review_command", required=True)

    review_list = review_sub.add_parser("list", help="alias of `proposals`")
    review_list.add_argument("--status", choices=["pending", "approved", "rejected", "all"], default="pending")
    review_list.add_argument("--relation")
    review_list.add_argument("--limit", type=int)

    review_approve = review_sub.add_parser("approve", help="approve proposals by id (or unique prefix)")
    review_approve.add_argument("ids", nargs="+")
    review_approve.add_argument("--reviewer", default=DEFAULT_REVIEWER)
    review_approve.add_argument("--note", default="")

    review_reject = review_sub.add_parser("reject", help="reject proposals by id (or unique prefix)")
    review_reject.add_argument("ids", nargs="+")
    review_reject.add_argument("--reviewer", default=DEFAULT_REVIEWER)
    review_reject.add_argument("--note", default="")

    review_all = review_sub.add_parser("all", help="apply one decision to every proposal matching a filter")
    review_all.add_argument("--decision", choices=["approved", "rejected"], required=True)
    review_all.add_argument("--status", choices=["pending", "approved", "rejected"], default="pending")
    review_all.add_argument("--relation")
    review_all.add_argument("--reviewer", default=DEFAULT_REVIEWER)
    review_all.add_argument("--note", default="")

    review_reset = review_sub.add_parser("reset", help="clear review decisions")
    review_reset.add_argument("ids", nargs="*")

    review_apply = review_sub.add_parser("apply", help="apply decisions from a JSONL/YAML file")
    review_apply.add_argument("path")
    review_apply.add_argument("--reviewer", default=DEFAULT_REVIEWER)

    review_render = review_sub.add_parser("render", help="write review_pending.md checklist")
    review_render.add_argument("--limit", type=int)

    review_sub.add_parser("summary", help="print review counts")

    compile_cmd = sub.add_parser("compile", help="compile approved proposals into WiGame YAML")
    compile_cmd.add_argument("--allow-unreviewed", action="store_true", help="include pending proposals (audited in facts)")
    compile_cmd.add_argument("--max-projection-pairs", type=int, default=2000)

    verify_cmd = sub.add_parser("verify", help="re-check every fact through the runtime")
    verify_cmd.add_argument("--fail-on-problems", action="store_true")

    query_cmd = sub.add_parser("query", help="evaluate canonical s-expressions")
    query_cmd.add_argument("expressions", nargs="+")

    sub.add_parser("contexts", help="print the context tree")

    sub.add_parser("capabilities", help="probe upserts, inference, queries, sense, serialization")

    software = sub.add_parser("software", help="build a KB from a software corpus (AST, context=module)")
    software.add_argument("--path", action="append", required=True, help="file or dir relative to repo root (repeatable)")
    software.add_argument("--base", default=".", help="base dir for --path resolution")
    software.add_argument("--include-tests", action="store_true")
    software.add_argument("--include-harness", action="store_true")
    software.add_argument("--all-imports", action="store_true", help="keep stdlib/external imports")

    machine = sub.add_parser("machine", help="build a KB from machine/recipe specs (context=machine)")
    machine.add_argument("--spec-dir", default=None)
    machine.add_argument("--operatoria-dir", default=None)

    reach = sub.add_parser("reachability", help="closure vs BFS oracle, cycles, unreachable states, equivalence")
    reach.add_argument("--context", help="single context (default: all)")
    reach.add_argument("--relation", default="precede")

    shared = sub.add_parser("shared", help="symbols shared across contexts (cross-context referents)")
    shared.add_argument("--symbol", help="filter by symbol id")
    shared.add_argument("--relation", help="filter by relation")
    shared.add_argument("--axis", choices=["subject", "object"])

    aliases = sub.add_parser("aliases", help="curate context-scoped aliases (kb/aliases.yaml)")
    aliases.add_argument("--add", action="append", help="<context>:<symbol>=<canonical> (repeatable)")
    aliases.add_argument("--list", action="store_true")

    stress = sub.add_parser("stress", help="synthetic stress-test over many contexts/WiGames")
    stress.add_argument("--contexts", type=int, default=50)
    stress.add_argument("--relations", type=int, default=3)
    stress.add_argument("--own-refs", type=int, default=6)
    stress.add_argument("--shared-refs", type=int, default=20)
    stress.add_argument("--contexts-per-shared-ref", type=int, default=5)
    stress.add_argument("--attrs-per-ref", type=int, default=6)
    stress.add_argument("--asserted-attrs", type=int, default=2)
    stress.add_argument("--seed", type=int, default=7)
    stress.add_argument("--root", default="kb/stress")
    stress.add_argument("--mode", choices=["synthetic", "wikipedia"], default="synthetic")
    stress.add_argument("--source", choices=["dbpedia", "wikipedia"], default="dbpedia")
    stress.add_argument("--category", help="wikipedia category (wikipedia mode)")
    stress.add_argument("--lang", default="en")
    stress.add_argument("--limit", type=int, default=300)
    stress.add_argument("--max-contexts", type=int, default=200)
    stress.add_argument("--attrs-per-member", type=int, default=6)

    route_cmd = sub.add_parser("route", help="multi-hop search across contexts via projections")
    route_cmd.add_argument("--source", required=True, help="source wigame id")
    route_cmd.add_argument("--terms", required=True, help="comma-separated source terms")
    route_cmd.add_argument("--projections", required=True, help="comma-separated projection ids (path)")
    route_cmd.add_argument("--target-terms", help="comma-separated target terms to intersect")

    sub.add_parser("report", help="print aggregated KB report")

    workers = sub.add_parser("workers", help="print the dispatch plan (chunk -> prompt -> output)")
    workers.add_argument("--source", required=True)

    args = parser.parse_args(argv)
    kb = KB(Path(args.kb)).ensure()

    if args.command == "fetch":
        _print(write_source(kb, fetch_wikipedia(args.title, lang=args.lang, intro_only=args.intro_only)))
        return 0

    if args.command == "prepare":
        sources = [args.source] if args.source else kb.source_slugs()
        _print([prepare(kb, slug, args.max_chars, kb.load_relations()) for slug in sources])
        return 0

    if args.command == "ingest":
        _print(ingest(kb, min_confidence=args.min_confidence, resolve=args.resolve))
        return 0

    if args.command == "proposals":
        rows = _proposal_view(kb, args.status, args.relation, args.limit, compact=not args.full)
        _print({"count": len(rows), "proposals": rows})
        return 0

    if args.command == "review":
        if args.review_command == "list":
            rows = _proposal_view(kb, args.status, args.relation, args.limit, compact=True)
            _print({"count": len(rows), "proposals": rows})
            return 0
        if args.review_command == "approve":
            _print(decide(kb, args.ids, "approved", args.reviewer, args.note))
            return 0
        if args.review_command == "reject":
            _print(decide(kb, args.ids, "rejected", args.reviewer, args.note))
            return 0
        if args.review_command == "all":
            _print(
                decide_filtered(
                    kb,
                    args.decision,
                    args.reviewer,
                    note=args.note,
                    status=args.status,
                    relation=args.relation,
                )
            )
            return 0
        if args.review_command == "reset":
            _print(reset(kb, args.ids or None))
            return 0
        if args.review_command == "apply":
            _print(apply_file(kb, Path(args.path), args.reviewer))
            return 0
        if args.review_command == "render":
            path = render_pending(kb, args.limit)
            _print({"path": str(path), "summary": summary(kb)})
            return 0
        if args.review_command == "summary":
            _print(summary(kb))
            return 0

    if args.command == "compile":
        manifest = compile_kb(
            kb, allow_unreviewed=args.allow_unreviewed, max_projection_pairs=args.max_projection_pairs
        )
        _print(
            {
                "totals": manifest["totals"],
                "excluded": manifest["excluded"],
                "review": manifest["review"]["by_status"],
                "projections_truncated": manifest.get("projections_truncated", False),
            }
        )
        return 0

    if args.command == "verify":
        payload = verify(kb)
        _print(payload)
        if args.fail_on_problems and not payload["ok"]:
            return 1
        return 0

    if args.command == "query":
        _print(query(kb, args.expressions))
        return 0

    if args.command == "contexts":
        _print(contexts_view(kb))
        return 0

    if args.command == "route":
        _print(
            route(
                kb,
                source_wigame_id=args.source,
                source_terms=[term.strip() for term in args.terms.split(",") if term.strip()],
                path=[pid.strip() for pid in args.projections.split(",") if pid.strip()],
                target_terms=[term.strip() for term in args.target_terms.split(",") if term.strip()]
                if args.target_terms
                else None,
            )
        )
        return 0

    if args.command == "stress":
        import shutil

        from tools.kb.stress import Scale, benchmark, disambiguation_curve, run_scales  # noqa: E402
        from tools.kb.store import slugify  # noqa: E402

        if args.mode == "wikipedia":
            if not args.category:
                parser.error("wikipedia mode requires --category")
            from tools.kb.stresswiki import generate_dbpedia, generate_wikipedia  # noqa: E402

            kb = KB((Path(args.root) / f"wiki_{slugify(args.category)}").resolve())
            if kb.root.exists():
                shutil.rmtree(kb.root)
            if args.source == "dbpedia":
                generated = generate_dbpedia(
                    kb,
                    category=args.category,
                    limit=args.limit,
                    max_contexts=args.max_contexts,
                    attrs_per_member=args.attrs_per_member,
                )
            else:
                generated = generate_wikipedia(
                    kb,
                    category=args.category,
                    lang=args.lang,
                    limit=args.limit,
                    max_contexts=args.max_contexts,
                    attrs_per_member=args.attrs_per_member,
                )
            measured = benchmark(kb, Scale(contexts=generated["contexts"], relations=1, seed=args.seed))
            measured["generated"] = generated
            measured["disambiguation_curve"] = disambiguation_curve(kb)
            write_json(kb.root / "stress_report.json", {"measured_at": now(), **measured})
            _print({"results": [measured]})
            return 0

        scale = Scale(
            contexts=args.contexts,
            relations=args.relations,
            own_refs_per_context=args.own_refs,
            shared_refs=args.shared_refs,
            contexts_per_shared_ref=args.contexts_per_shared_ref,
            attrs_per_ref=args.attrs_per_ref,
            asserted_attrs=args.asserted_attrs,
            seed=args.seed,
        )
        _print(run_scales([scale], root=args.root))
        return 0

    if args.command == "software":
        from tools.kb.software import generate_software  # noqa: E402

        _print(
            generate_software(
                kb,
                roots=args.path,
                base=Path(args.base),
                include_tests=args.include_tests,
                include_kb_harness=args.include_harness,
                internal_only=not args.all_imports,
            )
        )
        return 0

    if args.command == "machine":
        from tools.kb.machine import generate_machines  # noqa: E402

        _print(
            generate_machines(
                kb,
                machines_dir=Path(args.spec_dir) if args.spec_dir else None,
                operatoria_dir=Path(args.operatoria_dir) if args.operatoria_dir else None,
            )
        )
        return 0

    if args.command == "reachability":
        from tools.kb.reach import analyze, analyze_all  # noqa: E402

        _print(analyze(kb, args.context, args.relation) if args.context else analyze_all(kb, args.relation))
        return 0

    if args.command == "shared":
        payload = load_yaml(kb.shared_path).get("shared_symbols", {}) if kb.shared_path.exists() else {}
        rows: list[dict[str, Any]] = []
        for relation, axes in sorted(payload.items()):
            if args.relation and relation != args.relation:
                continue
            for axis, entries in sorted(axes.items()):
                if args.axis and axis != args.axis:
                    continue
                for symbol, contexts in sorted(entries.items()):
                    if args.symbol and symbol != args.symbol:
                        continue
                    rows.append({"relation": relation, "axis": axis, "symbol": symbol, "contexts": contexts})
        _print({"count": len(rows), "shared": rows})
        return 0

    if args.command == "aliases":
        from tools.kb.store import dump_yaml  # noqa: E402

        entries = kb.load_aliases()
        if args.add:
            for raw in args.add:
                head, _, canonical = raw.partition("=")
                context, _, symbol = head.partition(":")
                if not (context and symbol and canonical):
                    parser.error(f"bad alias spec: {raw!r} (expected <context>:<symbol>=<canonical>)")
                entries = [
                    entry
                    for entry in entries
                    if not (entry["context"] == context and entry["symbol"] == symbol)
                ]
                entries.append({"context": context, "symbol": symbol, "canonical": canonical})
            dump_yaml(kb.aliases_path, {"aliases": entries})
        _print({"count": len(entries), "aliases": entries if args.list or not args.add else []})
        return 0

    if args.command == "capabilities":
        from tools.kb.capabilities import run as run_capabilities  # noqa: E402

        payload = run_capabilities(kb if kb.wigame_paths() else None)
        write_json(kb.root / "capabilities_report.json", payload)
        _print(payload)
        return 0 if payload["failed"] == 0 else 1

    if args.command == "report":
        _print(report(kb))
        return 0

    if args.command == "workers":
        index_path = kb.work_dir / args.source / "index.json"
        if not index_path.exists():
            parser.error(f"no prepared work for source {args.source!r}; run prepare first")
        index = json.loads(index_path.read_text(encoding="utf-8"))
        _print(
            [
                {"chunk_id": chunk["chunk_id"], "prompt": chunk.get("prompt_path"), "output": chunk["output_path"]}
                for chunk in index.get("chunks", [])
            ]
        )
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
