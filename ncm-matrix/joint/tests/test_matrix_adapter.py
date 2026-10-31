"""SPEC §5: the oracle distinguishes label kinds, never mutates the reference, exports routes."""
import torch

from joint.fixture import ES, class_uri, context_id, sign_uri
from joint.matrix_adapter import (
    ENTRY, ReferenceWorlds, WorldSpec, export_routes, read_routes, wi_id,
)
from joint.model import collate

R = "https://x/r"


def tiny_world():
    return ReferenceWorlds([WorldSpec(
        "w", R, ["https://x/a", "https://x/b"], ["https://x/p", "https://x/q", "https://x/all"],
        facts={("https://x/a", "https://x/p"): True, ("https://x/b", "https://x/p"): False,
               ("https://x/a", "https://x/q"): True,
               ("https://x/a", "https://x/all"): True, ("https://x/b", "https://x/all"): True},
        unsinnig={("https://x/a", "https://x/q")},
        rule_schemas=[f"(if ({R} ?x https://x/p) ({R} ?x https://x/q))"],
    )])


def test_unknown_false_unsinnig_and_sinnlos_are_distinct_and_reads_are_pure():
    worlds = tiny_world()
    before = worlds.fingerprint()
    true = worlds.evaluate("w", "https://x/a", R, "https://x/p")
    false = worlds.evaluate("w", "https://x/b", R, "https://x/p")
    unknown = worlds.evaluate("w", "https://x/b", R, "https://x/q")
    masked = worlds.evaluate("w", "https://x/a", R, "https://x/q")
    universal = worlds.evaluate("w", "https://x/a", R, "https://x/all")
    outside = worlds.evaluate("w", "https://x/a", R, "https://x/zzz")
    assert (true.truth, true.applicable, true.status) == ("true", "true", "sinnvoll")
    assert (false.truth, false.applicable) == ("false", "true")
    assert (unknown.truth, unknown.applicable, unknown.truth_known) == ("unknown", "true", False)
    # a true fact and a deduction landed on this cell; the mask still wins
    assert (masked.applicable, masked.status) == ("false", "unsinnig")
    assert (universal.applicable, universal.status, universal.discriminative) == ("true", "sinnlos", False)
    assert (outside.applicable, outside.sense_known) == ("unknown", False)
    for _ in range(3):
        worlds.evaluate("w", "https://x/a", R, "https://x/q")
    assert worlds.fingerprint() == before


def test_context_route_is_registered_in_matrix():
    worlds = tiny_world()
    system = worlds.systems["w"]
    assert system.wigames["w"].context_id == "w"
    assert [r.target_id for r in system.contexts["w"].routes] == ["w"]


def test_fixture_labels_come_from_reference_without_mutating_it(full_fixture):
    records, worlds = full_fixture
    before = worlds.fingerprint()
    label = worlds.evaluate(context_id(("finanzas", "es", "formal")), sign_uri("banco"), ES, class_uri("organizacion"))
    assert label.truth == "true"
    assert worlds.fingerprint() == before


def test_executed_routes_and_exported_propositions_coincide(trainer, small):
    records, _ = small
    batch = collate(records[:6], trainer.vocab)
    with torch.no_grad():
        out = trainer.model(batch)
    paths = trainer.model.executed_paths(out)
    keyed = {f"mention{i}": p for i, p in enumerate(paths)}
    exported = read_routes(export_routes(keyed, trainer.cfg.model.n_wi))
    for key, path in keyed.items():
        hops = [ENTRY] + [wi_id(i) for i in path]
        assert exported[key] == set(zip(hops, hops[1:]))
    # the executed path is the argmax of the very transitions that propagate w
    P = out["trace"]["P"][0]
    first = torch.tensor([p[0] for p in paths])
    assert torch.equal(P[torch.arange(len(first)), first].argmax(-1), torch.tensor([p[1] for p in paths]))
