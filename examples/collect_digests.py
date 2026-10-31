"""Collects compact digests of KB artifacts for the examples catalog.

Raw KBs are build outputs (often in /tmp); the digest is what we commit: totals,
contexts, top cross-context links and artifact hashes. Reproducible without the
original KB directory.

Usage:
    python examples/collect_digests.py /tmp/kbmach=machine /tmp/kbsw=software
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.kb.store import KB, load_yaml, now, sha256_file, write_json  # noqa: E402

REPORTS = Path(__file__).resolve().parent / "reports"


def digest(kb: KB, name: str, top: int = 10) -> dict[str, Any]:
    manifest = load_yaml(kb.manifest_path) if kb.manifest_path.exists() else {}
    ingest = load_yaml(kb.root / "ingest_report.json") if (kb.root / "ingest_report.json").exists() else {}
    review = manifest.get("review", {})
    contexts = manifest.get("contexts", {}).get("contexts", {})
    projections = manifest.get("projections", {})
    shared = manifest.get("shared_symbols", {})

    sources: dict[str, Any] = {}
    for key in ("software_source.yaml", "machines_source.yaml", "wiki_source.yaml"):
        path = kb.root / key
        if path.exists():
            sources[key] = load_yaml(path)

    return {
        "name": name,
        "generated_at": now(),
        "kb_root": str(kb.root),
        "source": sources,
        "totals": manifest.get("totals", {}),
        "ingest": ingest,
        "review": review.get("by_status"),
        "contexts": {
            "count": len(contexts),
            "root": manifest.get("root_context"),
            "list": sorted(contexts)[:top],
        },
        "algebra": manifest.get("algebra"),
        "derived_facts": manifest.get("derived_facts"),
        "aliases_applied": manifest.get("aliases_applied"),
        "projections": {
            "count": len(projections),
            "truncated": manifest.get("projections_truncated"),
            "top": [
                {"id": pid, "shared_subjects": payload.get("shared_subjects", [])[:6]}
                for pid, payload in list(projections.items())[:top]
            ],
        },
        "shared_symbols": {
            relation: {axis: dict(list(entries.items())[:top]) for axis, entries in axes.items()}
            for relation, axes in list(shared.items())[:top]
        },
        "artifact_sha256": {
            "manifest": sha256_file(kb.manifest_path) if kb.manifest_path.exists() else None,
            "contexts": sha256_file(kb.contexts_path) if kb.contexts_path.exists() else None,
            "operatoria": sha256_file(kb.operatoria_path) if kb.operatoria_path.exists() else None,
            "shared": sha256_file(kb.shared_path) if kb.shared_path.exists() else None,
        },
    }


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    REPORTS.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for spec in argv[1:]:
        path, _, name = spec.partition("=")
        kb = KB(Path(path))
        if not kb.manifest_path.exists():
            print(f"skip {path}: no manifest")
            continue
        payload = digest(kb, name or Path(path).name)
        out = REPORTS / f"{payload['name']}.digest.json"
        write_json(out, payload)
        written.append(str(out.relative_to(ROOT)))
    print("\n".join(written))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
