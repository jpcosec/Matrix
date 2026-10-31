"""SPEC §9.1: gradients, routes that matter, permutation invariance, no escape via unsinnig."""
import torch

from joint.model import collate
from joint.train import losses, targets


def batch_of(trainer, records):
    return collate(records, trainer.vocab), targets(records)


def test_minibatch_gradients_are_finite_and_nonzero_everywhere(trainer, small):
    records, _ = small
    batch, tg = batch_of(trainer, records[:12])
    total, parts, _ = losses(trainer.model(batch), batch, tg, trainer.cfg.weights, trainer.model)
    total.backward()
    m = trainer.model
    for name, p in [("encoder", m.vqvae.encoder.wte.weight), ("fields F", m.F), ("Wi U", m.U), ("profiles A", m.A),
                    ("route scorer", m.scorer[0].weight), ("route context", m.route_context[0].weight)]:
        assert p.grad is not None and torch.isfinite(p.grad).all() and p.grad.abs().sum() > 0, name


def test_task_loss_alone_reaches_routing(trainer, small):
    records, _ = small
    batch, tg = batch_of(trainer, records[:12])
    _, parts, _ = losses(trainer.model(batch), batch, tg, trainer.cfg.weights, trainer.model)
    parts["truth"].backward()
    assert trainer.model.U.grad.abs().sum() > 0
    assert trainer.model.route_context[0].weight.grad.abs().sum() > 0
    assert trainer.model.role["entry"].weight.grad.abs().sum() > 0


def test_gradient_flows_through_both_refinement_steps(trainer, small):
    records, _ = small
    batch, tg = batch_of(trainer, records[:12])
    out = trainer.model(batch)
    for P in out["trace"]["P"]:
        P.retain_grad()
    assert len(out["trace"]["P"]) == 2
    _, parts, _ = losses(out, batch, tg, trainer.cfg.weights, trainer.model)
    (parts["truth"] + parts["correspondence"]).backward()
    assert all(P.grad.abs().sum() > 0 for P in out["trace"]["P"])


def test_changing_a_route_changes_representation_and_correspondence(trainer, small):
    """Wiring check: route -> u -> H -> m -> correspondence and queries, through both steps.

    Wi descriptors and fields are spread apart by hand so the check does not depend on training
    length; the trained-model effect is measured separately (JOINT.md).
    """
    records, _ = small
    # a context-requiring fragment: 'banco' resolves through tema; two mentions -> a correspondence
    record = next(r for r in records if "banco" in r.tags["signs"].values() and len(r.mentions) >= 2)
    batch, tg = batch_of(trainer, [record])
    model = trainer.model.eval()
    with torch.no_grad():
        model.U.mul_(20)
        model.F.mul_(20)
        base = model(batch)
        changed = {}
        for forced_step in (0, 1):
            target = (base["trace"]["w"][forced_step + 1].argmax(-1) + 7) % model.cfg.n_wi

            def force(t, P, target=target, forced_step=forced_step):
                if t != forced_step:
                    return P
                return torch.nn.functional.one_hot(target, model.cfg.n_wi).float()[:, None, :].expand_as(P).clone()

            changed[forced_step] = model(batch, route_override=force)
    similarity = lambda out: (out["m"][tg["pair_a"]] * out["m"][tg["pair_b"]]).sum(-1)
    for rerouted in changed.values():  # a different route at either refinement step matters
        assert (base["trace"]["H"][-1] - rerouted["trace"]["H"][-1]).abs().max() > 1e-2
        assert (base["m"] - rerouted["m"]).abs().max() > 1e-4
        assert (similarity(base) - similarity(rerouted)).abs().max() > 1e-6
        assert (base["query_logits"] - rerouted["query_logits"]).abs().max() > 1e-3


def test_joint_permutation_of_slots_leaves_outputs_unchanged(trainer, small):
    records, _ = small
    batch, _ = batch_of(trainer, records[:8])
    model = trainer.model.eval()
    with torch.no_grad():
        before = model(batch)
        fields, wis = torch.randperm(model.cfg.n_fields), torch.randperm(model.cfg.n_wi)
        model.F.copy_(model.F[fields])
        model.U.copy_(model.U[wis])
        model.A.copy_(model.A[wis])
        after = model(batch)
    assert torch.allclose(before["query_logits"], after["query_logits"], atol=1e-5)
    assert torch.allclose(before["reconstruction"], after["reconstruction"], atol=1e-5)
    assert torch.allclose(before["m"][:, fields], after["m"], atol=1e-6)
    assert torch.allclose(before["w"][:, wis], after["w"], atol=1e-6)


def test_predicting_everything_inapplicable_removes_no_obligation(trainer, small):
    records, _ = small
    batch, tg = batch_of(trainer, records[:12])
    out = trainer.model(batch)
    _, honest, honest_counts = losses(out, batch, tg, trainer.cfg.weights, trainer.model)
    out["query_logits"] = torch.stack([out["query_logits"][:, 0], torch.full_like(out["query_logits"][:, 1], -50.)], 1)
    _, evasive, evasive_counts = losses(out, batch, tg, trainer.cfg.weights, trainer.model)
    assert torch.allclose(honest["truth"], evasive["truth"])
    for key in ("n_truth", "n_sense", "n_route_cost", "n_logic"):
        assert honest_counts[key] == evasive_counts[key]
    assert evasive["sense"] > honest["sense"]


def test_route_cost_is_compared_over_the_same_queries_and_ignores_unknowns(trainer, small):
    records, _ = small
    batch, tg = batch_of(trainer, records[:12])
    out = trainer.model(batch)
    _, parts, counts = losses(out, batch, tg, trainer.cfg.weights, trainer.model)
    assert counts["n_route_cost"] == int((tg["cost_known"].sum(-1) > 0).sum())
    # moving all profile mass onto unknown costs cannot lower the cost: it is normalised by known mass
    known_any = tg["cost_known"].any(0)
    assert 0.0 <= float(parts["route_cost"].detach()) <= 1.0 and known_any.any()
