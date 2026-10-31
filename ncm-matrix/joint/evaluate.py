"""Metrics and ablations of SPEC §9.2: five variants x seeds 7, 19, 41, one step budget.

Seen and unseen context combinations, and new entities, are reported separately.
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import statistics
import time
from dataclasses import replace
from pathlib import Path

import torch

from .fixture import atom, build_records
from .matrix_adapter import formula_holds
from .model import UNK, collate
from .train import Trainer, TrainConfig, losses, targets

SEEDS = (7, 19, 41)
VARIANTS = ("full", "no_asi", "frozen_routing", "no_context", "no_logic")
SPLITS = ("validation", "test_entity", "test_combination_seen", "test_combination_unseen")


def variant_config(name: str, seed: int, steps: int, device: str) -> TrainConfig:
    cfg = TrainConfig(seed=seed, steps=steps, device=device, name=name)
    if name == "no_asi":
        cfg.use_asi = False
    elif name == "frozen_routing":
        cfg.model = replace(cfg.model, freeze_routing=True)
    elif name == "no_context":
        cfg.model = replace(cfg.model, use_context=False)
    elif name == "no_logic":
        cfg.weights = {**cfg.weights, "logic": 0.0}
    elif name != "full":
        raise ValueError(name)
    return cfg


def split_records(records, split: str):
    if split.startswith("test_combination"):
        seen = split.endswith("_seen")
        return [r for r in records if r.split == "test_combination" and r.tags["combo_seen"] == seen]
    return [r for r in records if r.split == split]


@torch.no_grad()
def evaluate_split(trainer: Trainer, records, batch_size: int = 256) -> dict:
    model = trainer.model
    model.eval()
    sums: dict[str, float] = {}
    counts: dict[str, int] = {}
    fields_used, wi_used = set(), set()
    field_entropy = []

    def add(key, value, n=1):
        sums[key] = sums.get(key, 0.0) + float(value)
        counts[key] = counts.get(key, 0) + n

    for start in range(0, len(records), batch_size):
        chunk = records[start:start + batch_size]
        batch = trainer.to_device(collate(chunk, trainer.vocab, trainer.cfg.model.use_context))
        tg = trainer.to_device(targets(chunk))
        out = model(batch)
        probs = out["query_logits"].sigmoid()
        truth_pred, sense_pred = probs[:, 0] > .5, probs[:, 1] > .5
        tm, sm = tg["truth_mask"], tg["sense_mask"]
        add("truth_accuracy", (truth_pred[tm] == (tg["truth"][tm] > .5)).sum(), int(tm.sum()))
        add("sense_accuracy", (sense_pred[sm] == (tg["sense"][sm] > .5)).sum(), int(sm.sum()))
        applicable = sm & (tg["sense"] > .5)
        inapplicable = sm & (tg["sense"] < .5)
        add("coverage", sense_pred[applicable].sum(), int(applicable.sum()))
        add("unsinnig_false_accept", sense_pred[inapplicable].sum(), int(inapplicable.sum()))

        m = out["m"]
        sim = (m[tg["pair_a"]] * m[tg["pair_b"]]).sum(-1)
        same = tg["pair_label"] > .5
        add("correspondence_accuracy", ((sim > .5) == same).sum(), len(sim))
        add("correspondence_same_accuracy", (sim[same] > .5).sum(), int(same.sum()))
        add("correspondence_distinct_accuracy", (sim[~same] <= .5).sum(), int((~same).sum()))
        add("distinct_pair_mean_similarity", sim[~same].sum(), int((~same).sum()))
        field_entropy += (-(m.clamp_min(1e-9).log() * m).sum(-1)).tolist()
        fields_used |= set(m.argmax(-1).tolist())
        wi_used |= set(out["w"].argmax(-1).tolist())

        offset = 0
        for record in chunk:
            index = {q.query_id: offset + i for i, q in enumerate(record.queries)}
            for rule in record.supervision.rules:
                atoms = rule.provenance["atoms"]
                valuation = {atom(a): bool(truth_pred[index[a]]) for a in atoms}
                add("logic_violation_rate", not formula_holds(rule.formula, valuation))
            offset += len(record.queries)

        ids = batch["ids"]
        prediction = out["reconstruction"].argmax(-1)
        real = ids.ne(0)
        add("reconstruction_accuracy", (prediction[real] == ids[real]).sum(), int(real.sum()))
        in_vocab = real & ids.ne(UNK)
        add("reconstruction_in_vocab_accuracy", (prediction[in_vocab] == ids[in_vocab]).sum(), int(in_vocab.sum()))

        mass = out["profile_mass"][batch["q_subject"]]
        known = tg["cost_known"].float()
        known_mass = (mass * known).sum(-1)
        rows = known.sum(-1) > 0
        cost = (mass * known * tg["costs"]).sum(-1) / known_mass.clamp_min(1e-6)
        add("route_cost", cost[rows].sum(), int(rows.sum()))
        add("unknown_cost_mass", (1 - known_mass).sum(), len(known_mass))
    report = {k: sums[k] / counts[k] if counts[k] else None for k in sums}
    report.update({"rows": len(records), "fields_used": len(fields_used), "wi_used": len(wi_used),
                   "mean_field_entropy": sum(field_entropy) / max(len(field_entropy), 1),
                   "scored_truth": counts.get("truth_accuracy", 0)})
    model.train()
    return report


def run_one(variant: str, seed: int, steps: int, device: str, records, worlds, output: Path) -> dict:
    trainer = Trainer(variant_config(variant, seed, steps, device), records, worlds)
    trainer.run(log_every=500)
    trainer.save(output / "checkpoints" / f"{variant}_seed{seed}.pt")
    result = {"variant": variant, "seed": seed, "steps": steps, "elapsed_seconds": trainer.elapsed,
              "splits": {s: evaluate_split(trainer, split_records(records, s)) for s in SPLITS},
              "asi_snapshots": trainer.snapshots, "history": trainer.history,
              "parameters": sum(p.numel() for p in trainer.model.parameters()),
              "trainable_parameters": sum(p.numel() for p in trainer.model.parameters() if p.requires_grad)}
    (output / "runs").mkdir(parents=True, exist_ok=True)
    (output / "runs" / f"{variant}_seed{seed}.json").write_text(json.dumps(result, indent=2))
    return result


def aggregate(results: list[dict]) -> dict:
    table = {}
    for variant in VARIANTS:
        runs = [r for r in results if r["variant"] == variant]
        if not runs:
            continue
        table[variant] = {}
        for split in SPLITS:
            metrics = runs[0]["splits"][split].keys()
            table[variant][split] = {}
            for metric in metrics:
                values = [r["splits"][split][metric] for r in runs if r["splits"][split][metric] is not None]
                if values:
                    table[variant][split][metric] = {
                        "mean": statistics.fmean(values),
                        "std": statistics.stdev(values) if len(values) > 1 else 0.0, "values": values}
    return table


KEY_METRICS = ("truth_accuracy", "sense_accuracy", "coverage", "unsinnig_false_accept", "correspondence_accuracy",
               "correspondence_same_accuracy", "logic_violation_rate", "reconstruction_in_vocab_accuracy",
               "route_cost", "unknown_cost_mass", "fields_used", "wi_used")


def markdown(table: dict, meta: dict) -> str:
    lines = [f"# Joint Matrix-NCM: ablations ({meta['steps']} steps, seeds {', '.join(map(str, meta['seeds']))})", "",
             f"Device: {meta['device']}. Mean ± sample std over seeds. Generated by `joint/evaluate.py`.", ""]
    for split in SPLITS:
        lines += [f"## {split}", "", "| metric | " + " | ".join(table) + " |",
                  "|---|" + "---:|" * len(table)]
        for metric in KEY_METRICS:
            cells = []
            for variant in table:
                value = table[variant][split].get(metric)
                cells.append("—" if value is None else f"{value['mean']:.3f} ± {value['std']:.3f}")
            lines.append(f"| {metric} | " + " | ".join(cells) + " |")
        lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--steps", type=int, default=3000)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--seeds", type=int, nargs="+", default=list(SEEDS))
    parser.add_argument("--variants", nargs="+", default=list(VARIANTS))
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent.parent / "artifacts" / "joint")
    args = parser.parse_args()
    records, worlds = build_records()
    started = time.perf_counter()
    results = [run_one(v, s, args.steps, args.device, records, worlds, args.output)
               for s in args.seeds for v in args.variants]
    table = aggregate(results)
    device = str(torch.cuda.get_device_name(0)) if torch.cuda.is_available() and args.device != "cpu" else "cpu"
    meta = {"steps": args.steps, "seeds": args.seeds, "variants": args.variants, "device": device,
            "torch": torch.__version__, "wall_seconds": time.perf_counter() - started,
            "rows": {s: len(split_records(records, s)) for s in SPLITS}}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "report.json").write_text(json.dumps({"meta": meta, "table": table}, indent=2))
    (args.output / "REPORT.md").write_text(markdown(table, meta))
    print(markdown(table, meta))


if __name__ == "__main__":
    main()
