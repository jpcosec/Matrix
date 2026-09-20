"""Review gate: worker output is a proposal until a reviewer decides."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from .store import KB, dump_yaml, load_yaml, now, write_json

DECISIONS = ("approved", "rejected")


def load_decisions(kb: KB) -> dict[str, Any]:
    """Loads the review ledger."""

    if not kb.review_path.exists():
        return {"decisions": {}}
    payload = load_yaml(kb.review_path) or {}
    payload.setdefault("decisions", {})
    return payload


def save_decisions(kb: KB, payload: dict[str, Any]) -> None:
    """Persists the review ledger."""

    dump_yaml(kb.review_path, payload)


def status_of(proposal: dict[str, Any], ledger: dict[str, Any]) -> str:
    """Returns `pending`, `approved`, or `rejected` for one proposal."""

    decision = ledger["decisions"].get(proposal["proposal_id"])
    return decision["decision"] if decision else "pending"


def annotate(kb: KB, proposals: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Attaches the current review status and decision metadata to proposals."""

    ledger = load_decisions(kb)
    rows: list[dict[str, Any]] = []
    for proposal in proposals:
        decision = ledger["decisions"].get(proposal["proposal_id"], {})
        rows.append(
            {
                **proposal,
                "status": decision.get("decision", "pending"),
                "review": {
                    "reviewer": decision.get("reviewer"),
                    "note": decision.get("note", ""),
                    "reviewed_at": decision.get("reviewed_at"),
                },
            }
        )
    return rows


def _record(proposal_id_value: str, decision: str, reviewer: str, note: str) -> dict[str, Any]:
    if decision not in DECISIONS:
        raise ValueError(f"decision must be one of {DECISIONS}")
    return {
        "proposal_id": proposal_id_value,
        "decision": decision,
        "reviewer": reviewer,
        "note": note,
        "reviewed_at": now(),
    }


def decide(kb: KB, proposal_ids: Iterable[str], decision: str, reviewer: str, note: str = "") -> dict[str, Any]:
    """Approves or rejects specific proposals."""

    ledger = load_decisions(kb)
    known = {proposal["proposal_id"] for proposal in kb.proposals()}
    applied: list[str] = []
    unknown: list[str] = []
    for raw_id in proposal_ids:
        for candidate in ([raw_id] if raw_id in known else [pid for pid in known if pid.startswith(raw_id)]):
            if candidate not in known:
                unknown.append(raw_id)
                break
            ledger["decisions"][candidate] = _record(candidate, decision, reviewer, note)
            applied.append(candidate)
    save_decisions(kb, ledger)
    return {"decision": decision, "applied": applied, "unknown": unknown}


def decide_filtered(
    kb: KB,
    decision: str,
    reviewer: str,
    note: str = "",
    status: str = "pending",
    relation: str | None = None,
) -> dict[str, Any]:
    """Applies a decision to every proposal matching a filter."""

    targets = [
        proposal["proposal_id"]
        for proposal in annotate(kb, kb.proposals())
        if proposal["status"] == status and (relation is None or proposal["relation"] == relation)
    ]
    return decide(kb, targets, decision, reviewer, note=note)


def reset(kb: KB, proposal_ids: Iterable[str] | None = None) -> dict[str, Any]:
    """Clears decisions, for the given ids or the whole ledger."""

    ledger = load_decisions(kb)
    if proposal_ids is None:
        removed = len(ledger["decisions"])
        ledger["decisions"] = {}
    else:
        removed = 0
        for raw_id in proposal_ids:
            for pid in [raw_id] + [p for p in ledger["decisions"] if p.startswith(raw_id)]:
                if pid in ledger["decisions"]:
                    del ledger["decisions"][pid]
                    removed += 1
                    break
    save_decisions(kb, ledger)
    return {"reset": removed}


def apply_file(kb: KB, path: Path, reviewer: str) -> dict[str, Any]:
    """Applies decisions from a JSONL or YAML file of {proposal_id, decision, note}."""

    text = Path(path).read_text(encoding="utf-8")
    if path.suffix in {".yaml", ".yml"}:
        rows = (load_yaml(path) or {}).get("decisions", [])
    else:
        rows = [json.loads(line) for line in text.splitlines() if line.strip()]
    applied: list[str] = []
    unknown: list[str] = []
    for row in rows:
        result = decide(kb, [row["proposal_id"]], row.get("decision", "approved"), row.get("reviewer", reviewer), row.get("note", ""))
        applied.extend(result["applied"])
        unknown.extend(result["unknown"])
    return {"applied": applied, "unknown": unknown}


def summary(kb: KB) -> dict[str, Any]:
    """Counts proposals by review status and relation."""

    rows = annotate(kb, kb.proposals())
    by_status: dict[str, int] = {"pending": 0, "approved": 0, "rejected": 0}
    by_relation: dict[str, dict[str, int]] = {}
    for row in rows:
        by_status[row["status"]] = by_status.get(row["status"], 0) + 1
        bucket = by_relation.setdefault(row["relation"], {"pending": 0, "approved": 0, "rejected": 0})
        bucket[row["status"]] = bucket.get(row["status"], 0) + 1
    return {"total": len(rows), "by_status": by_status, "by_relation": by_relation}


def render_pending(kb: KB, limit: int | None = None) -> Path:
    """Writes a human-reviewable Markdown checklist of pending proposals."""

    rows = [row for row in annotate(kb, kb.proposals()) if row["status"] == "pending"]
    rows.sort(key=lambda row: (row["relation"], row["subject"], row["object"]))
    if limit:
        rows = rows[:limit]
    lines = [
        "# Pending KB proposals",
        "",
        f"Generated: {now()}",
        "",
        "Approve or reject each line. Apply decisions with:",
        "`python -m tools.kb --kb <kb> review apply <this-file-as-.yaml>`",
        "",
    ]
    current = None
    for row in rows:
        if row["relation"] != current:
            current = row["relation"]
            lines.append(f"## {current}")
            lines.append("")
        evidence = (row.get("provenance") or [{}])[0].get("sentence", "")
        lines.append(
            f"- [ ] `{row['proposal_id']}` {row['subject']} --{row['relation']}--> {row['object']}"
            f" (truth={row['truth']})"
        )
        if evidence:
            lines.append(f"  - evidence: {evidence[:200]}")
    path = kb.root / "review_pending.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_json(kb.root / "review_summary.json", summary(kb))
    return path
