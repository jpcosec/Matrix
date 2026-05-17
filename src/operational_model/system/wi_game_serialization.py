"""Serialization helpers for WiGame aggregates."""

from __future__ import annotations

from typing import Any
from typing import TYPE_CHECKING

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

    return {
        "wigame_id": wigame.wigame_id,
        "ejeA": list(wigame.axis_a),
        "ejeB": list(wigame.axis_b),
        "relacion": wigame.relation_id,
        "contexto": wigame.context_id,
        "Li": _li_payload(wigame),
        "Vi": wigame.Vi.to_dict(),
        "Si": wigame.Si.to_dict(),
        "facts": [
            _serialize_fact(fact_id, fact) for fact_id, fact in wigame.facts.items()
        ],
        "metadata": dict(wigame.metadata),
    }


def from_dict(payload: dict[str, Any]) -> "WiGame":
    """Hydrates a WiGame from serialized operational data."""

    from .wigame import WiGame

    wigame = WiGame(
        wigame_id=payload["wigame_id"],
        li=_li_from_payload(payload),
        context_id=payload.get("contexto"),
        Vi=ViMatrix.from_dict(payload["Vi"]),
        Si=SiMatrix.from_dict(payload["Si"]),
        metadata=payload.get("metadata", {}),
    )
    for fact_payload in payload.get("facts", []):
        _hydrate_fact(wigame, fact_payload)
    return wigame


def to_yaml(wigame: "WiGame") -> str:
    """Serializes the WiGame to YAML."""

    return yaml.safe_dump(to_dict(wigame), sort_keys=False, allow_unicode=True)


def from_yaml(payload: str) -> "WiGame":
    """Hydrates a WiGame from YAML."""

    return from_dict(yaml.safe_load(payload))


def _li_payload(wigame: "WiGame") -> dict[str, Any]:
    """Builds the serialized Li payload."""

    return {"li_id": wigame.li.li_id, "metadata": dict(wigame.li.metadata)}


def _serialize_fact(fact_id: str, fact: Fact) -> dict[str, Any]:
    """Serializes one fact entry."""

    return {
        "fact_id": fact_id,
        "truth": fact.truth.value,
        "proposition": {
            "proposition_id": fact.proposition.proposition_id,
            "relation_id": fact.proposition.relation_id,
            "subject_symbol_id": fact.proposition.subject_symbol_id,
            "object_symbol_id": fact.proposition.object_symbol_id,
            "wigame_id": fact.proposition.wigame_id,
        },
        "evidence": dict(fact.evidence),
    }


def _li_from_payload(payload: dict[str, Any]) -> LiSpace:
    """Builds a LiSpace from serialized WiGame data."""

    return LiSpace(
        li_id=payload.get("Li", {}).get("li_id", new_id("li")),
        axis_a=payload["ejeA"],
        axis_b=payload["ejeB"],
        relation_id=payload["relacion"],
        metadata=payload.get("Li", {}).get("metadata", {}),
    )


def _hydrate_fact(wigame: "WiGame", fact_payload: dict[str, Any]) -> None:
    """Hydrates one fact and stores it in the aggregate."""

    proposition = _proposition_from_payload(fact_payload["proposition"])
    fact = Fact(
        proposition=proposition,
        truth=TruthValue(fact_payload["truth"]),
        fact_id=fact_payload["fact_id"],
        evidence=fact_payload.get("evidence", {}),
    )
    wigame.propositions[proposition.proposition_id] = proposition
    wigame.facts[fact.fact_id] = fact


def _proposition_from_payload(payload: dict[str, Any]) -> Proposition:
    """Hydrates one proposition from serialized data."""

    return Proposition(
        relation_id=payload["relation_id"],
        subject_symbol_id=payload["subject_symbol_id"],
        object_symbol_id=payload["object_symbol_id"],
        wigame_id=payload["wigame_id"],
        proposition_id=payload["proposition_id"],
    )
