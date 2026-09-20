"""Candidate validation and deterministic dedupe into context-scoped proposals.

Worker output is a *proposal*, never a fact. Everything is scoped by context
(the source document), so the same proposition in two articles yields two
proposals and never silently merges.
"""

from __future__ import annotations

import re
from typing import Any

from .store import KB, dump_yaml, proposal_id, slugify, write_json, write_jsonl

REQUIRED = ("relation", "subject", "object", "truth", "sentence", "source", "chunk_id")
MIN_SENTENCE = 8


def _norm(text: str) -> str:
    return " ".join(str(text).split())


def _appears(needle: str, haystack: str) -> bool:
    needle = needle.strip()
    if not needle:
        return False
    return re.search(r"\b" + re.escape(needle) + r"\b", haystack, flags=re.IGNORECASE) is not None


def validate_candidate(
    obj: Any,
    vocab: dict[str, dict[str, Any]],
    chunk_text: str,
    min_confidence: float,
) -> tuple[dict[str, Any] | None, str | None]:
    """Validates one candidate row; returns (normalized_row, reject_reason)."""

    if not isinstance(obj, dict):
        return None, "row is not a JSON object"
    missing = [key for key in REQUIRED if key not in obj]
    if missing:
        return None, f"missing keys: {', '.join(missing)}"

    relation = str(obj["relation"]).strip()
    if relation not in vocab:
        return None, f"relation not allowed: {relation!r}"

    context = slugify(str(obj["source"]).strip())
    if not context:
        return None, "source has no usable context id"

    subject, obj_value = str(obj["subject"]).strip(), str(obj["object"]).strip()
    subject_id, object_id = slugify(subject), slugify(obj_value)
    if not subject_id or not object_id:
        return None, "subject/object has no usable symbol id"
    if len(subject_id) > 120 or len(object_id) > 120:
        return None, "subject/object symbol id too long"
    if subject_id == object_id:
        return None, "self-referential proposition"

    truth = obj["truth"]
    if isinstance(truth, str):
        truth = truth.strip().lower() == "true"
    if not isinstance(truth, bool):
        return None, f"truth is not boolean: {truth!r}"

    sentence = _norm(obj["sentence"])
    if len(sentence) < MIN_SENTENCE:
        return None, "sentence too short"
    if sentence not in _norm(chunk_text):
        return None, "sentence is not a verbatim substring of the declared chunk"
    if not _appears(subject, sentence):
        return None, f"subject {subject!r} does not appear in sentence"
    if not _appears(obj_value, sentence):
        return None, f"object {obj_value!r} does not appear in sentence"

    try:
        confidence = float(obj.get("confidence", 1.0))
    except (TypeError, ValueError):
        return None, f"confidence is not numeric: {obj.get('confidence')!r}"
    if not 0.0 <= confidence <= 1.0:
        return None, f"confidence out of range: {confidence}"
    if confidence < min_confidence:
        return None, f"confidence {confidence} below min {min_confidence}"

    return (
        {
            "context": context,
            "relation": relation,
            "subject": subject_id,
            "object": object_id,
            "subject_sign": subject,
            "object_sign": obj_value,
            "truth": "true" if truth else "false",
            "sentence": sentence,
            "source": context,
            "chunk_id": str(obj["chunk_id"]).strip(),
            "revid": obj.get("revid"),
            "confidence": confidence,
        },
        None,
    )


def ingest(kb: KB, min_confidence: float = 0.0, resolve: str = "drop") -> dict[str, Any]:
    """Validates candidate rows and writes context-scoped pending proposals."""

    kb.ensure()
    vocab = kb.load_relations()
    chunk_cache: dict[str, str] = {}
    rows, bad_lines = kb.all_candidates()

    accepted: list[dict[str, Any]] = []
    rejects: list[dict[str, Any]] = [
        {"row": None, "reason": "unparseable JSONL line", **entry} for entry in bad_lines
    ]
    for index, raw in enumerate(rows):
        source_slug = str(raw.get("source", "")).strip() if isinstance(raw, dict) else ""
        chunk_id = str(raw.get("chunk_id", "")).strip() if isinstance(raw, dict) else ""
        if chunk_id not in chunk_cache:
            chunk_cache[chunk_id] = _chunk_text(kb, source_slug, chunk_id)
        if not chunk_cache[chunk_id]:
            rejects.append({"row": index, "reason": f"unknown or empty chunk: {chunk_id!r}", "raw": raw})
            continue
        row, reason = validate_candidate(raw, vocab, chunk_cache[chunk_id], min_confidence)
        if row is None:
            rejects.append({"row": index, "reason": reason, "raw": raw})
            continue
        accepted.append(row)

    by_slot: dict[tuple[str, str, str, str], list[dict[str, Any]]] = {}
    for row in accepted:
        by_slot.setdefault((row["context"], row["relation"], row["subject"], row["object"]), []).append(row)

    conflicts: list[dict[str, Any]] = []
    proposals: list[dict[str, Any]] = []
    for (context, relation, subject, obj), group in sorted(by_slot.items()):
        truths = {row["truth"] for row in group}
        if len(truths) > 1 and resolve == "drop":
            conflicts.append(_conflict(context, relation, subject, obj, group, resolution="dropped"))
            continue
        chosen = _choose(group, resolve)
        provenance = [
            {
                "source": row["source"],
                "chunk_id": row["chunk_id"],
                "revid": row["revid"],
                "sentence": row["sentence"],
                "confidence": row["confidence"],
            }
            for row in group
        ]
        proposal = {
            "proposal_id": proposal_id(context, relation, subject, obj, chosen["truth"]),
            "context": context,
            "context_id": f"ctx:{context}",
            "wigame_id": f"wigame:{context}:{relation}",
            "relation": relation,
            "subject": subject,
            "object": obj,
            "subject_sign": chosen["subject_sign"],
            "object_sign": chosen["object_sign"],
            "truth": chosen["truth"],
            "status": "pending",
            "confidence": max(row["confidence"] for row in group),
            "sources": sorted({row["source"] for row in group}),
            "provenance": provenance,
        }
        if len(truths) > 1:
            proposal["conflict"] = True
            conflicts.append(
                _conflict(context, relation, subject, obj, group, resolution=f"resolved_{chosen['truth']}")
            )
        proposals.append(proposal)

    for path in kb.proposals_dir.glob("*.jsonl"):
        path.unlink()
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in proposals:
        grouped.setdefault(f"{row['context']}__{row['relation']}", []).append(row)
    for name, group in grouped.items():
        write_jsonl(kb.proposals_dir / f"{name}.jsonl", group)

    write_jsonl(kb.rejects_path, rejects)
    write_jsonl(kb.conflicts_path, conflicts)

    symbols: dict[str, dict[str, Any]] = {}
    for row in proposals:
        bucket = symbols.setdefault(row["context"], {})
        for sid, sign in ((row["subject"], row["subject_sign"]), (row["object"], row["object_sign"])):
            entry = bucket.setdefault(sid, {"id": sid, "signs": []})
            if sign not in entry["signs"]:
                entry["signs"].append(sign)
    dump_yaml(kb.symbols_path, {"contexts": symbols})

    by_context_relation = _group_by_context_relation(proposals)
    report = {
        "candidates": len(rows),
        "unparseable": len(bad_lines),
        "accepted": len(accepted),
        "proposals": len(proposals),
        "pending": len(proposals),
        "rejected": len(rejects),
        "conflicts": len(conflicts),
        "contexts": sorted({row["context"] for row in proposals}),
        "relations": {
            f"{context}:{relation}": len(group)
            for (context, relation), group in sorted(by_context_relation.items())
        },
    }
    write_json(kb.root / "ingest_report.json", report)
    return report


def _group_by_context_relation(proposals: list[dict[str, Any]]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in proposals:
        grouped.setdefault((row["context"], row["relation"]), []).append(row)
    return grouped


def _chunk_text(kb: KB, source: str, chunk_id: str) -> str:
    """Resolves the declared chunk file for a candidate row."""

    if not source or "/" not in chunk_id:
        return ""
    _, index = chunk_id.rsplit("/", 1)
    if not index.isdigit():
        return ""
    path = kb.work_dir / slugify(source) / f"{int(index):03d}.txt"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _choose(group: list[dict[str, Any]], resolve: str) -> dict[str, Any]:
    if resolve == "true":
        return next(row for row in group if row["truth"] == "true")
    if resolve == "false":
        return next(row for row in group if row["truth"] == "false")
    return max(group, key=lambda row: (row["confidence"], row["chunk_id"]))


def _conflict(
    context: str, relation: str, subject: str, obj: str, group: list[dict[str, Any]], resolution: str
) -> dict[str, Any]:
    return {
        "context": context,
        "wigame_id": f"wigame:{context}:{relation}",
        "relation": relation,
        "subject": subject,
        "object": obj,
        "resolution": resolution,
        "truths": sorted({row["truth"] for row in group}),
        "provenance": [
            {"source": row["source"], "chunk_id": row["chunk_id"], "sentence": row["sentence"], "truth": row["truth"]}
            for row in group
        ],
    }
