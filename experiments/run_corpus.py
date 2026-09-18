"""Run the whole pipeline over one corpus and verify what was written and read."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys
import time
import unicodedata
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.append(str(_REPO_ROOT))

from populator import build_corpus, read_documents
from populator.tokenize import normalize
from pipeline.run import build_system, peak_memory_mb

DERIVABLE_TIERS = {"observed", "confirmed"}


def main(argv: list[str] | None = None) -> int:
    """Runs the experiment for one corpus and writes its artifacts."""

    parser = argparse.ArgumentParser(description="Populate a WiGame from a corpus and verify it.")
    parser.add_argument("corpus", help="directory or file to read")
    parser.add_argument("--wigame", required=True)
    parser.add_argument("--lang", choices=["es", "en"], default=None)
    parser.add_argument("--max-concepts", type=int, default=800)
    parser.add_argument("--max-facts", type=int, default=3000)
    parser.add_argument("--max-nonsense", type=int, default=500)
    parser.add_argument("--max-classes", type=int, default=15)
    parser.add_argument("--hierarchy-concepts", type=int, default=120)
    parser.add_argument("--min-confirmed", type=int, default=30)
    parser.add_argument("--recursive", action="store_true")
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {}

    start = time.perf_counter()
    documents = read_documents(args.corpus, recursive=args.recursive)
    corpus = build_corpus(documents, lang=args.lang, max_concepts=args.max_concepts)
    populator_seconds = round(time.perf_counter() - start, 3)

    system, runtime, results = build_system(
        args.corpus,
        args.wigame,
        corpus=corpus,
        documents=documents,
        lang=args.lang,
        max_concepts=args.max_concepts,
        max_fact_candidates=args.max_facts,
        max_nonsense=args.max_nonsense,
        max_class_candidates=args.max_classes,
        hierarchy_max_concepts=args.hierarchy_concepts,
        recursive=args.recursive,
        report=report,
    )
    report["populator_seconds"] = populator_seconds
    wigame = system.wigames[f"wigame:{args.wigame}"]
    identity = f"wigame:{args.wigame}"
    promoted = ensure_confirmed(system, runtime, identity, args.min_confirmed)
    confirmed = confirmed_facts(system, identity)
    report["promoted_for_retrieval"] = promoted
    report["confirmed_facts"] = len(confirmed)
    report["true_facts"] = len(confirmed)
    report["candidates_by_kind"] = dict(Counter(candidate.kind for candidate in system.candidates.values()))
    report["peak_memory_mb"] = round(peak_memory_mb(), 1)
    (out / "stats.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    _write_rules(out / "rules_top.md", system, identity)
    retrieval = _write_retrieval(out / "retrieval.md", system, runtime, identity, documents)
    _write_queries(out / "queries.md", system, runtime, corpus, identity)
    persistence = _write_persistence(out, system, runtime, wigame, identity)
    _write_system_extras(out, system)

    report["retrieval_total_spans"] = retrieval["total"]
    report["retrieval_correct_spans"] = retrieval["correct"]
    report["retrieval_percent"] = retrieval["percent"]
    report["persistence_identical"] = persistence["identical"]
    (out / "stats.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps({key: report[key] for key in (
        "documents", "sentences", "concepts", "sexprs", "candidates_by_kind",
        "confirmed_facts", "promoted_for_retrieval", "retrieval_percent",
        "persistence_identical", "total_seconds", "peak_memory_mb",
    )}, ensure_ascii=False))
    return 0


def confirmed_facts(system, wigame_id: str) -> list:
    """Returns the TRUE facts with a confirmed or observed tier."""

    return [
        fact
        for fact in system.wigames[wigame_id].facts.values()
        if fact.truth.value == "true" and fact.evidence.get("tier") in DERIVABLE_TIERS
    ]


def ensure_confirmed(system, runtime, wigame_id: str, minimum: int) -> int:
    """Promotes the highest-intensity queued rules until ``minimum`` facts exist."""

    promoted = 0
    while len(confirmed_facts(system, wigame_id)) < minimum:
        pending = [
            candidate
            for candidate in system.candidates.values()
            if candidate.kind == "fact" and candidate.evidence.get("curation") == "proposed"
        ]
        if not pending:
            break
        pending.sort(key=lambda candidate: -candidate.evidence["stats"]["phi_entropic"])
        candidate = pending[0]
        result = runtime.evaluate(f"(promote {candidate.candidate_id})")
        if result.status != "accept":
            candidate.evidence["curation"] = "rejected"
            continue
        promoted += 1
    return promoted


def rule_rows(system) -> list[dict]:
    """Returns every queued implication rule with its statistics."""

    rows: list[dict] = []
    for candidate in system.candidates.values():
        if candidate.kind != "fact":
            continue
        stats = candidate.evidence.get("stats", {})
        relation, a, b = _parse_proposition(candidate.payload["proposition"])
        rows.append(
            {
                "a": a,
                "b": b,
                "phi": stats.get("phi"),
                "phi_entropic": stats.get("phi_entropic"),
                "confidence": stats.get("confidence"),
                "n_a": stats.get("n_a"),
                "n_b": stats.get("n_b"),
                "curation": candidate.evidence.get("curation"),
                "candidate_id": candidate.candidate_id,
            }
        )
    rows.sort(key=lambda row: -row["phi_entropic"])
    return rows


def _parse_proposition(sexpr: str) -> tuple[str, str, str]:
    return tuple(sexpr.strip("()").split())  # type: ignore[return-value]


def _write_rules(path: Path, system, wigame_id: str) -> None:
    rows = rule_rows(system)[:40]
    lines = [f"# Reglas de mayor φ — {wigame_id}", ""]
    lines.append("| a | b | φ entrópica | φ clásica | conf | n_a | n_b | curaduría |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for row in rows:
        lines.append(
            f"| {row['a']} | {row['b']} | {row['phi_entropic']:.4f} | {row['phi']:.4f} | "
            f"{row['confidence']:.3f} | {row['n_a']} | {row['n_b']} | {row['curation']} |"
        )
    classes = [candidate for candidate in system.candidates.values() if candidate.kind == "class"]
    lines.extend(["", "## Clases de niveles significativos", ""])
    for candidate in classes[:15]:
        symbols = " ".join(candidate.payload["symbols"])
        cohesion = candidate.evidence.get("stats", {}).get("cohesion")
        lines.append(f"- `{candidate.payload['class_id']}` ({symbols}) — cohesión {cohesion:.4f}")
    if not classes:
        lines.append("- (sin clases: corpus con menos conceptos que el tope de jerarquía)")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_retrieval(path: Path, system, runtime, wigame_id: str, documents) -> dict:
    by_id = {document.document_id: document for document in documents}
    phi_by_proposition = {
        candidate.payload["proposition"]: candidate.evidence.get("stats", {}).get("phi_entropic", 0.0)
        for candidate in system.candidates.values()
        if candidate.kind == "fact"
    }
    facts = sorted(
        confirmed_facts(system, wigame_id),
        key=lambda fact: -phi_by_proposition.get(fact.proposition.sexpr(), 0.0),
    )[:30]
    total = correct = 0
    examples: list[str] = []
    for fact in facts:
        subject = fact.proposition.subject_symbol_id
        obj = fact.proposition.object_symbol_id
        signs_a = {subject} | (system.symbols[subject].signs if subject in system.symbols else set())
        signs_b = {obj} | (system.symbols[obj].signs if obj in system.symbols else set())
        chain = runtime.evaluate(f"(why {wigame_id} {fact.proposition.sexpr()})").payload["chain"]
        node = chain[0] if chain else {}
        for prov in node.get("prov", []):
            total += 1
            if _span_matches(prov, subject, signs_a, obj, signs_b, by_id):
                correct += 1
        if len(examples) < 10 and node.get("prov"):
            prov = node["prov"][0]
            document = by_id.get(prov["document_id"])
            snippet = document.text[prov["span"][0] : prov["span"][1]] if document else ""
            examples.append(
                f"- `{fact.proposition.sexpr()}` — {prov['document_id']} "
                f"[{prov['span'][0]}:{prov['span'][1]}]: «{snippet.strip()}»"
            )
    percent = round(100.0 * correct / total, 2) if total else 0.0
    lines = [
        f"# Recuperación con procedencia — {wigame_id}",
        "",
        f"Hechos confirmados verificados: {len(facts)}. Spans comprobados: {total}. "
        f"Correctos (contienen una forma superficial de `a` y de `b`): {correct} ({percent}%).",
        "",
        "## Ejemplos",
        "",
        *examples,
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"total": total, "correct": correct, "percent": percent}


def _span_matches(prov: dict, concept_a: str, signs_a, concept_b: str, signs_b, by_id: dict) -> bool:
    document = by_id.get(prov["document_id"])
    if document is None:
        return False
    start, end = prov["span"]
    text = _fold_keep(document.text[start:end])
    return _present(text, signs_a, concept_a) and _present(text, signs_b, concept_b)


def _fold_keep(text: str) -> str:
    """Lowercases and strips accents but keeps separators for token matching."""

    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(char for char in decomposed if not unicodedata.combining(char)).lower()


def _present(text: str, signs, concept: str) -> bool:
    """Checks that a token sequence of the concept appears in the span text."""

    for surface in list(signs) + [concept]:
        pattern = _surface_pattern(surface)
        if pattern is not None and pattern.search(text):
            return True
    return False


def _surface_pattern(surface: str):
    tokens = [normalize(part) for part in surface.split("_")]
    tokens = [token for token in tokens if token]
    if not tokens:
        return None
    return re.compile(r"[^0-9a-z]*".join(re.escape(token) for token in tokens))


def _write_queries(path: Path, system, runtime, corpus, wigame_id: str) -> None:
    support = corpus.X.sum(axis=0).A1
    order = sorted(range(len(corpus.concepts)), key=lambda index: -support[index])[:10]
    lines = [f"# Consultas de retorno — {wigame_id}", "", "## Conceptos más frecuentes", ""]
    for index in order:
        concept = corpus.concepts[index]
        result = runtime.evaluate(f"(return facts symbol:{concept} wigame:{wigame_id})")
        count = sum(len(group["facts"]) for group in result.payload["groups"])
        lines.append(f"- `{concept}` (soporte {int(support[index])}): {count} hechos")
    confirmed_rows = [row for row in rule_rows(system) if row["curation"] == "confirmed"][:5]
    lines.extend(["", "## check sobre reglas confirmadas", ""])
    for row in confirmed_rows:
        result = runtime.evaluate(f"(check {wigame_id} (implies {row['a']} {row['b']}))")
        lines.append(f"- `(implies {row['a']} {row['b']})` → {result.payload['truth']}")
    nonsense = [candidate for candidate in system.candidates.values() if candidate.kind == "nonsense"][:5]
    lines.extend(["", "## check sobre pares nonsense", ""])
    for candidate in nonsense:
        relation, a, b = _parse_proposition(candidate.payload["proposition"])
        result = runtime.evaluate(f"(check {wigame_id} ({relation} {a} {b}))")
        lines.append(f"- `({relation} {a} {b})` → {result.payload['truth']} (esperado ∅/false)")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_persistence(path: Path, system, runtime, wigame, wigame_id: str) -> dict:
    world = path / "world.yaml"
    world.write_text(wigame.to_yaml(), encoding="utf-8")

    from src.operational_model import LogicalSystem, SExpressionRuntime, WiGame

    restored = WiGame.from_yaml(world.read_text(encoding="utf-8"))
    new_system = LogicalSystem()
    new_system.register_wigame(restored)
    new_runtime = SExpressionRuntime(new_system)

    rows = [row for row in rule_rows(system) if row["curation"] == "confirmed"][:5]
    checks: list[bool] = []
    for row in rows:
        before = runtime.evaluate(f"(check {wigame_id} (implies {row['a']} {row['b']}))").payload
        after = new_runtime.evaluate(f"(check {wigame_id} (implies {row['a']} {row['b']}))").payload
        checks.append(before == after)

    confirmed = sorted(
        confirmed_facts(system, wigame_id),
        key=lambda fact: fact.proposition.sexpr(),
    )[:3]
    whys: list[bool] = []
    for fact in confirmed:
        before = runtime.evaluate(f"(why {wigame_id} {fact.proposition.sexpr()})").payload
        after = new_runtime.evaluate(f"(why {wigame_id} {fact.proposition.sexpr()})").payload
        whys.append(before == after)

    identical = bool(checks) and all(checks) and all(whys)
    lines = [
        f"# Persistencia — {wigame_id}",
        "",
        f"`world.yaml`: {world.stat().st_size} bytes.",
        f"checks idénticos: {sum(checks)}/{len(checks)}. why idénticos: {sum(whys)}/{len(whys)}.",
        f"Resultado: {'idéntico' if identical else 'DIVERGENTE'}.",
    ]
    (path / "persistence.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"identical": identical, "checks": checks, "whys": whys}


def _write_system_extras(path: Path, system) -> None:
    import yaml

    payload = {
        "rules": [rule.to_sexpr() for rule in system.rules],
        "candidates": [
            {
                "candidate_id": candidate.candidate_id,
                "kind": candidate.kind,
                "wigame_id": candidate.wigame_id,
                "payload": candidate.payload,
                "evidence": candidate.evidence,
            }
            for candidate in system.candidates.values()
        ],
    }
    (path / "system_extras.yaml").write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )


if __name__ == "__main__":
    raise SystemExit(main())
