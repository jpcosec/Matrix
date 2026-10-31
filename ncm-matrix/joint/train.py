"""Joint trainer of SPEC §7: one optimizer over every neural part, ASI every 250 steps.

L = L_rec + L_VQ + L_truth + L_sense + L_corr + 0.2 L_logic + 0.1 L_ASI + 0.01 L_route_cost

Every term averages over its valid elements; an empty set yields zero and a
visible counter. No loss mask comes from the predicted sense.
"""
from __future__ import annotations

import argparse
import json
import random
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np
import torch
from torch.nn import functional as F

from . import asi_adapter as asi
from .fixture import EX, build_records, feature_uri, profiles
from .matrix_adapter import ROUTES_TO, falsifying_assignments
from .model import JointModel, ModelConfig, Vocabulary, collate
from .schema import Record

EPS = 1e-6


@dataclass
class TrainConfig:
    seed: int = 7
    fixture_seed: int = 0
    steps: int = 3000
    batch_groups: int = 8
    lr: float = 1e-3
    asi_every: int = 250
    asi_max_records: int = 4096
    use_asi: bool = True
    weights: dict = field(default_factory=lambda: {
        "reconstruction": 1.0, "vq": 1.0, "truth": 1.0, "sense": 1.0, "correspondence": 1.0,
        "logic": 0.2, "asi": 0.1, "route_cost": 0.01})
    device: str = "auto"
    model: ModelConfig = field(default_factory=ModelConfig)
    name: str = "joint"


def resolve_device(name: str) -> torch.device:
    if name == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(name)


_FALSIFYING: dict[str, list] = {}


def _falsifying(formula: str, atoms: list[str]) -> list[tuple[bool, ...]]:
    shape = formula
    for index, a in enumerate(atoms):
        shape = shape.replace(a, f"(p{index} x y)")
    if shape not in _FALSIFYING:
        _FALSIFYING[shape] = falsifying_assignments(shape, [f"(p{i} x y)" for i in range(len(atoms))])
    return _FALSIFYING[shape]


def targets(records: list[Record]) -> dict:
    """Supervision tensors, aligned with collate()'s query and mention order."""
    truth, truth_mask, sense, sense_mask, costs, known = [], [], [], [], [], []
    pair_a, pair_b, pair_label, rule_atoms, rule_false = [], [], [], [], []
    q_offset = m_offset = 0
    for record in records:
        labels = {a.query_id: a for a in record.supervision.assertions}
        q_index = {q.query_id: q_offset + i for i, q in enumerate(record.queries)}
        m_index = {m.mention_id: m_offset + i for i, m in enumerate(record.mentions)}
        for query, row in zip(record.queries, record.supervision.costs):
            label = labels[query.query_id]
            truth.append(float(label.truth == "true"))
            truth_mask.append(label.truth in ("true", "false") and label.applicable == "true")
            sense.append(float(label.applicable == "true"))
            sense_mask.append(label.applicable in ("true", "false"))
            costs.append([0.0 if v is None else v for v in row])
            known.append([v is not None for v in row])
        for constraint in record.supervision.identity_constraints:
            pair_a.append(m_index[constraint.first_mention])
            pair_b.append(m_index[constraint.second_mention])
            pair_label.append(float(constraint.relation == "same_referent"))
        for rule in record.supervision.rules:
            atom_ids = rule.provenance["atoms"]
            from .fixture import atom
            assignments = _falsifying(rule.formula, [atom(a) for a in atom_ids])
            mask = [0.0] * (2 ** len(atom_ids))
            for values in assignments:
                mask[sum(int(v) << i for i, v in enumerate(values))] = 1.0
            rule_atoms.append([q_index[a] for a in atom_ids])
            rule_false.append(mask)
        q_offset += len(record.queries)
        m_offset += len(record.mentions)
    as_tensor = lambda x, dtype=torch.float: torch.tensor(x, dtype=dtype)
    return {
        "truth": as_tensor(truth), "truth_mask": as_tensor(truth_mask, torch.bool),
        "sense": as_tensor(sense), "sense_mask": as_tensor(sense_mask, torch.bool),
        "costs": as_tensor(costs), "cost_known": as_tensor(known, torch.bool),
        "pair_a": as_tensor(pair_a, torch.long), "pair_b": as_tensor(pair_b, torch.long),
        "pair_label": as_tensor(pair_label),
        "rule_atoms": as_tensor(rule_atoms, torch.long).reshape(-1, 2),
        "rule_false": as_tensor(rule_false).reshape(-1, 4),
    }


def _masked_mean(values: torch.Tensor, mask: torch.Tensor):
    count = int(mask.sum())
    return (values[mask].mean() if count else values.new_zeros(())), count


def losses(out: dict, batch: dict, tg: dict, weights: dict, model, asi_pairs=None):
    logits = out["query_logits"]
    ids = batch["ids"]
    parts, counts = {}, {}
    parts["reconstruction"] = F.cross_entropy(out["reconstruction"].flatten(0, 1), ids.flatten(), ignore_index=0)
    parts["vq"] = out["vq_loss"]
    parts["truth"], counts["n_truth"] = _masked_mean(
        F.binary_cross_entropy_with_logits(logits[:, 0], tg["truth"], reduction="none"), tg["truth_mask"])
    parts["sense"], counts["n_sense"] = _masked_mean(
        F.binary_cross_entropy_with_logits(logits[:, 1], tg["sense"], reduction="none"), tg["sense_mask"])

    m = out["m"]
    similarity = (m[tg["pair_a"]] * m[tg["pair_b"]]).sum(-1).clamp(EPS, 1 - EPS)
    pair_loss = F.binary_cross_entropy(similarity, tg["pair_label"], reduction="none")
    positive, negative = tg["pair_label"] > .5, tg["pair_label"] < .5
    pos, counts["n_correspondence_pos"] = _masked_mean(pair_loss, positive)
    neg, counts["n_correspondence_neg"] = _masked_mean(pair_loss, negative)
    present = [x for x, c in ((pos, counts["n_correspondence_pos"]), (neg, counts["n_correspondence_neg"])) if c]
    parts["correspondence"] = torch.stack(present).mean() if present else logits.new_zeros(())

    if len(tg["rule_atoms"]):
        p = logits[:, 0].sigmoid()[tg["rule_atoms"]]                       # [R, 2]
        bits = torch.tensor([[0, 0], [1, 0], [0, 1], [1, 1]], device=p.device, dtype=p.dtype)
        assignment = (p[:, None] * bits + (1 - p[:, None]) * (1 - bits)).prod(-1)   # [R, 4]
        invalid = (assignment * tg["rule_false"]).sum(-1).clamp(max=1 - EPS)
        parts["logic"] = -torch.log1p(-invalid).mean()
    else:
        parts["logic"] = logits.new_zeros(())
    counts["n_logic"] = len(tg["rule_atoms"])

    profile_mass = out["profile_mass"][batch["q_subject"]]                 # [Q, C]
    known = tg["cost_known"].float()
    known_mass = (profile_mass * known).sum(-1)
    has_known = known.sum(-1) > 0
    route_cost = (profile_mass * known * tg["costs"]).sum(-1) / known_mass.clamp_min(EPS)
    parts["route_cost"], counts["n_route_cost"] = _masked_mean(route_cost, has_known)
    counts["unknown_cost_mass"] = float((1 - known_mass).mean().detach())

    ctx = out["trace"]["ctx"][-1].mean(0)
    parts["asi"], counts["n_asi_pairs"] = asi.asi_loss(model, asi_pairs, ctx)
    total = sum(weights[k] * v for k, v in parts.items())
    return total, parts, counts


class Trainer:
    def __init__(self, cfg: TrainConfig, records: list[Record] | None = None, worlds=None):
        self.cfg = cfg
        self.device = resolve_device(cfg.device)
        if records is None:
            records, worlds = build_records(cfg.fixture_seed)
        self.records, self.worlds = records, worlds
        self.train_records = [r for r in records if r.split == "train"]
        self.vocab = Vocabulary(self.train_records, [EX + "es", ROUTES_TO], profiles(), feature_uri)
        self._seed_everything(cfg.seed)
        self.model = JointModel(cfg.model, self.vocab, ROUTES_TO).to(self.device)
        self.optimizer = torch.optim.AdamW([p for p in self.model.parameters() if p.requires_grad], lr=cfg.lr)
        self.rng = random.Random(cfg.seed)
        groups: dict[str, list[Record]] = {}
        for record in self.train_records:
            groups.setdefault(record.source_group, []).append(record)
        self.groups = [groups[k] for k in sorted(groups)]
        self.reservoir = asi.reservoir(self.train_records, cfg.asi_max_records, cfg.seed)
        self.step = 0
        self.proposals: list[asi.Proposal] = []
        self.asi_pairs = None
        self.history: list[dict] = []
        self.snapshots: list[dict] = []
        self.first_paths = None

    @staticmethod
    def _seed_everything(seed: int) -> None:
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)

    def to_device(self, tensors: dict) -> dict:
        return {k: v.to(self.device) for k, v in tensors.items()}

    def sample(self) -> list[Record]:
        chosen = self.rng.sample(range(len(self.groups)), min(self.cfg.batch_groups, len(self.groups)))
        return [r for g in chosen for r in self.groups[g]]

    def train_step(self) -> dict:
        self.model.train()
        records = self.sample()
        batch = self.to_device(collate(records, self.vocab, self.cfg.model.use_context))
        tg = self.to_device(targets(records))
        out = self.model(batch)
        pairs = self.asi_pairs if self.cfg.use_asi else None
        total, parts, counts = losses(out, batch, tg, self.cfg.weights, self.model, pairs)
        self.optimizer.zero_grad(set_to_none=True)
        total.backward()
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
        self.optimizer.step()
        self.step += 1
        entry = {"step": self.step, "loss": float(total.detach()),
                 **{k: float(v.detach()) for k, v in parts.items()}, **counts}
        if self.step == 1 or self.step % 50 == 0:
            self.history.append(entry)
        if self.step % self.cfg.asi_every == 0:
            self.rebuild_asi()
        return entry

    def rebuild_asi(self) -> None:
        records = [self.train_records[i] for i in self.reservoir]
        snapshot = asi.encode_snapshot(self.model, records, self.vocab, self.device, self.cfg.model.use_context)
        self.proposals = asi.build_proposals(snapshot, self.step, self.vocab.features,
                                             self.cfg.model.n_wi, self.cfg.model.n_fields)
        pairs = asi.ranking_pairs(self.proposals, self.vocab.features)
        self.asi_pairs = torch.tensor(pairs, dtype=torch.long, device=self.device) if pairs else None
        paths = [m["path"] for u in snapshot["units"] for m in u["mentions"]]
        if self.first_paths is None:
            self.first_paths = paths
        changed = float(np.mean([a != b for a, b in zip(self.first_paths, paths)]))
        self.snapshots.append({"step": self.step, "summary": asi.summarize(self.proposals),
                               "ranking_pairs": len(pairs), "asi_supervises": bool(pairs),
                               "route_change_vs_first_snapshot": changed,
                               "wi_used": len({m["wi"] for u in snapshot["units"] for m in u["mentions"]}),
                               "fields_used": len({m["field"] for u in snapshot["units"] for m in u["mentions"]})})

    def run(self, log_every: int = 250) -> None:
        started = time.perf_counter()
        while self.step < self.cfg.steps:
            entry = self.train_step()
            if log_every and self.step % log_every == 0:
                print(f"[{self.cfg.name} seed={self.cfg.seed}] step {self.step} loss {entry['loss']:.3f} "
                      f"truth {entry['truth']:.3f} sense {entry['sense']:.3f} corr {entry['correspondence']:.3f} "
                      f"cost {entry['route_cost']:.3f} asi_pairs {entry['n_asi_pairs']} "
                      f"({time.perf_counter() - started:.0f}s)", flush=True)
        self.elapsed = time.perf_counter() - started

    # -- checkpoints ---------------------------------------------------------------
    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        cfg = asdict(self.cfg)
        torch.save({
            "model": self.model.state_dict(),  # includes the VQ EMA buffers
            "optimizer": self.optimizer.state_dict(),
            "step": self.step, "config": cfg, "vocabulary": self.vocab.state(),
            "reservoir": self.reservoir, "proposals": asi.serialize(self.proposals),
            "asi_pairs": None if self.asi_pairs is None else self.asi_pairs.cpu(),
            "history": self.history, "snapshots": self.snapshots, "first_paths": self.first_paths,
            "rng": {"python_sampler": self.rng.getstate(), "python": random.getstate(),
                    "numpy": np.random.get_state(), "torch": torch.get_rng_state(),
                    "cuda": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None},
        }, path)

    @classmethod
    def load(cls, path: Path, records=None, worlds=None, device: str | None = None) -> "Trainer":
        state = torch.load(path, weights_only=False, map_location="cpu")
        cfg_dict = dict(state["config"])
        cfg_dict["model"] = ModelConfig(**cfg_dict["model"])
        if device:
            cfg_dict["device"] = device
        trainer = cls(TrainConfig(**cfg_dict), records, worlds)
        trainer.vocab = Vocabulary.from_state(state["vocabulary"])
        trainer.model.load_state_dict(state["model"])
        trainer.optimizer.load_state_dict(state["optimizer"])
        trainer.step = state["step"]
        trainer.reservoir = state["reservoir"]
        trainer.proposals = [asi.Proposal(**p) for p in state["proposals"]]
        trainer.asi_pairs = None if state["asi_pairs"] is None else state["asi_pairs"].to(trainer.device)
        trainer.history, trainer.snapshots = state["history"], state["snapshots"]
        trainer.first_paths = state["first_paths"]
        rng = state["rng"]
        trainer.rng.setstate(rng["python_sampler"])
        random.setstate(rng["python"])
        np.random.set_state(rng["numpy"])
        torch.set_rng_state(rng["torch"])
        if rng["cuda"] is not None and torch.cuda.is_available():
            torch.cuda.set_rng_state_all(rng["cuda"])
        return trainer


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--steps", type=int, default=3000)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent.parent / "artifacts" / "joint")
    args = parser.parse_args()
    trainer = Trainer(TrainConfig(seed=args.seed, steps=args.steps, device=args.device))
    trainer.run()
    trainer.save(args.output / f"checkpoint_seed{args.seed}.pt")
    print(json.dumps(trainer.snapshots[-1] if trainer.snapshots else {}, indent=2))


if __name__ == "__main__":
    main()
