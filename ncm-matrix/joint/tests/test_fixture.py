"""SPEC §8: the fixture contract that separates success from memorisation."""
from collections import defaultdict

from joint.asi_adapter import SUPPORT_THRESHOLD
from joint.fixture import (
    ES, HELD_OUT, NAMES_NEW, class_uri, context_id, profiles, sign_uri,
)
from joint.model import Vocabulary
from joint.fixture import feature_uri
from joint.matrix_adapter import ROUTES_TO


def test_same_sign_has_different_referents_by_context(full_fixture):
    records, _ = full_fixture
    referents = defaultdict(set)
    for r in records:
        for m, sign in r.tags["signs"].items():
            referents[sign].add(r.tags["referents"][m])
    assert referents["banco"] == {"institucion_financiera", "asiento"}
    assert referents["guagua"] == {"bebe", "autobus"}
    assert len(referents["pega"]) == 3


def test_distinct_signs_converge_under_annotated_scope(full_fixture):
    records, _ = full_fixture
    seen = defaultdict(set)
    for r in records:
        for c in r.supervision.identity_constraints:
            pair = frozenset((r.tags["signs"][c.first_mention], r.tags["signs"][c.second_mention]))
            seen[pair].add((r.tags["combo"][1], c.relation, c.scope))
    assert {rel for _, rel, _ in seen[frozenset({"palta", "aguacate"})]} == {"same_referent"}
    guagua = seen[frozenset({"guagua", "autobus"})]
    assert ("es", "same_referent", "pais") in guagua and ("cl", "distinct_referent", "pais") in guagua


def test_three_crossed_dimensions_with_reserved_test_combinations(full_fixture):
    records, _ = full_fixture
    by_split = defaultdict(set)
    for r in records:
        by_split[r.split].add(r.tags["combo"])
    for combo in HELD_OUT:
        assert combo not in by_split["train"] | by_split["validation"] | by_split["test_entity"]
        assert combo in by_split["test_combination"]
    assert all(len(set(c[i] for c in by_split["train"])) == 2 for i in range(3))


def test_all_label_kinds_exist(full_fixture):
    records, _ = full_fixture
    kinds = {(a.truth, a.applicable, a.provenance["status"]) for r in records for a in r.supervision.assertions}
    truths = {k[0] for k in kinds}
    assert {"true", "false", "unknown"} <= truths
    assert any(k[1] == "false" and k[2] == "unsinnig" for k in kinds)
    assert any(k[1] == "true" and k[2] == "sinnlos" for k in kinds)
    assert any(k[1] == "unknown" for k in kinds)  # no sense label: out of the world's axes


def test_two_organizations_differ_in_inapplicable_crossings_on_identical_queries(full_fixture):
    records, worlds = full_fixture
    from joint.fixture import _cost
    by_profile = {tuple(sorted(p.items())): p for p in profiles()}
    tema = lambda v: by_profile[(("tema", v),)]
    pais = lambda v: by_profile[(("pais", v),)]
    assert (_cost(worlds, "banco", "tiene_respaldo", tema("finanzas")), _cost(worlds, "banco", "tiene_respaldo", tema("parque"))) == (1.0, 0.0)
    assert _cost(worlds, "banco", "tiene_respaldo", pais("cl")) is None
    assert (_cost(worlds, "guagua", "elector", pais("es")), _cost(worlds, "guagua", "elector", pais("cl"))) == (1.0, 0.0)
    assert _cost(worlds, "guagua", "elector", tema("parque")) is None
    # the facts themselves are the same in both organizations: one reference world per full context
    assert worlds.evaluate(context_id(("parque", "es", "formal")), sign_uri("banco"), ES, class_uri("mueble")).truth == "true"


def test_universal_feature_does_not_discriminate_while_others_do(full_fixture):
    records, _ = full_fixture
    status = defaultdict(set)
    for r in records:
        for q, a in zip(r.queries, r.supervision.assertions):
            status[q.object.rsplit("/", 1)[-1]].add(a.provenance["discriminative"])
    assert status["existe"] == {False}
    assert status["persona"] == {True}


def test_asi_has_enough_support_and_splits_are_grouped(full_fixture):
    records, _ = full_fixture
    train = [r for r in records if r.split == "train"]
    assert len(train) >= SUPPORT_THRESHOLD
    split_of = defaultdict(set)
    for r in records:
        split_of[r.source_group].add(r.split)
    assert all(len(s) == 1 for s in split_of.values())
    vocab = Vocabulary(train, [ES, ROUTES_TO], profiles(), feature_uri)
    assert not set(NAMES_NEW) & set(vocab.tokens)
