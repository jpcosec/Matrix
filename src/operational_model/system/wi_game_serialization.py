"""Serialization helpers for WiGame aggregates."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import yaml

from .._ids import new_id
from ..core.fact import Fact
from ..core.li_space import LiSpace
from ..core.proposition import Proposition
from ..core.truth_value import TruthValue
from ..matrices.si_matrix import SiMatrix
from ..matrices.vi_matrix import ViMatrix

if TYPE_CHECKING:
    from .wigame import WiGame


def to_dict(wigame: "WiGame") -> dict[str, Any]:
    """Serializes the WiGame into its direct operational shape."""
    res = _base_payload(wigame)
    res["Li"] = _li_payload(wigame)
    res["Vi"] = wigame.Vi.to_dict()
    res["Si"] = wigame.Si.to_dict()
    res["facts"] = [_serialize_fact(i, f) for i, f in wigame.facts.items()]
    res["metadata"] = dict(wigame.metadata)
    return res


def from_dict(payload: dict[str, Any]) -> "WiGame":
    """Hydrates a WiGame from serialized operational data."""
    from .wigame import WiGame

    wigame = WiGame(
        wigame_id=payload["wigame_id"],
        li=_li_from_payload(payload),
        context_id=payload.get("context") or payload.get("contexto"),
        Vi=ViMatrix.from_dict(payload["Vi"]),
        Si=SiMatrix.from_dict(payload["Si"]),
        metadata=payload.get("metadata", {}),
    )
    _hydrate_facts(wigame, payload.get("facts", []))
    return wigame


def to_yaml(wigame: "WiGame") -> str:
    """Serializes the WiGame to YAML."""
    return yaml.safe_dump(to_dict(wigame), sort_keys=False, allow_unicode=True)


def from_yaml(payload: str) -> "WiGame":
    """Hydrates a WiGame from YAML."""
    return from_dict(yaml.safe_load(payload))


def _base_payload(wigame: "WiGame") -> dict[str, Any]:
    """Returns the core identification payload."""
    return {
        "wigame_id": wigame.wigame_id,
        "axis_a": list(wigame.axis_a),
        "axis_b": list(wigame.axis_b),
        "relation": wigame.relation_id,
        "context": wigame.context_id,
    }


def _li_payload(wigame: "WiGame") -> dict[str, Any]:
    """Builds the serialized Li payload."""
    return {"li_id": wigame.li.li_id, "metadata": dict(wigame.li.metadata)}


def _key(payload: dict, primary: str, fallback: str) -> Any:
    """Returns the value for the primary key or its fallback."""
    return payload.get(primary) if primary in payload else payload[fallback]


def _serialize_fact(fact_id: str, fact: Fact) -> dict[str, Any]:
    """Serializes one fact entry."""
    return {
        "fact_id": fact_id,
        "truth": fact.truth.value,
        "proposition": _serialize_prop(fact.proposition),
        "evidence": dict(fact.evidence),
    }


def _serialize_prop(prop: Proposition) -> dict[str, Any]:
    """Serializes one proposition."""
    return {
        "proposition_id": prop.proposition_id,
        "relation_id": prop.relation_id,
        "subject_symbol_id": prop.subject_symbol_id,
        "object_symbol_id": prop.object_symbol_id,
        "wigame_id": prop.wigame_id,
    }


def _li_from_payload(payload: dict[str, Any]) -> LiSpace:
    """Builds a LiSpace from serialized WiGame data."""
    li_p = payload.get("Li", {})
    return LiSpace(
        li_id=li_p.get("li_id", new_id("li")),
        axis_a=_key(payload, "axis_a", "ejeA"),
        axis_b=_key(payload, "axis_b", "ejeB"),
        relation_id=_key(payload, "relation", "relacion"),
        metadata=li_p.get("metadata", {}),
    )


def _hydrate_facts(wigame: "WiGame", facts_payload: list[dict]) -> None:
    """Hydrates a list of facts into a WiGame."""
    for fact_p in facts_payload:
        _hydrate_fact(wigame, fact_p)


def _hydrate_fact(wigame: "WiGame", fact_p: dict[str, Any]) -> None:
    """Hydrates one fact and stores it in the aggregate."""
    prop = _prop_from_payload(fact_p["proposition"])
    fact = Fact(
        proposition=prop,
        truth=TruthValue(fact_p["truth"]),
        fact_id=fact_p["fact_id"],
        evidence=fact_p.get("evidence", {}),
    )
    wigame.propositions[prop.proposition_id] = prop
    wigame.facts[fact.fact_id] = fact


def _prop_from_payload(p: dict[str, Any]) -> Proposition:
    """Hydrates one proposition from serialized data."""
    return Proposition(
        relation_id=p["relation_id"],
        subject_symbol_id=p["subject_symbol_id"],
        object_symbol_id=p["object_symbol_id"],
        wigame_id=p["wigame_id"],
        proposition_id=p["proposition_id"],
    )
