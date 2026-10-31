"""Matrix oracle contract of SPEC §5 and the export of executed routes as propositions.

Two spaces never mix: the immutable *reference* worlds compiled from the fixture
and a *prediction* space where the model's routes become `(routes_to wi_i wi_j)`
facts. The adapter avoids the reproduced discrepancies (REVISION_MATRIX.md):

- truth is read cell by cell with `get_status`, never via `ViMatrix` bitmasks;
- worlds are evaluated locally, never through block assembly;
- `unsinnig` masks are applied after every fact and deduction, because
  `add_fact` writes `sinnvoll` and would otherwise overwrite them;
- predictions are never inserted into the reference with `assert`/`check`.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

from . import _paths  # noqa: F401
from src.operational_model import (
    Context, Fact, LiSpace, LogicalSystem, Name, Proposition, Relation, SenseValue,
    Symbol, Thing, TruthValue, WiGame,
)
from src.operational_model.core.evidence import make_evidence
from src.operational_model.kernel.formula_evaluation import evaluate_formula
from src.operational_model.kernel.formulas import parse_formula
from src.operational_model.kernel.rule_schema import parse_schema
from src.operational_model.system.deduction import deduce
from src.operational_model.system.wi_game_queries import get_status

ROUTES_TO = "https://example.org/matrix-ncm/joint/routes_to"
ENTRY = "wi:entry"


@dataclass
class WorldSpec:
    """One reference context: admissible terms, facts, masks and rule schemas."""
    context_id: str
    relation: str
    subjects: list[str]
    objects: list[str]
    facts: dict[tuple[str, str], bool]
    unsinnig: set[tuple[str, str]]
    rule_schemas: list[str] = field(default_factory=list)
    source: str = "controlled-fixture"


@dataclass(frozen=True)
class Label:
    truth: str            # "true" | "false" | "unknown"
    applicable: str       # "true" | "false" | "unknown"
    status: str           # Matrix status: sinnvoll | sinnlos | unsinnig
    discriminative: bool
    truth_known: bool
    sense_known: bool
    provenance: dict


class ReferenceWorlds:
    """Compiles each WorldSpec into its own LogicalSystem, with a real Context route."""

    def __init__(self, specs: list[WorldSpec]):
        self.specs = {spec.context_id: spec for spec in specs}
        self.systems = {spec.context_id: self._compile(spec) for spec in specs}

    @staticmethod
    def _compile(spec: WorldSpec) -> LogicalSystem:
        system = LogicalSystem()
        system.register_relation(Relation(spec.relation, spec.relation.rsplit("/", 1)[-1]))
        for symbol in dict.fromkeys(spec.subjects + spec.objects):
            system.register_thing(Thing(Symbol(symbol), Name(symbol)))
        world = WiGame(
            wigame_id=spec.context_id,
            li=LiSpace(li_id=f"li:{spec.context_id}", relation_id=spec.relation,
                       axis_a=list(spec.subjects), axis_b=list(spec.objects)),
            context_id=spec.context_id,
        )
        system.register_wigame(world)
        context = Context(spec.context_id)
        context.route_to_wigame(spec.context_id)
        system.register_context(context)
        for (subject, obj), value in sorted(spec.facts.items()):
            system.add_fact(Fact(
                Proposition(spec.relation, subject, obj, spec.context_id),
                TruthValue.TRUE if value else TruthValue.FALSE,
                evidence=make_evidence(prov=[{
                    "document_id": f"{spec.source}#{spec.context_id}", "span": (0, 0),
                    "extractor": spec.source, "confidence": 1.0,
                }]),
            ))
        for schema in spec.rule_schemas:
            system.rules.extend(parse_schema(schema).expand(spec.subjects))
        deduce(system, spec.context_id)
        # Masks last: add_fact/deduce write sinnvoll into the cells they touch.
        for subject, obj in sorted(spec.unsinnig):
            world.set_sense(subject, obj, SenseValue.UNSINNIG)
        for subject, obj in spec.unsinnig:
            if get_status(world, subject, obj).status != "unsinnig":
                raise AssertionError(f"mask lost for {subject} {obj} in {spec.context_id}")
        return system

    def evaluate(self, context_id: str, subject: str, relation: str, obj: str) -> Label:
        """Explicit read of one proposition; out-of-axes cells carry no sense label."""
        spec = self.specs[context_id]
        world = self.systems[context_id].wigames[context_id]
        provenance = {"source_id": f"{spec.source}#{context_id}", "span": None, "method": "matrix.get_status"}
        if relation != spec.relation:
            return Label("unknown", "unknown", "unsinnig", False, False, False,
                         {**provenance, "reason": "relation outside world"})
        result = get_status(world, subject, obj)
        if result.reason == "Out of bounds":
            return Label("unknown", "unknown", "unsinnig", False, False, False,
                         {**provenance, "reason": "out of axes"})
        truth = {"true": "true", "false": "false"}.get(result.truth, "unknown")
        return Label(truth, "true" if result.applicable else "false", result.status,
                     bool(result.discriminative), truth != "unknown", True, provenance)

    def fingerprint(self) -> str:
        """Digest of every Vi/Si cell, to prove that evaluation never mutates the reference."""
        cells = {}
        for context_id, system in self.systems.items():
            world = system.wigames[context_id]
            for subject in world.Vi.row_axis:
                for obj in world.Vi.column_axis:
                    cells[f"{context_id}|{subject}|{obj}"] = (world.Vi.get(subject, obj), world.Si.get(subject, obj))
        return hashlib.sha256(json.dumps(cells, sort_keys=True).encode()).hexdigest()


def falsifying_assignments(formula: str, atoms: list[str]) -> list[tuple[bool, ...]]:
    """Every valuation of `atoms` that falsifies `formula`, decided by Matrix's evaluator."""
    parsed = parse_formula(formula)
    rows = []
    for mask in range(2 ** len(atoms)):
        values = tuple(bool(mask >> i & 1) for i in range(len(atoms)))
        if not evaluate_formula(parsed, dict(zip(atoms, values))):
            rows.append(values)
    return rows


def formula_holds(formula: str, valuation: dict[str, bool]) -> bool:
    return evaluate_formula(parse_formula(formula), valuation)


def wi_id(index: int) -> str:
    return f"wi:{index}"


def export_routes(paths: dict[str, list[int]], n_wi: int) -> LogicalSystem:
    """Prediction space: one routing WiGame per mention with its executed edges as facts.

    `paths[key]` is the executed sequence [w0, w1, ..., wT] of Wi indices; the
    entry endpoint precedes w0. Nothing here touches the reference worlds.
    """
    endpoints = [ENTRY] + [wi_id(i) for i in range(n_wi)]
    system = LogicalSystem()
    system.register_relation(Relation(ROUTES_TO, "routes_to"))
    for endpoint in endpoints:
        system.register_thing(Thing(Symbol(endpoint), Name(endpoint)))
    for key, path in paths.items():
        game = f"route:{key}"
        system.register_wigame(WiGame(
            wigame_id=game, li=LiSpace(li_id=f"li:{game}", relation_id=ROUTES_TO,
                                       axis_a=endpoints, axis_b=endpoints),
        ))
        hops = [ENTRY] + [wi_id(i) for i in path]
        for step, (source, target) in enumerate(zip(hops, hops[1:])):
            system.add_fact(Fact(Proposition(ROUTES_TO, source, target, game), TruthValue.TRUE,
                                 evidence=make_evidence(tier="statistical", curation="proposed",
                                                        stats={"step": step})))
    return system


def read_routes(system: LogicalSystem) -> dict[str, set[tuple[str, str]]]:
    """The `(routes_to a b)` propositions that are true in each exported routing world."""
    routes = {}
    for game_id, world in system.wigames.items():
        routes[game_id.removeprefix("route:")] = {
            (a, b) for a in world.Vi.row_axis for b in world.Vi.column_axis
            if get_status(world, a, b).truth == "true"
        }
    return routes
