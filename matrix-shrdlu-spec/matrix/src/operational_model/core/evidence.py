"""Provenance schema stored inside `Fact.evidence`."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, TypedDict

TIERS = ("observed", "confirmed", "inferred", "statistical")
CURATION = ("proposed", "confirmed", "rejected")
DERIVABLE_TIERS = ("observed", "confirmed", "inferred")


class Prov(TypedDict):
    """A citation of one document fragment backing a fact."""

    document_id: str
    span: tuple[int, int]
    extractor: str
    confidence: float


class Evidence(TypedDict, total=False):
    """Validated evidence payload attached to every fact."""

    prov: list[Prov]
    tier: str
    curation: str
    stats: dict[str, Any]
    derived_from: list[str]
    rule: str
    history: list[dict[str, Any]]


def make_evidence(
    tier: str = "observed",
    curation: str = "confirmed",
    prov: list[Prov] | None = None,
    stats: dict[str, Any] | None = None,
    derived_from: list[str] | None = None,
    rule: str | None = None,
) -> Evidence:
    """Builds a minimal evidence payload with the given epistemic level."""

    evidence: Evidence = {"tier": tier, "curation": curation, "history": []}
    if prov is not None:
        evidence["prov"] = prov
    if stats is not None:
        evidence["stats"] = stats
    if derived_from is not None:
        evidence["derived_from"] = derived_from
    if rule is not None:
        evidence["rule"] = rule
    validate_evidence(evidence)
    return evidence


def validate_evidence(e: dict[str, Any]) -> None:
    """Raises ValueError when tier, curation or prov are malformed."""

    tier = e.get("tier")
    if tier is not None and tier not in TIERS:
        raise ValueError(f"unknown evidence tier: {tier!r}")
    curation = e.get("curation")
    if curation is not None and curation not in CURATION:
        raise ValueError(f"unknown evidence curation: {curation!r}")
    prov = e.get("prov")
    if prov is None:
        return
    if not isinstance(prov, list):
        raise ValueError("evidence.prov must be a list")
    for entry in prov:
        if not isinstance(entry, dict):
            raise ValueError("evidence.prov entries must be mappings")
        if not isinstance(entry.get("document_id"), str):
            raise ValueError("evidence.prov entries need a string document_id")
        if not isinstance(entry.get("extractor"), str):
            raise ValueError("evidence.prov entries need a string extractor")
        span = entry.get("span")
        if not isinstance(span, (list, tuple)) or len(span) != 2:
            raise ValueError("evidence.prov entries need a two-element span")
        if not all(isinstance(bound, int) for bound in span):
            raise ValueError("evidence.prov span bounds must be integers")
        confidence = entry.get("confidence")
        if not isinstance(confidence, (int, float)) or isinstance(confidence, bool):
            raise ValueError("evidence.prov entries need a numeric confidence")


def append_history(e: dict[str, Any], action: str, by: str = "system", note: str = "") -> None:
    """Appends one curation event with an ISO-8601 UTC timestamp."""

    stamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    e.setdefault("history", []).append({"at": stamp, "by": by, "action": action, "note": note})
