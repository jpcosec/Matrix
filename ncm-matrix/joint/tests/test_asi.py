"""SPEC §6: intensity values, reproducible reservoir, snapshots from the live checkpoint."""
import math

import pytest
import torch

from joint import asi_adapter as asi


def test_implicative_intensity_reference_values():
    # independence: n_a_not_b equals its expectation lambda = 10
    expected = 1 - sum(math.exp(-10) * 10 ** k / math.factorial(k) for k in range(11))
    assert asi.implicative_intensity(100, 20, 50, 10) == pytest.approx(expected, abs=1e-12)
    assert asi.implicative_intensity(100, 20, 50, 20) == pytest.approx(1 - math.exp(-10), abs=1e-12)
    assert asi.implicative_intensity(100, 0, 50, 0) == 0.0
    assert asi.implicative_intensity(100, 20, 100, 20) == 0.0  # b universal: no information


def test_large_counts_do_not_overflow():
    value = asi.implicative_intensity(200_000, 50_000, 120_000, 49_000)
    assert 0.0 <= value <= 1.0 and value > 0.99


def test_reservoir_is_reproducible_and_bounded():
    items = list(range(10_000))
    a, b = asi.reservoir(items, 4096, 7), asi.reservoir(items, 4096, 7)
    assert a == b and len(a) == 4096 and a != asi.reservoir(items, 4096, 8)


def test_snapshots_are_rebuilt_from_current_assignments_without_moving_ema(trainer, small):
    records, _ = small
    train = [r for r in records if r.split == "train"]
    vq_before = {k: v.clone() for k, v in trainer.model.vqvae.vq.state_dict().items()}
    first = asi.encode_snapshot(trainer.model, train, trainer.vocab, trainer.device)
    assert all(torch.equal(vq_before[k], v) for k, v in trainer.model.vqvae.vq.state_dict().items())
    with torch.no_grad():
        trainer.model.F.copy_(torch.randn_like(trainer.model.F) * 5)
        trainer.model.U.copy_(torch.randn_like(trainer.model.U) * 5)
    second = asi.encode_snapshot(trainer.model, train, trainer.vocab, trainer.device)
    fields = lambda s: [m["field"] for u in s["units"] for m in u["mentions"]]
    assert fields(first) != fields(second)
    p1 = asi.build_proposals(first, 1, trainer.vocab.features, 32, 64)
    p2 = asi.build_proposals(second, 2, trainer.vocab.features, 32, 64)
    assert {p.snapshot_step for p in p1} == {1} and {p.snapshot_step for p in p2} == {2}
    assert {(p.kind, p.source, p.target) for p in p1} != {(p.kind, p.source, p.target) for p in p2}


def test_proposals_without_support_are_rejected_and_give_no_asi_loss(trainer, small):
    records, _ = small
    few = [r for r in records if r.split == "train"][:5]
    snapshot = asi.encode_snapshot(trainer.model, few, trainer.vocab, trainer.device)
    proposals = asi.build_proposals(snapshot, 1, trainer.vocab.features, 32, 64)
    assert all(p.status == "rejected" for p in proposals if p.kind == "route")
    assert asi.ranking_pairs(proposals, trainer.vocab.features) == []
    loss, n = asi.asi_loss(trainer.model, None, torch.zeros(64))
    assert float(loss) == 0.0 and n == 0


def test_asi_ranking_has_gradient_into_the_route_scorer(trainer):
    pairs = torch.tensor([[0, 1, 2], [0, 3, 4]])
    loss, n = asi.asi_loss(trainer.model, pairs, torch.zeros(64))
    loss.backward()
    assert n == 2 and trainer.model.U.grad.abs().sum() > 0
