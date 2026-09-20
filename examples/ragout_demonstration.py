"""Ragout de Champiñones: 5-stage culinary demonstration over the Matrix engine.

Materializes `Aplicaciones/Dominio_Culinario/Demostracion_Dominio_Culinario_Ragout.md`:
ingesta de hechos atómicos -> reducción descriptiva -> consulta de desambiguación
(D_i) -> filtro de sentido (Si) -> W* = (Vi v Di) ^ Si sin alucinación.

Run directly (`python examples/ragout_demonstration.py`) or via
`tests/test_ragout_demonstration.py`.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.operational_model import (  # noqa: E402
    Fact,
    LiSpace,
    LogicalSystem,
    Name,
    Proposition,
    Relation,
    SearchVector,
    SenseValue,
    Symbol,
    Thing,
    TruthValue,
    WiGame,
)

RELATION = "tiene_ingrediente"
BASE_TERMS = ["cebolla", "vino", "coccion_lenta"]
DISCRIMINATIVE_TERM = "champinon"
RECIPES = ["ragout_carne", "ragout_champinones"]
INGREDIENTS = ["carne", "cebolla", "vino", "coccion_lenta", "champinon"]


def _build_system() -> tuple[LogicalSystem, WiGame]:
    system = LogicalSystem()
    for symbol_id in RECIPES + INGREDIENTS:
        system.register_thing(Thing(Symbol(symbol_id), Name(symbol_id)))
    system.register_relation(Relation(RELATION, RELATION))
    wigame = WiGame(
        wigame_id="wigame:ragout",
        li=LiSpace(li_id="li:ragout", axis_a=list(RECIPES), axis_b=list(INGREDIENTS), relation_id=RELATION),
        context_id="ctx:ragout",
        metadata={"title": "Ragout"},
    )
    system.register_wigame(wigame)
    return system, wigame


def _assert(system: LogicalSystem, wigame: WiGame, subject: str, obj: str) -> None:
    proposition = Proposition(RELATION, subject, obj, wigame.wigame_id)
    system.add_fact(Fact(proposition=proposition, truth=TruthValue.TRUE, evidence={"stage": "ingesta"}))


def run_ragout_demo(verbose: bool = True) -> dict[str, Any]:
    """Runs the 5 stages and returns their results."""

    system, wigame = _build_system()

    # Stage 1 - atomic facts
    shared = ["cebolla", "vino", "coccion_lenta"]
    for ingredient in shared:
        _assert(system, wigame, "ragout_carne", ingredient)
        _assert(system, wigame, "ragout_champinones", ingredient)
    _assert(system, wigame, "ragout_carne", "carne")
    _assert(system, wigame, "ragout_champinones", "champinon")
    stage1 = {"facts": len(wigame.facts), "axis_a": len(wigame.axis_a), "axis_b": len(wigame.axis_b)}

    # Stage 2 - descriptive reduction: W_base = cebolla ^ vino ^ coccion_lenta
    stage2 = {"terms": BASE_TERMS, "hits": wigame.search(SearchVector(wigame_id=wigame.wigame_id, terms=BASE_TERMS))}

    # Stage 3 - disambiguation query: D_i = champinon
    stage3 = {
        "discriminative_term": DISCRIMINATIVE_TERM,
        "hits": wigame.search(SearchVector(wigame_id=wigame.wigame_id, terms=[DISCRIMINATIVE_TERM])),
    }

    # Stage 4 - Si filter: champinon is unsinnig inside the carne game (categorical error)
    wigame.set_sense("ragout_carne", DISCRIMINATIVE_TERM, SenseValue.UNSINNIG)
    blocked = wigame.get_status("ragout_carne", DISCRIMINATIVE_TERM)
    stage4 = {"status": blocked.status, "applicable": blocked.applicable, "reason": blocked.reason}

    # Stage 5 - W* = (Vi v Di) ^ Si : the surviving recipe must satisfy base and D_i
    base_hits = set(stage2["hits"])
    discriminative_hits = set(wigame.search(SearchVector(wigame_id=wigame.wigame_id, terms=[DISCRIMINATIVE_TERM])))
    stage5 = {"result": sorted(base_hits & discriminative_hits), "hallucination": "ragout_carne" in discriminative_hits}

    result = {"stage1_ingest": stage1, "stage2_base": stage2, "stage3_disambiguation": stage3, "stage4_sense": stage4, "stage5_result": stage5}

    if verbose:
        print("1. ingesta atómica:", stage1)
        print("2. reducción descriptiva W_base:", stage2)
        print("3. consulta de desambiguación D_i:", stage3)
        print("4. filtro Si:", stage4)
        print("5. W* = (Vi v Di) ^ Si:", stage5)
    return result


if __name__ == "__main__":
    run_ragout_demo()
