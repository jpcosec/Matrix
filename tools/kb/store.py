"""Store layout and IO helpers for the Wikipedia KB fan-out harness."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RELATIONS = Path(__file__).resolve().parent / "relations.yaml"


def slugify(text: str) -> str:
    """Converts a surface form into a stable lowercase symbol id."""

    normalized = unicodedata.normalize("NFKD", text or "")
    ascii_only = "".join(c for c in normalized if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "_", ascii_only.lower()).strip("_")


def now() -> str:
    """Returns an ISO-8601 UTC timestamp."""

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_text(text: str) -> str:
    """Hashes text content."""

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    """Hashes a file's bytes."""

    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fact_id(context: str, relation: str, subject: str, obj: str, truth: str) -> str:
    """Builds a deterministic fact identifier."""

    return "fact:" + sha256_text(f"{context}|{relation}|{subject}|{obj}|{truth}")[:12]


def proposal_id(context: str, relation: str, subject: str, obj: str, truth: str) -> str:
    """Builds a deterministic proposal identifier."""

    return "proposal:" + sha256_text(f"{context}|{relation}|{subject}|{obj}|{truth}")[:12]


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def dump_yaml(path: Path, payload: Any) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def read_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows, _ = read_jsonl_safe(path)
    return rows


def read_jsonl_safe(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Reads JSONL, returning (rows, unparseable_lines)."""

    rows: list[dict[str, Any]] = []
    bad: list[dict[str, Any]] = []
    if not Path(path).exists():
        return rows, bad
    for lineno, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            bad.append({"file": str(path), "line": lineno, "text": line[:200]})
    return rows, bad


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with Path(path).open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            count += 1
    return count


@dataclass
class KB:
    """Filesystem layout for one knowledge base."""

    root: Path

    def __post_init__(self) -> None:
        self.root = Path(self.root)

    @property
    def sources_dir(self) -> Path:
        return self.root / "sources"

    @property
    def work_dir(self) -> Path:
        return self.root / "work"

    @property
    def candidates_dir(self) -> Path:
        return self.root / "candidates"

    @property
    def proposals_dir(self) -> Path:
        return self.root / "proposals"

    @property
    def review_path(self) -> Path:
        return self.root / "review.yaml"

    @property
    def contexts_path(self) -> Path:
        return self.root / "contexts.yaml"

    @property
    def aliases_path(self) -> Path:
        return self.root / "aliases.yaml"

    @property
    def projections_dir(self) -> Path:
        return self.root / "projections"

    @property
    def facts_dir(self) -> Path:
        return self.root / "facts"

    @property
    def wigames_dir(self) -> Path:
        return self.root / "wigames"

    @property
    def rejects_path(self) -> Path:
        return self.root / "rejects.jsonl"

    @property
    def conflicts_path(self) -> Path:
        return self.root / "conflicts.jsonl"

    @property
    def symbols_path(self) -> Path:
        return self.root / "symbols.yaml"

    @property
    def relations_path(self) -> Path:
        return self.root / "relations.yaml"

    @property
    def operatoria_path(self) -> Path:
        return self.root / "operatoria.yaml"

    @property
    def shared_path(self) -> Path:
        return self.root / "shared.yaml"

    @property
    def manifest_path(self) -> Path:
        return self.root / "manifest.yaml"

    def ensure(self) -> "KB":
        for directory in (
            self.root,
            self.sources_dir,
            self.work_dir,
            self.candidates_dir,
            self.facts_dir,
            self.wigames_dir,
            self.proposals_dir,
            self.projections_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)
        return self

    def source_meta(self, slug: str) -> dict[str, Any]:
        return read_json(self.sources_dir / f"{slug}.json")

    def source_text(self, slug: str) -> str:
        return (self.sources_dir / f"{slug}.txt").read_text(encoding="utf-8")

    def source_slugs(self) -> list[str]:
        return sorted(p.stem for p in self.sources_dir.glob("*.json"))

    def all_candidates(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        rows: list[dict[str, Any]] = []
        bad: list[dict[str, Any]] = []
        for path in sorted(self.candidates_dir.glob("**/*.jsonl")):
            file_rows, file_bad = read_jsonl_safe(path)
            rows.extend(file_rows)
            bad.extend(file_bad)
        return rows, bad

    def facts(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for path in sorted(self.facts_dir.glob("*.jsonl")):
            rows.extend(read_jsonl(path))
        return rows

    def proposals(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for path in sorted(self.proposals_dir.glob("*.jsonl")):
            rows.extend(read_jsonl(path))
        return rows

    def wigame_paths(self) -> list[Path]:
        return sorted(self.wigames_dir.glob("*.yaml"))

    def projection_paths(self) -> list[Path]:
        return sorted(self.projections_dir.glob("*.yaml"))

    def load_relations(self) -> dict[str, dict[str, Any]]:
        path = self.relations_path if self.relations_path.exists() else DEFAULT_RELATIONS
        return (load_yaml(path) or {}).get("relations", {})

    def load_aliases(self) -> list[dict[str, str]]:
        """Loads reviewed occurrence -> referent aliases (context-scoped)."""

        if not self.aliases_path.exists():
            return []
        payload = load_yaml(self.aliases_path) or {}
        return list(payload.get("aliases", []))

    def alias_map(self) -> dict[tuple[str, str], str]:
        """Returns {(context, symbol): canonical_referent}."""

        mapping: dict[tuple[str, str], str] = {}
        for entry in self.load_aliases():
            mapping[(entry["context"], entry["symbol"])] = entry["canonical"]
        return mapping
