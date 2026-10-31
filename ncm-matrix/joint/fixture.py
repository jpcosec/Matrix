"""Crossed contextual fixture of SPEC §8, labelled by the Matrix reference worlds.

Three observable dimensions (tema, país, registro) are crossed into eight
reference contexts; two full combinations are reserved for test before any
training. Signs resolve to referents through the context:

| Sign | Depends on | Referents |
|---|---|---|
| banco | tema | institución financiera / asiento |
| guagua | país | bebé (cl) / autobús (es) |
| micro | país | autobús (cl) / micrófono (es) |
| pega | país × registro | trabajo (cl, coloquial) / objeción (es, coloquial) / adhesivo (formal) |
| palta, aguacate | — | the same fruit: distinct signs, one referent |

Hence the same sign has different referents by context, distinct signs
converge (palta/aguacate always; guagua/autobús only in es; micro/autobús only
in cl), every label kind exists (true, false, unknown, unsinnig, sinnlos via
`existe`), and route-cost tables differ between organizations by tema and by
país on identical queries. This is a controlled fixture, not an extractor.
"""
from __future__ import annotations

import itertools
import random

from .matrix_adapter import ReferenceWorlds, WorldSpec
from .schema import (
    Assertion, IdentityConstraint, Mention, Query, Record, Rule, Supervision, validate,
)

EX = "https://example.org/matrix-ncm/joint/"
ES = EX + "es"
DIMENSIONS = {"tema": ("finanzas", "parque"), "pais": ("cl", "es"), "registro": ("formal", "coloquial")}
DIM_NAMES = tuple(DIMENSIONS)
COMBINATIONS = tuple(itertools.product(*DIMENSIONS.values()))
HELD_OUT = (("parque", "es", "coloquial"), ("finanzas", "cl", "formal"))
SEEN = tuple(c for c in COMBINATIONS if c not in HELD_OUT)

CLASSES = ("organizacion", "mueble", "alimento", "persona", "ser_vivo", "vehiculo", "objeto",
           "actividad", "sustancia", "idea", "elector", "madura", "tiene_respaldo", "existe")
OUTSIDE_CLASS = "es_caro"  # deliberately outside every world's axes: no sense label
RULES = ("(if ({es} ?x {persona}) ({es} ?x {ser_vivo}))", "(if ({es} ?x {vehiculo}) ({es} ?x {objeto}))")
EXCLUSIONS = (("mueble", "alimento"), ("persona", "vehiculo"))

# referent -> (true classes, unknown classes, unsinnig classes); every other class is false.
REFERENTS = {
    "institucion_financiera": ({"organizacion"}, set(), {"elector", "madura", "tiene_respaldo"}),
    "asiento": ({"mueble", "objeto"}, {"tiene_respaldo"}, {"elector", "madura"}),
    "fruta": ({"alimento"}, {"madura", "ser_vivo"}, {"elector", "tiene_respaldo"}),
    "bebe": ({"persona"}, {"ser_vivo"}, {"madura", "tiene_respaldo"}),
    "autobus": ({"vehiculo", "tiene_respaldo"}, {"objeto"}, {"elector", "madura"}),
    "microfono": ({"objeto"}, set(), {"elector", "madura", "tiene_respaldo"}),
    "trabajo": ({"actividad"}, set(), {"elector", "madura", "tiene_respaldo"}),
    "objecion": ({"idea"}, set(), {"elector", "madura", "tiene_respaldo"}),
    "adhesivo": ({"sustancia"}, set(), {"elector", "madura", "tiene_respaldo"}),
    "persona": ({"persona", "elector"}, {"ser_vivo"}, {"madura", "tiene_respaldo"}),
}
# Unknown ser_vivo/objeto cells of persons, babies and buses are filled by the rules via deduce().

NAMES_TRAIN = ("ana", "luis", "marta", "pedro", "sofia", "diego", "carla", "jorge", "elena", "pablo",
               "lucia", "tomas", "irene", "mateo", "nora", "raul", "olga", "ivan", "rosa", "hugo",
               "alba", "simon", "julia", "bruno")
NAMES_NEW = ("zoe", "fermin", "otilia", "baldo", "yolanda", "quique", "wanda", "xavier")


def sign_uri(sign: str) -> str:
    return f"{EX}sign/{sign}"


def class_uri(name: str) -> str:
    return f"{EX}class/{name}"


def feature_uri(dim: str, value: str | None = None) -> str:
    return f"{EX}ctx/{dim}" + (f"/{value}" if value else "")


def context_id(combo: tuple[str, str, str]) -> str:
    return "|".join(combo)


def resolve(sign: str, combo: tuple[str, str, str]) -> str:
    tema, pais, registro = combo
    if sign in NAMES_TRAIN + NAMES_NEW:
        return f"persona:{sign}"
    return {
        "banco": "institucion_financiera" if tema == "finanzas" else "asiento",
        "palta": "fruta", "aguacate": "fruta", "autobus": "autobus",
        "guagua": "bebe" if pais == "cl" else "autobus",
        "micro": "autobus" if pais == "cl" else "microfono",
        "pega": "adhesivo" if registro == "formal" else ("trabajo" if pais == "cl" else "objecion"),
    }[sign]


def _kind(referent: str) -> str:
    return "persona" if referent.startswith("persona:") else referent


SIGNS = ("banco", "palta", "aguacate", "guagua", "micro", "autobus", "pega")


def world_specs() -> list[WorldSpec]:
    subjects = [sign_uri(s) for s in SIGNS + NAMES_TRAIN + NAMES_NEW]
    objects = [class_uri(c) for c in CLASSES]
    rules = [r.format(es=ES, **{c: class_uri(c) for c in CLASSES}) for r in RULES]
    specs = []
    for combo in COMBINATIONS:
        facts, masked = {}, set()
        for sign in SIGNS + NAMES_TRAIN + NAMES_NEW:
            true, unknown, unsinnig = REFERENTS[_kind(resolve(sign, combo))]
            for cls in CLASSES:
                cell = (sign_uri(sign), class_uri(cls))
                if cls == "existe" or cls in true:
                    facts[cell] = True
                elif cls not in unknown and cls not in unsinnig:
                    facts[cell] = False
                if cls in unsinnig:
                    masked.add(cell)
        specs.append(WorldSpec(context_id(combo), ES, subjects, objects, facts, masked, rules))
    return specs


def profiles() -> list[dict[str, str]]:
    """Every partial conjunction of observable attributes (schema values; all seen in train)."""
    options = [[None, *values] for values in DIMENSIONS.values()]
    return [{d: v for d, v in zip(DIM_NAMES, choice) if v is not None}
            for choice in itertools.product(*options)]


TEMPLATES = (
    ("t_ver", "{N} vio la {guagua} cerca del {banco}"),
    ("t_fruta", "La {palta}, o {aguacate}, quedó junto al {banco}"),
    ("t_pega", "{N} dijo que la {pega} era cosa seria"),
    ("t_guagua", "La {guagua} pasó antes que el {autobus}"),
    ("t_micro", "El {micro} y el {autobus} de {N}"),
    ("t_hablar", "{N} habló de la {pega} y del {banco}"),
)
CUES = {
    "tema": {"finanzas": ("con la cuenta", "por el crédito"), "parque": ("en la plaza", "bajo el árbol")},
    "pais": {"cl": ("po",), "es": ("tío",)},
    "registro": {"formal": ("estimado",), "coloquial": ("cachai",)},
}


def _render(template: str, names: dict[str, str], cues: list[str]):
    text, mentions = "", []
    for literal, slot in _parts(template):
        text += literal
        if slot:
            surface = names.get(slot, slot)
            mentions.append((slot, len(text), len(text) + len(surface)))
            text += surface
    if cues:
        text += ", " + ", ".join(cues)
    return text + ".", mentions


def _parts(template: str):
    while "{" in template:
        before, rest = template.split("{", 1)
        slot, template = rest.split("}", 1)
        yield before, slot
    yield template, None


def build_records(seed: int = 0, groups: dict[str, int] | None = None,
                  worlds: ReferenceWorlds | None = None) -> tuple[list[Record], ReferenceWorlds]:
    """Grouped records: every context variant of a fragment shares group and split."""
    groups = groups or {"train": 500, "validation": 60, "test_entity": 60, "test_combination": 80}
    worlds = worlds or ReferenceWorlds(world_specs())
    rng = random.Random(seed)
    profile_list = profiles()
    records = []
    for split, count in groups.items():
        for g in range(count):
            templates = [t for t in TEMPLATES if "{N}" in t[1]] if split == "test_entity" else TEMPLATES
            template_id, template = templates[rng.randrange(len(templates))]
            name = rng.choice(NAMES_NEW if split == "test_entity" else NAMES_TRAIN)
            observed = {d: rng.random() < 0.75 for d in DIM_NAMES}
            cue_dims = [d for d in DIM_NAMES if rng.random() < (0.3 if observed[d] else 0.7)]
            cue_pick = {d: rng.randrange(2) for d in DIM_NAMES}
            query_plan = {}
            for slot, _, _ in _render(template, {"N": name}, [])[1]:
                chosen = rng.sample(CLASSES, 5)
                for a, b in [("persona", "ser_vivo"), ("vehiculo", "objeto"), *EXCLUSIONS]:
                    if rng.random() < 0.35:
                        chosen += [a, b]
                if rng.random() < 0.3:
                    chosen.append(OUTSIDE_CLASS)
                query_plan[slot] = list(dict.fromkeys(chosen))
            combos = COMBINATIONS if split == "test_combination" else SEEN
            group_id = f"{split}/{g:04d}"
            for combo in combos:
                values = dict(zip(DIM_NAMES, combo))
                cues = [CUES[d][values[d]][cue_pick[d] % len(CUES[d][values[d]])] for d in cue_dims]
                records.append(_record(group_id, split, template_id, template, name, combo, observed,
                                       cues, query_plan, worlds, profile_list))
    return records, worlds


def _record(group_id, split, template_id, template, name, combo, observed, cues, query_plan,
            worlds, profile_list) -> Record:
    text, spans = _render(template, {"N": name}, cues)
    ctx = context_id(combo)
    values = dict(zip(DIM_NAMES, combo))
    mentions, signs, referents = [], {}, {}
    for index, (slot, start, end) in enumerate(spans):
        mention_id = f"m{index}"
        sign = name if slot == "N" else slot
        mentions.append(Mention(mention_id, start, end))
        signs[mention_id], referents[mention_id] = sign, resolve(sign, combo)
    queries, assertions, costs, atoms = [], [], [], {}
    slot_to_mention = {slot: f"m{i}" for i, (slot, _, _) in enumerate(spans)}
    for slot, classes in query_plan.items():
        mention_id = slot_to_mention[slot]
        for cls in classes:
            query_id = f"q{len(queries)}"
            queries.append(Query(query_id, mention_id, ES, class_uri(cls)))
            label = worlds.evaluate(ctx, sign_uri(signs[mention_id]), ES, class_uri(cls))
            assertions.append(Assertion(query_id, label.truth, label.applicable, {
                **label.provenance, "status": label.status, "discriminative": label.discriminative,
                "truth_known": label.truth_known, "sense_known": label.sense_known,
            }))
            costs.append(tuple(_cost(worlds, signs[mention_id], cls, p) for p in profile_list))
            atoms[(mention_id, cls)] = (query_id, label)
    rules = []
    for mention_id in signs:
        for premise, conclusion in [("persona", "ser_vivo"), ("vehiculo", "objeto")]:
            rules += _rule(atoms, mention_id, premise, conclusion, "(if {a} {b})")
        for a, b in EXCLUSIONS:
            rules += _rule(atoms, mention_id, a, b, "(not (and {a} {b}))")
    identity = []
    for (a, sa), (b, sb) in itertools.combinations(signs.items(), 2):
        same = referents[a] == referents[b]
        scope = "pais" if {sa, sb} in ({"guagua", "autobus"}, {"micro", "autobus"}) else "global"
        identity.append(IdentityConstraint(a, b, "same_referent" if same else "distinct_referent", scope))
    return validate(Record(
        example_id=f"{group_id}@{ctx}", source_group=group_id, text=text,
        observed_context=tuple((feature_uri(d), feature_uri(d, values[d])) for d in DIM_NAMES if observed[d]),
        mentions=tuple(mentions), queries=tuple(queries),
        supervision=Supervision(ctx, tuple(assertions), tuple(identity), tuple(rules), tuple(costs)),
        split=split,
        tags={"combo": combo, "combo_seen": combo in SEEN, "template": template_id,
              "referents": referents, "signs": signs},
    ))


def atom(query_id: str) -> str:
    """Propositional atom naming a query inside rule formulas."""
    return f"({ES} {query_id} {EX}holds)"


def _rule(atoms, mention_id, a, b, shape) -> list[Rule]:
    if (mention_id, a) not in atoms or (mention_id, b) not in atoms:
        return []
    (qa, la), (qb, lb) = atoms[(mention_id, a)], atoms[(mention_id, b)]
    if la.applicable != "true" or lb.applicable != "true":
        return []  # only formulas whose scope is verified applicable in the reference
    return [Rule(shape.format(a=atom(qa), b=atom(qb)), "reference_context",
                 {"source_id": "fixture.rules", "atoms": [qa, qb]})]


_COST_CACHE: dict = {}


def _cost(worlds: ReferenceWorlds, sign: str, cls: str, profile: dict[str, str]) -> float | None:
    """1 if the crossing is inapplicable in every context the profile admits, 0 if applicable
    in all of them, None when they disagree or Matrix has no sense label."""
    key = (sign, cls, tuple(sorted(profile.items())))
    if key not in _COST_CACHE:
        statuses = set()
        for combo in COMBINATIONS:
            if all(dict(zip(DIM_NAMES, combo))[d] == v for d, v in profile.items()):
                statuses.add(worlds.evaluate(context_id(combo), sign_uri(sign), ES, class_uri(cls)).applicable)
        _COST_CACHE[key] = 1.0 if statuses == {"false"} else 0.0 if statuses == {"true"} else None
    return _COST_CACHE[key]
