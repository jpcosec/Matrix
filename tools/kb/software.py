"""Software corpus generator: modules as contexts, symbols as referents.

Deterministic extraction with the `ast` module (no LLM), reusing the same
proposal -> review -> compile pipeline as the Wikipedia path.

Mapping:

- **context** = module (file) under the given roots
- **referent** = symbol (defined name, imported name, receiver, class, base)
- relations:
  - `define_en`  (symbol, class|def)     -> defined symbol and its kind
  - `usa`        (receiver, member)      -> member access `receiver.member`
  - `importa`    (name, import)          -> imported module/name
  - `hereda_de`  (class, base)           -> class inheritance

Every fact's `sentence` is the exact source line, so the harness validation
(verbatim substring of the chunk + subject/object present) applies unchanged.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, Iterable

from .store import KB, dump_yaml, slugify, write_jsonl

RELATIONS = {
    "define_en": {"name": "defined symbol", "transitive": False},
    "usa": {"name": "member access", "transitive": False},
    "importa": {"name": "imported name", "transitive": False},
    "hereda_de": {"name": "inherits from", "transitive": False},
}


def _context_id(path: Path, root: Path) -> str:
    relative = path.resolve().relative_to(root.resolve())
    return slugify(str(relative.with_suffix("")).replace("/", ".").replace("\\", "."))


def _line(source: str, lineno: int) -> str:
    lines = source.splitlines()
    return lines[lineno - 1].strip() if 0 < lineno <= len(lines) else ""


def _dotted(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _dotted(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return None


def extract_module(path: Path, root: Path) -> dict[str, Any]:
    """Extracts candidate rows for one module using its AST."""

    source = path.read_text(encoding="utf-8", errors="replace")
    context = _context_id(path, root)
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {"context": context, "source": source, "rows": [], "error": "syntax error"}

    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()

    def emit(relation: str, subject: str, obj: str, sentence: str) -> None:
        key = (relation, subject, obj)
        if key in seen or not sentence or len(subject) < 2 or len(obj) < 2:
            return
        if slugify(subject) == slugify(obj):
            return
        if subject not in sentence or obj not in sentence:
            return
        seen.add(key)
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

    for node in ast.walk(tree):
        lineno = getattr(node, "lineno", None)
        if lineno is None:
            continue
        line = _line(source, lineno)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            emit("define_en", node.name, "def", line)
        elif isinstance(node, ast.ClassDef):
            emit("define_en", node.name, "class", line)
            for base in node.bases:
                base_name = _dotted(base)
                if base_name:
                    emit("hereda_de", node.name, base_name.rsplit(".", 1)[-1], line)
        elif isinstance(node, ast.Attribute):
            receiver = _dotted(node.value)
            if receiver:
                emit("usa", receiver.rsplit(".", 1)[-1], node.attr, line)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                emit("importa", alias.name.rsplit(".", 1)[-1], "import", line)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name != "*":
                    emit("importa", alias.name, "import", line)

    return {"context": context, "source": source, "rows": rows, "error": None}


def generate_software(
    kb: KB,
    *,
    roots: Iterable[str],
    base: Path,
    include_tests: bool = True,
    include_kb_harness: bool = True,
    internal_only: bool = True,
) -> dict[str, Any]:
    """Writes module contexts + deterministic candidates into a KB directory."""

    kb.ensure()
    dump_yaml(kb.relations_path, {"relations": RELATIONS})

    module_paths: list[Path] = []
    for root in roots:
        target = (base / root).resolve()
        if target.is_file() and target.suffix == ".py":
            module_paths.append(target)
        elif target.is_dir():
            module_paths.extend(sorted(target.rglob("*.py")))
    if not include_tests:
        module_paths = [path for path in module_paths if "test" not in path.parts]
    if not include_kb_harness:
        module_paths = [path for path in module_paths if "tools/kb" not in str(path)]

    modules = [extract_module(path, base) for path in module_paths]
    modules = [module for module in modules if module["rows"]]

    dropped_imports = 0
    if internal_only:
        corpus_modules = {module["context"].rsplit("_", 1)[-1] for module in modules}
        defined = {
            slugify(row["subject"])
            for module in modules
            for row in module["rows"]
            if row["relation"] == "define_en"
        }
        known = corpus_modules | defined
        for module in modules:
            kept = []
            for row in module["rows"]:
                if row["relation"] == "importa" and slugify(row["subject"]) not in known:
                    dropped_imports += 1
                    continue
                kept.append(row)
            module["rows"] = kept
        modules = [module for module in modules if module["rows"]]

    total_rows = 0
    contexts: list[str] = []
    errors: list[str] = []
    for module in modules:
        context = module["context"]
        contexts.append(context)
        if module["error"]:
            errors.append(context)
        (kb.work_dir / context).mkdir(parents=True, exist_ok=True)
        (kb.work_dir / context / "000.txt").write_text(module["source"] + "\n", encoding="utf-8")
        write_jsonl(kb.candidates_dir / context / "000.jsonl", module["rows"])
        total_rows += len(module["rows"])

    summary = {
        "kind": "software-ast",
        "modules": len(modules),
        "contexts": len(contexts),
        "rows": total_rows,
        "dropped_external_imports": dropped_imports,
        "internal_only": internal_only,
        "errors": errors,
        "roots": list(roots),
    }
    dump_yaml(kb.root / "software_source.yaml", summary)
    return summary
