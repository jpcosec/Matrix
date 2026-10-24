"""Contract tests, not claims about pretrained language understanding."""
import torch
from torch.nn import functional as F

from dataset import build_dataset
from experiment import ContextualNCM, encode, implication_loss, metrics, vocabulary


def test_context_pairs_and_no_split_leakage(tmp_path):
    rows = build_dataset(tmp_path)
    entities = {split: {r["entity"] for r in rows if r["split"] == split}
                for split in ("train", "validation", "test")}
    assert not entities["train"] & entities["test"]
    assert not entities["train"] & entities["validation"]
    assert not entities["validation"] & entities["test"]
    pair = [r for r in rows if r["pair_id"] == "litre_000/planta"]
    assert len(pair) == 2 and pair[0]["text"] == pair[1]["text"]
    assert {r["truth"] for r in pair} == {"true", "false"}


def test_matrix_unknown_sense_and_inference(tmp_path):
    rows = build_dataset(tmp_path)
    by_key = {(r["context"], r["predicate"]): r for r in rows if r["entity"] == "litre_000"}
    assert by_key["botanica", "fotosintetico"]["truth"] == "true"  # derived, absent from RDF truth
    assert by_key["fabula", "caminante"]["truth"] == "true"
    assert by_key["botanica", "elector"]["sense"] == "unsinnig"
    assert not by_key["botanica", "elector"]["applicable"]
    assert by_key["fabula", "elector"]["applicable"]
    assert by_key["botanica", "respirable"]["sense"] == "sinnlos"
    assert by_key["botanica", "respirable"]["applicable"]
    assert by_key["botanica", "florido"]["truth"] == "∅"
    _, _, _, known, _ = encode(rows, vocabulary(rows))
    assert all(not known[i] for i, r in enumerate(rows) if r["predicate"] == "florido")


def test_logic_penalizes_true_implies_false_and_has_gradient():
    a = torch.tensor(.9, requires_grad=True)
    b = torch.tensor(.1, requires_grad=True)
    bad = implication_loss(a, b)
    good = implication_loss(torch.tensor(.9), torch.tensor(.9))
    assert bad > good
    bad.backward()
    assert a.grad > 0 and b.grad < 0


def test_matrix_kernel_detects_predicted_rule_violation(tmp_path):
    rows = build_dataset(tmp_path)
    logits = torch.full((len(rows), 2), 10.)
    for i, row in enumerate(rows):
        if row["context"] == "botanica" and row["predicate"] == "fotosintetico":
            logits[i, 0] = -10.
    assert metrics(logits, rows)["hard_rule_violation_rate"] == .5


def test_context_is_in_embedding_and_gradient_reaches_encoder(tmp_path):
    torch.manual_seed(7)
    torch.set_num_threads(2)
    rows = build_dataset(tmp_path)
    pair = [r for r in rows if r["pair_id"] == "litre_000/planta"]
    vocab = vocabulary(rows)
    ids, ctx, sense, known, truth = encode(pair, vocab)
    assert torch.equal(ids[0], ids[1])
    model = ContextualNCM(len(vocab)).eval()
    assert not torch.allclose(model.conditioned_z(ids, ctx)[0], model.conditioned_z(ids, ctx)[1])
    _, logits, _, _ = model(ids, ctx)
    # Matrix supervision alone, not reconstruction, must reach NCM.
    F.binary_cross_entropy_with_logits(logits[known, 0], truth[known]).backward()
    assert model.context_embedding.weight.grad.abs().sum() > 0
    assert model.vqvae.encoder.wte.weight.grad.abs().sum() > 0
    assert model.vqvae.vq.embeddings[0].weight.grad is None  # EMA, not optimizer
    model.use_context = False
    _, output, _, z = model(ids, ctx)
    assert torch.allclose(z[0], z[1])
    assert torch.allclose(output[0], output[1])
