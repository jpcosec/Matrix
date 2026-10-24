"""CPU smoke experiment using the upstream NCM VQ-VAE, trained from scratch.

An explicit context adapter BEFORE VQ makes z = f(text, context). The probe sees
only quantized representations, never a context ID or Matrix label directly.
No claim about pretrained NCM or general natural-language reasoning is made.
"""
from __future__ import annotations

import argparse
import json
import random
import re
import resource
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import torch
from omegaconf import OmegaConf
from torch import nn
from torch.nn import functional as F

from dataset import CONTEXTS, EX, ROOT, build_dataset
from src.operational_model.kernel.formula_evaluation import evaluate_formula
from src.operational_model.kernel.formulas import parse_formula

sys.path.insert(0, str(ROOT / "ncm"))
from models.vqvae import VQVAE


def words(text):
    return re.findall(r"\w+|[^\w\s]", text.lower())


def vocabulary(rows):
    return {word: index for index, word in enumerate(
        ["<pad>", "<unk>"] + sorted({w for r in rows if r["split"] == "train" for w in words(r["text"])}))}


def encode(rows, vocab):
    tokens = [words(row["text"]) for row in rows]
    if any(len(seq) > 8 for seq in tokens):
        raise ValueError("fixture exceeds the eight-token model; no silent truncation")
    ids = torch.tensor([[vocab.get(w, 1) for w in seq] + [0] * (8-len(seq)) for seq in tokens])
    contexts = torch.tensor([CONTEXTS.index(r["context"]) for r in rows])
    sense = torch.tensor([float(r["applicable"]) for r in rows])
    known = torch.tensor([r["applicable"] and r["truth"] in ("true", "false") for r in rows])
    truth = torch.tensor([float(r["truth"] == "true") for r in rows])
    return ids, contexts, sense, known, truth


class ContextualNCM(nn.Module):
    def __init__(self, vocab_size, use_context=True):
        super().__init__()
        self.use_context = use_context
        self.vqvae = VQVAE(
            in_vocab_size=vocab_size, context_length=8, embed_dim=32,
            vqvae_vocab_size=[16, 16, 16], n_layers=4, compression_factor=1,
            dropout=0.0, enc_layers=0, dec_layers=1,
            vector_quantizer_config=OmegaConf.create({
                "clss": "multiscale_residual_vector_quantizer", "decay": .9,
                "commitment_cost": .25, "quant_resi": {"enabled": False},
                "levels": {"use_manual_levels": True, "manual_levels": [2, 4, 8]},
            }),
        )
        self.context_embedding = nn.Embedding(len(CONTEXTS), 32)
        self.adapter = nn.Sequential(nn.Linear(32, 64), nn.GELU(), nn.Linear(64, 32))
        self.readout = nn.Sequential(nn.Linear(32, 64), nn.GELU(), nn.Linear(64, 2))

    def conditioned_z(self, ids, contexts):
        # Public encode()/encode_z() are no_grad in upstream: use training path.
        z = self.vqvae._encode_pre_quant(ids)
        if self.use_context:
            z = z + self.context_embedding(contexts).unsqueeze(1)
        return z + self.adapter(z)

    def forward(self, ids, contexts):
        z = self.conditioned_z(ids, contexts)
        zq, vq_loss, *_ = self.vqvae.vq(z)  # upstream straight-through + EMA
        mask = ids.ne(0).unsqueeze(-1)
        pooled = (zq * mask).sum(1) / mask.sum(1).clamp_min(1)
        return self.vqvae.decoder(zq), self.readout(pooled), vq_loss, pooled


def implication_loss(prob_a, prob_b):
    # Exact invalid-assignment mass for two independent Bernoulli readouts.
    # It is a declared probabilistic surrogate, not differentiation of Matrix.
    return -torch.log1p(-(prob_a * (1 - prob_b)).clamp(max=1 - 1e-6)).mean()


def rule_loss(logits, rows):
    groups = defaultdict(dict)
    for index, row in enumerate(rows):
        groups[(row["context"], row["entity"])][row["predicate"]] = index
    losses = []
    probabilities = logits[:, 0].sigmoid()
    for (context, _), indices in groups.items():
        a, b = ("planta", "fotosintetico") if context == "botanica" else ("animal", "caminante")
        losses.append(implication_loss(probabilities[indices[a]], probabilities[indices[b]]))
    return torch.stack(losses).mean()


def metrics(logits, rows):
    probs = logits.sigmoid()
    truth_pred, sense_pred = probs[:, 0].ge(.5), probs[:, 1].ge(.5)
    known = torch.tensor([r["applicable"] and r["truth"] in ("true", "false") for r in rows])
    truth = torch.tensor([r["truth"] == "true" for r in rows])
    applicable = torch.tensor([r["applicable"] for r in rows])
    pair_indices = defaultdict(list)
    for i, row in enumerate(rows):
        pair_indices[row["pair_id"]].append(i)
    flipped = [ix for ix in pair_indices.values() if len(ix) == 2 and known[ix].all() and truth[ix[0]] != truth[ix[1]]]
    pairs_correct = [bool((truth_pred[ix] == truth[ix]).all()) for ix in flipped]
    groups = defaultdict(dict)
    for i, r in enumerate(rows):
        groups[(r["context"], r["entity"])][r["predicate"]] = i
    violations = []
    for (ctx, entity), ix in groups.items():
        a, b = ("planta", "fotosintetico") if ctx == "botanica" else ("animal", "caminante")
        atom_a, atom_b = f"({EX.es} {EX[entity]} {EX[a]})", f"({EX.es} {EX[entity]} {EX[b]})"
        formula = parse_formula(f"(if {atom_a} {atom_b})")
        # Evaluate thresholded predictions with the actual Matrix kernel.
        violations.append(not evaluate_formula(formula, {
            atom_a: bool(truth_pred[ix[a]]), atom_b: bool(truth_pred[ix[b]]),
        }))
    return {
        "truth_accuracy_known_applicable": float((truth_pred[known] == truth[known]).float().mean()),
        "sense_accuracy": float((sense_pred == applicable).float().mean()),
        "unsinnig_false_accept_rate": float(sense_pred[~applicable].float().mean()),
        "context_flip_both_correct": sum(pairs_correct) / len(pairs_correct),
        "hard_rule_violation_rate": sum(violations) / len(violations),
        "probabilistic_rule_loss": float(rule_loss(logits, rows)),
        "truth_scored_rows": int(known.sum()),
        "truth_unscored_rows": int((~known).sum()),
    }


@torch.no_grad()
def evaluate(model, rows, vocab):
    model.eval()
    ids, ctx, *_ = encode(rows, vocab)
    rec, logits, _, pooled = model(ids, ctx)
    report = metrics(logits, rows)
    mask = ids.ne(0)
    report["reconstruction_token_accuracy"] = float((rec.argmax(-1)[mask] == ids[mask]).float().mean())
    in_vocab = mask & ids.ne(1)
    report["reconstruction_in_vocab_token_accuracy"] = float((rec.argmax(-1)[in_vocab] == ids[in_vocab]).float().mean())
    report["input_oov_token_fraction"] = float(ids[mask].eq(1).float().mean())
    # Change ONLY context: identical ids, same entity, same text, same query.
    _, switched, _, switched_pool = model(ids, 1 - ctx)
    report["mean_embedding_l2_when_context_changes"] = float((pooled - switched_pool).norm(dim=-1).mean())
    report["mean_probability_change_when_context_changes"] = float((logits.sigmoid() - switched.sigmoid()).abs().mean())
    original_codes = model.vqvae.vq.z_to_idx(model.conditioned_z(ids, ctx))
    switched_codes = model.vqvae.vq.z_to_idx(model.conditioned_z(ids, 1-ctx))
    report["code_change_fraction_when_context_changes"] = float(original_codes.ne(switched_codes).float().mean())
    return report, logits


def train(rows, vocab, use_context, matrix_weight, steps, seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    model = ContextualNCM(len(vocab), use_context)
    optimizer = torch.optim.AdamW(model.parameters(), lr=.003)
    groups = defaultdict(list)
    for row in rows:
        if row["split"] == "train":
            groups[(row["entity"], row["context"])].append(row)
    batches = list(groups.values())
    history = []
    started = time.perf_counter()
    for step in range(steps):
        model.train()
        batch = [r for group in random.sample(batches, min(4, len(batches))) for r in group]
        ids, ctx, sense, known, truth = encode(batch, vocab)
        reconstruction, logits, vq_loss, _ = model(ids, ctx)
        rec_loss = F.cross_entropy(reconstruction.flatten(0, 1), ids.flatten(), ignore_index=0)
        ground_loss = F.binary_cross_entropy_with_logits(logits[known, 0], truth[known])
        sense_loss = F.binary_cross_entropy_with_logits(logits[:, 1], sense)
        logic_loss = rule_loss(logits, batch)
        loss = rec_loss + vq_loss + matrix_weight * (ground_loss + sense_loss + .2 * logic_loss)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.)
        optimizer.step()
        if step == 0 or step == steps - 1 or (step + 1) % 50 == 0:
            history.append({"step": step+1, "loss": float(loss.detach()), "reconstruction": float(rec_loss.detach()),
                            "vq": float(vq_loss.detach()), "grounding": float(ground_loss.detach()),
                            "sense": float(sense_loss.detach()), "logic": float(logic_loss.detach())})
    return model, {"elapsed_seconds": time.perf_counter()-started, "history": history,
                   "trainable_parameters": sum(p.numel() for p in model.parameters() if p.requires_grad),
                   "all_parameters": sum(p.numel() for p in model.parameters())}


def context_only_baseline(rows):
    """Majority labels per context: detect a task solvable by context ID alone."""
    counts = defaultdict(Counter)
    for r in rows:
        if r["split"] == "train" and r["applicable"] and r["truth"] in ("true", "false"):
            counts[r["context"]][r["truth"]] += 1
    scored = [r for r in rows if r["split"] == "test" and r["applicable"] and r["truth"] in ("true", "false")]
    return sum(counts[r["context"]].most_common(1)[0][0] == r["truth"] for r in scored) / len(scored)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=250)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts")
    args = parser.parse_args()
    if args.steps <= 0:
        parser.error("steps must be positive")
    torch.set_num_threads(2)
    rows = build_dataset(args.output / "dataset")
    vocab = vocabulary(rows)
    report = {
        "kind": "synthetic mechanism test; randomly initialized upstream NCM VQ-VAE; CPU",
        "seed": args.seed, "steps_per_run": args.steps, "torch": torch.__version__,
        "split_by": "entity, including both contexts and every predicate in the same split",
        "rows": dict(Counter(r["split"] for r in rows)),
        "context_only_truth_accuracy": context_only_baseline(rows), "runs": {},
        "ncm_commit": subprocess.check_output(["git", "-C", str(ROOT / "ncm"), "rev-parse", "HEAD"], text=True).strip(),
    }
    for name, conditioned in (("without_context", False), ("with_context", True)):
        model, stats = train(rows, vocab, conditioned, 2., args.steps, args.seed)
        for split in ("validation", "test"):
            selected = [r for r in rows if r["split"] == split]
            stats[split], logits = evaluate(model, selected, vocab)
            if split == "test":
                with (args.output / f"{name}_predictions.jsonl").open("w") as handle:
                    for row, prob in zip(selected, logits.sigmoid().tolist()):
                        handle.write(json.dumps({**row, "p_true": prob[0], "p_applicable": prob[1]}, ensure_ascii=False) + "\n")
        report["runs"][name] = stats
        if conditioned:
            torch.save({"state_dict": model.state_dict(), "vocabulary": vocab,
                        "contexts": CONTEXTS, "seed": args.seed, "steps": args.steps}, args.output / "tiny_contextual_vqvae.pt")
        print(name, json.dumps(stats["test"]), flush=True)
    report["peak_process_rss_mib_linux"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Report: {args.output / 'report.json'}")


if __name__ == "__main__":
    main()
