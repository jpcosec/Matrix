"""Machine/recipe generator: contexts as state machines, steps as referents.

Deterministic, authored specs. Covers both FSMs (cycles expected) and recipes
(acyclic required). Relations come from the domain operatoria:

- `precede`  (step/state -> next state), transitive
- `requiere` (step -> precondition)
- `usa`      (step -> item/ingredient)
- `produce`  (step -> result)
- `sustituye_a` (item -> item), transitive
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import operatoria
from .store import KB, dump_yaml, load_yaml, slugify, write_jsonl

DEFAULT_MACHINES_DIR = Path(__file__).resolve().parent / "machines"


def load_specs(directory: Path | None = None) -> list[dict[str, Any]]:
    directory = directory or DEFAULT_MACHINES_DIR
    return [load_yaml(path) for path in sorted(directory.glob("*.yaml"))]


def generate_machines(
    kb: KB,
    *,
    machines_dir: Path | None = None,
    operatoria_dir: Path | None = None,
) -> dict[str, Any]:
    """Writes the operatoria context plus one context per machine/recipe spec."""

    kb.ensure()
    merged = operatoria.write(kb, operatoria.default_specs(operatoria_dir))
    operatoria_rows = operatoria.materialize(kb, merged)

    specs = load_specs(machines_dir)
    summary: list[dict[str, Any]] = []
    for spec in specs:
        context = slugify(spec["context"])
        sentences: list[str] = []
        rows: list[dict[str, Any]] = []

        def emit(relation: str, subject: str, obj: str, sentence: str | None = None) -> None:
            sentence = sentence or f"{subject} {relation} {obj}"
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

        for edge in spec.get("edges", []):
            emit("precede", edge["from"], edge["to"], edge.get("sentence"))
        for requirement in spec.get("requires", []):
            emit("requiere", requirement["step"], requirement["needs"], requirement.get("sentence"))
        for use in spec.get("uses", []):
            emit("usa", use["step"], use["item"], use.get("sentence"))
        for produced in spec.get("produces", []):
            emit("produce", produced["step"], produced["result"], produced.get("sentence"))
        for substitution in spec.get("sustituciones", []):
            emit("sustituye_a", substitution["from"], substitution["to"], substitution.get("sentence"))

        (kb.work_dir / context).mkdir(parents=True, exist_ok=True)
        (kb.work_dir / context / "000.txt").write_text("\n".join(sentences) + "\n", encoding="utf-8")
        write_jsonl(kb.candidates_dir / context / "000.jsonl", rows)
        summary.append(
            {
                "context": context,
                "domain": spec.get("domain"),
                "kind": spec.get("kind"),
                "title": spec.get("title", context),
                "initial": spec.get("initial"),
                "facts": len(rows),
            }
        )

    payload = {
        "kind": "machine-specs",
        "operatoria_context": "operatoria",
        "operatoria_facts": operatoria_rows,
        "machines": summary,
        "domains": merged.get("domains", []),
    }
    dump_yaml(kb.root / "machines_source.yaml", payload)
    return payload
