"""Stress-test harness for context indexing and context-crossing disambiguation.

Two independent questions are measured:

1. Engineering: how do compile/load/verify/route costs and artifact counts scale
   with contexts x relations x facts, and where do dense projections blow up.
2. Epistemology: does accumulating contexts identify a homonym referent? Each
   context asserts a random subset of the referent's true attribute profile, so
   the union of asserted attributes grows with the number of contexts and
   separates the true referent from its homonyms.

Synthetic data is used because the hypothesis is about structure, not about any
particular corpus: ground truth (referent per occurrence + true profiles) is
known, which real extraction can never provide.
"""

from __future__ import annotations

import random
import resource
import shutil
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .compile import compile_kb
from .ingest import ingest
from .review import decide_filtered
from .runtime import load_system, route, verify
from .store import KB, dump_yaml, load_yaml, now, write_json, write_jsonl

SURFACES = ["Smith", "Jones", "Lee", "Chen", "Garcia", "Muller", "Rossi", "Kim", "Novak", "Silva"]


@dataclass
class Scale:
    contexts: int = 50
    relations: int = 3
    own_refs_per_context: int = 6
    shared_refs: int = 20
    contexts_per_shared_ref: int = 5
    attrs_per_ref: int = 6
    asserted_attrs: int = 2
    seed: int = 7


def generate(kb: KB, scale: Scale) -> dict[str, Any]:
    """Writes synthetic candidates + chunk text + ground truth for one scale."""

    rng = random.Random(scale.seed)
    kb.ensure()
    relations = [f"rel_{index}" for index in range(scale.relations)]
    dump_yaml(kb.relations_path, {"relations": {rel: {"name": rel} for rel in relations}})
    attrs = [f"attr_{index}" for index in range(max(scale.attrs_per_ref * 3, 12))]

    referents: dict[str, dict[str, Any]] = {}
    for ctx_index in range(scale.contexts):
        for ref_index in range(scale.own_refs_per_context):
            ref_id = f"own_{ctx_index}_{ref_index}"
            referents[ref_id] = {
                "surfaces": [f"Own{ctx_index}X{ref_index}"],
                "profile": set(rng.sample(attrs, scale.attrs_per_ref)),
            }
    for shared_index in range(scale.shared_refs):
        ref_id = f"shared_{shared_index}"
        referents[ref_id] = {
            "surfaces": rng.sample(SURFACES, rng.randint(1, 2)),
            "profile": set(rng.sample(attrs, scale.attrs_per_ref)),
        }

    # occurrences: which referents appear in which context
    occurrences: dict[str, list[str]] = {f"ctx_{index:04d}": [] for index in range(scale.contexts)}
    for ref_id in [key for key in referents if key.startswith("own_")]:
        ctx_index = int(ref_id.split("_")[1])
        occurrences[f"ctx_{ctx_index:04d}"].append(ref_id)
    shared_ids = [key for key in referents if key.startswith("shared_")]
    for ref_id in shared_ids:
        for context in rng.sample(sorted(occurrences), min(scale.contexts_per_shared_ref, scale.contexts)):
            occurrences[context].append(ref_id)

    truth: dict[str, Any] = {"referents": {}, "occurrences": []}
    for ref_id, payload in referents.items():
        truth["referents"][ref_id] = {"surface": payload["surfaces"][0], "profile": sorted(payload["profile"])}

    total_rows = 0
    for context, ref_ids in sorted(occurrences.items()):
        sentences: list[str] = []
        rows: list[dict[str, Any]] = []
        chunk_id = f"{context}/000"
        for ref_id in sorted(ref_ids):
            payload = referents[ref_id]
            surface = rng.choice(payload["surfaces"])
            asserted = sorted(rng.sample(sorted(payload["profile"]), min(scale.asserted_attrs, len(payload["profile"]))))
            for attr in asserted:
                sentence = f"{surface} is {attr}."
                sentences.append(sentence)
                rows.append(
                    {
                        "relation": rng.choice(relations),
                        "subject": surface,
                        "object": attr,
                        "truth": True,
                        "sentence": sentence,
                        "source": context,
                        "chunk_id": chunk_id,
                        "revid": 1,
                        "confidence": 0.9,
                    }
                )
            truth["occurrences"].append(
                {"context": context, "surface": surface, "referent": ref_id, "asserted": asserted}
            )
        (kb.work_dir / context).mkdir(parents=True, exist_ok=True)
        (kb.work_dir / context / "000.txt").write_text("\n".join(sentences) + "\n", encoding="utf-8")
        write_jsonl(kb.candidates_dir / context / "000.jsonl", rows)
        total_rows += len(rows)

    dump_yaml(kb.root / "stress_truth.yaml", truth)
    return {"rows": total_rows, "contexts": len(occurrences), "referents": len(referents), "relations": relations}


def disambiguation_curve(kb: KB, repeats: int = 10) -> list[dict[str, Any]]:
    """Identification rate of a homonym referent as its contexts accumulate.

    For each surface shared by several referents (homonyms), we accumulate the
    attributes asserted for one referent across k contexts and ask whether the
    accumulated set leaves only that referent standing among its homonyms.
    """

    truth = load_yaml(kb.root / "stress_truth.yaml")
    profiles = {ref: set(payload["profile"]) for ref, payload in truth["referents"].items()}
    candidates_by_surface: dict[str, set[str]] = {}
    occurrences: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for occurrence in truth["occurrences"]:
        candidates_by_surface.setdefault(occurrence["surface"], set()).add(occurrence["referent"])
        occurrences.setdefault((occurrence["surface"], occurrence["referent"]), []).append(occurrence)

    homonyms = {surface: refs for surface, refs in candidates_by_surface.items() if len(refs) > 1}
    if not homonyms:
        return []

    max_k = max((len(items) for items in occurrences.values()), default=0)
    curve: list[dict[str, Any]] = []
    for k in range(1, max_k + 1):
        trials = identified = survivor_total = 0
        for surface, refs in homonyms.items():
            for ref in sorted(refs):
                items = occurrences.get((surface, ref), [])
                if len(items) < k:
                    continue
                for repeat in range(repeats):
                    sample = random.Random(f"{surface}:{ref}:{k}:{repeat}").sample(items, k)
                    observed: set[str] = set()
                    for occurrence in sample:
                        observed |= set(occurrence["asserted"])
                    survivors = [candidate for candidate in sorted(refs) if observed <= profiles[candidate]]
                    trials += 1
                    survivor_total += len(survivors)
                    if survivors == [ref]:
                        identified += 1
        if trials == 0:
            continue
        curve.append(
            {
                "contexts_per_referent": k,
                "trials": trials,
                "identified": identified,
                "rate": round(identified / trials, 4),
                "survivors_mean": round(survivor_total / trials, 3),
            }
        )
    return curve


def benchmark(kb: KB, scale: Scale, route_samples: int = 25) -> dict[str, Any]:
    """Runs the real pipeline at scale and measures cost and artifact counts."""

    timings: dict[str, float] = {}

    start = time.perf_counter()
    report = ingest(kb)
    timings["ingest_s"] = round(time.perf_counter() - start, 3)

    start = time.perf_counter()
    decide_filtered(kb, "approved", "stress", note="synthetic")
    timings["review_s"] = round(time.perf_counter() - start, 3)

    start = time.perf_counter()
    manifest = compile_kb(kb)
    timings["compile_s"] = round(time.perf_counter() - start, 3)

    start = time.perf_counter()
    verify_report = verify(kb)
    timings["verify_s"] = round(time.perf_counter() - start, 3)

    route_latencies: list[float] = []
    hot_latencies: list[float] = []
    projection_ids = sorted(manifest.get("projections", {}))

    start = time.perf_counter()
    system = load_system(kb)
    timings["load_system_s"] = round(time.perf_counter() - start, 3)

    if projection_ids:
        from src.operational_model.system.logical_system_queries import route_search

        for _ in range(route_samples):
            projection_id = random.choice(projection_ids)
            source = manifest["projections"][projection_id]["source"]
            start = time.perf_counter()
            route_search(system, source, [], [projection_id])
            hot_latencies.append((time.perf_counter() - start) * 1000)

        # one cold call measures full hydration + routing
        start = time.perf_counter()
        route(kb, source_wigame_id=manifest["projections"][projection_ids[0]]["source"], source_terms=[], path=[projection_ids[0]])
        route_latencies.append((time.perf_counter() - start) * 1000)

    route_latencies.sort()
    hot_latencies.sort()

    sizes = {
        "proposals": len(kb.proposals()),
        "facts": len(kb.facts()),
        "wigames": len(kb.wigame_paths()),
        "projections": len(kb.projection_paths()),
        "contexts": len(manifest.get("contexts", {}).get("contexts", {})),
        "truncated": manifest.get("projections_truncated", False),
        "disk_mb": round(sum(path.stat().st_size for path in kb.root.rglob("*") if path.is_file()) / 1e6, 2),
    }
    return {
        "scale": scale.__dict__,
        "sizes": sizes,
        "timings_s": timings,
        "route_ms": {
            "cold": round(route_latencies[0], 3) if route_latencies else None,
            "hot_samples": len(hot_latencies),
            "hot_p50": round(hot_latencies[len(hot_latencies) // 2], 3) if hot_latencies else None,
            "hot_p95": round(hot_latencies[int(len(hot_latencies) * 0.95) - 1], 3) if hot_latencies else None,
        },
        "peak_rss_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1),
        "ingest": {key: report[key] for key in ("candidates", "accepted", "proposals", "rejected", "conflicts")},
        "verify_ok": verify_report["ok"],
    }


def run_scales(scales: list[Scale], root: str = "kb/stress", quiet: bool = False) -> dict[str, Any]:
    """Runs generate + benchmark for each scale, writing one report per scale."""

    results: list[dict[str, Any]] = []
    for index, scale in enumerate(scales):
        kb = KB((Path(root) / f"s{index}_ctx{scale.contexts}").resolve())
        if kb.root.exists():
            shutil.rmtree(kb.root)
        generated = generate(kb, scale)
        curve = disambiguation_curve(kb)
        measured = benchmark(kb, scale)
        measured["generated"] = generated
        measured["disambiguation_curve"] = curve
        payload = {"measured_at": now(), **measured}
        write_json(kb.root / "stress_report.json", payload)
        results.append(payload)
        if not quiet:
            print(
                f"[{scale.contexts} ctx] facts={measured['sizes']['facts']} wigames={measured['sizes']['wigames']} "
                f"projections={measured['sizes']['projections']} trunc={measured['sizes']['truncated']} "
                f"compile={measured['timings_s']['compile_s']}s load={measured['timings_s']['load_system_s']}s "
                f"hot_route_p50={measured['route_ms']['hot_p50']}ms rss={measured['peak_rss_mb']}MB",
                file=sys.stderr,
            )
    return {"results": results}
