"""Domain operatoria: how to read content as a machine.

The operatoria is **authored**, not extracted: it declares relations, their
algebra, the admissible operations, and the typed errors for one domain. It is
the infra layer that `compile` consults to decide which closures to apply and
which validations to run.

It is also materialized into the KB as `ctx:operatoria`, so the spec is itself
queryable (`wigame:operatoria:declara`).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .store import KB, dump_yaml, load_yaml, write_jsonl

DEFAULT_OPERATORIA_DIR = Path(__file__).resolve().parent / "operatoria"

DECLARATIONS = {"declara": "declares", "aplica": "applies", "tipifica": "types"}


def default_specs(directory: Path | None = None) -> list[dict[str, Any]]:
    directory = directory or DEFAULT_OPERATORIA_DIR
    return [load_yaml(path) for path in sorted(directory.glob("*.yaml"))]


def merge(specs: list[dict[str, Any]]) -> dict[str, Any]:
    """Merges operatoria specs; relation algebra conflicts are hard errors."""

    relations: dict[str, dict[str, Any]] = {}
    operations: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    domains: list[str] = []
    for spec in specs:
        domain = spec["domain"]
        domains.append(domain)
        for relation_id, profile in spec.get("relations", {}).items():
            existing = relations.setdefault(relation_id, {"name": profile.get("name", relation_id)})
            for flag in ("transitive", "commutative", "associative", "distributive"):
                if flag in profile:
                    if flag in existing and existing[flag] != bool(profile[flag]):
                        raise ValueError(
                            f"operatoria conflict for {relation_id}.{flag}: {existing[flag]} vs {profile[flag]}"
                        )
                    existing[flag] = bool(profile[flag])
            existing.setdefault("domains", [])
            if domain not in existing["domains"]:
                existing["domains"].append(domain)
        for operation in spec.get("operations", []):
            operations.append({**operation, "domain": domain})
        for error in spec.get("errors", []):
            errors.append({**error, "domain": domain})
    return {"domains": sorted(set(domains)), "relations": relations, "operations": operations, "errors": errors}


def load(kb: KB, directory: Path | None = None) -> dict[str, Any]:
    """Loads the merged operatoria for a KB (written at build time, else defaults)."""

    if kb.operatoria_path.exists():
        return load_yaml(kb.operatoria_path) or {}
    return merge(default_specs(directory))


def algebra_for(kb: KB, directory: Path | None = None) -> dict[str, dict[str, bool]]:
    """Returns {relation: {transitive, commutative}} for the KB."""

    merged = load(kb, directory)
    return {
        relation: {
            "transitive": bool(profile.get("transitive", False)),
            "commutative": bool(profile.get("commutative", False)),
        }
        for relation, profile in merged.get("relations", {}).items()
    }


def write(kb: KB, specs: list[dict[str, Any]]) -> dict[str, Any]:
    """Persists the merged operatoria and the flat relation profile."""

    merged = merge(specs)
    dump_yaml(kb.operatoria_path, merged)
    relations = {
        relation: {
            "name": profile.get("name", relation),
            "transitive": bool(profile.get("transitive", False)),
            "commutative": bool(profile.get("commutative", False)),
        }
        for relation, profile in merged["relations"].items()
    }
    for declaration in DECLARATIONS:
        relations.setdefault(declaration, {"name": DECLARATIONS[declaration], "transitive": False, "commutative": False})
    dump_yaml(kb.relations_path, {"relations": relations})
    return merged


def materialize(kb: KB, merged: dict[str, Any]) -> int:
    """Writes the operatoria as a normal context (`ctx:operatoria`)."""

    context = "operatoria"
    sentences: list[str] = []
    rows: list[dict[str, Any]] = []

    def emit(relation: str, subject: str, obj: str) -> None:
        sentence = f"{relation} {subject} {obj}"
        sentences.append(sentence)
        rows.append(
            {
                "relation": relation,
                "subject": subject,
                "object": obj,
                "truth": True,
                "sentence": sentence,
                "source": context,
                "chunk_id": f"{context}/000",
                "revid": 1,
                "confidence": 1.0,
            }
        )

    for relation_id, profile in sorted(merged["relations"].items()):
        algebra = "transitiva" if profile.get("transitive") else "conmutativa" if profile.get("commutative") else "simple"
        emit("declara", relation_id, algebra)
    for operation in merged["operations"]:
        emit("aplica", operation["id"], operation["kind"])
    for error in merged["errors"]:
        emit("tipifica", error["domain"], error["id"])

    (kb.work_dir / context).mkdir(parents=True, exist_ok=True)
    (kb.work_dir / context / "000.txt").write_text("\n".join(sentences) + "\n", encoding="utf-8")
    write_jsonl(kb.candidates_dir / context / "000.jsonl", rows)
    return len(rows)
