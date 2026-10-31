"""ASI snapshots of SPEC §6: binary incidences, implicative intensity, proposals, L_ASI pairs.

ASI receives no gradient and produces no truth labels. Each snapshot re-encodes
a reproducible train reservoir with the current checkpoint in eval mode (so the
VQ EMA does not move) and never mixes assignments from different checkpoints.
The numeric routine is implemented here (classical Gras intensity with an exact
Poisson tail) instead of importing an external runtime; counts are int64.
"""
from __future__ import annotations

import math
import random
from collections import defaultdict
from dataclasses import asdict, dataclass

import numpy as np
import torch

from .model import collate

SUPPORT_THRESHOLD = 20
MIN_GAP = 0.1
MARGIN = 0.2
MASK_POLICY = "units with an unobserved dimension (or no query for a class) are excluded from comparisons on it"


@dataclass
class Proposal:
    kind: str           # route | projection | gate | discriminant
    source: str
    target: str
    score: float
    support: int
    counterexamples: int
    universe_size: int
    snapshot_step: int
    status: str         # proposed | eligible | rejected
    reason: str


def implicative_intensity(n: int, n_a: int, n_b: int, n_ab: int) -> float:
    """phi(a => b) = P[Poisson(n_a * n_not_b / n) > n_a_not_b]; 0 when undefined."""
    n, n_a, n_b, n_ab = (int(x) for x in (n, n_a, n_b, n_ab))
    if n <= 0 or n_a == 0 or n_b == n:
        return 0.0
    lam = n_a * (n - n_b) / n
    observed = n_a - n_ab
    log_terms = [-lam + k * math.log(lam) - math.lgamma(k + 1) for k in range(observed + 1)]
    peak = max(log_terms)
    cdf = math.exp(peak) * sum(math.exp(t - peak) for t in log_terms)
    return float(min(max(1.0 - cdf, 0.0), 1.0))


def reservoir(records: list, limit: int, seed: int) -> list[int]:
    """Algorithm R over the train records' order: reproducible for a seed."""
    rng = random.Random(seed)
    chosen = []
    for index in range(len(records)):
        if index < limit:
            chosen.append(index)
        else:
            slot = rng.randrange(index + 1)
            if slot < limit:
                chosen[slot] = index
    return sorted(chosen)


@torch.no_grad()
def encode_snapshot(model, records, vocab, device, use_context=True, batch_size=256) -> dict:
    """Current assignments of every reservoir record, discretised only for this snapshot."""
    was_training = model.training
    model.eval()  # the NCM quantizer only applies EMA while training
    usage = {k: v.clone() for k, v in model.vqvae.vq.named_buffers() if k.startswith("codebook_hit_")}
    units = []
    for start in range(0, len(records), batch_size):
        chunk = records[start:start + batch_size]
        batch = {k: v.to(device) for k, v in collate(chunk, vocab, use_context).items()}
        out = model(batch)
        wi = out["w"].argmax(-1).tolist()
        field = out["m"].argmax(-1).tolist()
        paths = model.executed_paths(out)
        cursor = 0
        for record in chunk:
            mentions = []
            labels = {a.query_id: a for a in record.supervision.assertions}
            for mention in record.mentions:
                true_classes, queried = set(), set()
                for query in record.queries:
                    if query.subject == mention.mention_id:
                        label = labels[query.query_id]
                        if label.applicable == "true" and label.truth in ("true", "false"):
                            queried.add(query.object)
                            if label.truth == "true":
                                true_classes.add(query.object)
                mentions.append({"wi": wi[cursor], "field": field[cursor], "path": paths[cursor],
                                 "anchor": record.tags["referents"][mention.mention_id],
                                 "true": true_classes, "queried": queried})
                cursor += 1
            units.append({"id": record.example_id, "features": {v for _, v in record.observed_context},
                          "dims": {d for d, _ in record.observed_context}, "mentions": mentions})
    for name, value in usage.items():  # utilisation counters are bookkeeping, not snapshot output
        getattr(model.vqvae.vq, name).copy_(value)
    model.train(was_training)
    return {"units": units}


def _dimension(feature: str) -> str:
    return feature.rsplit("/", 1)[0]


def build_proposals(snapshot: dict, step: int, feature_vocab: dict[str, int], n_wi: int,
                    n_fields: int) -> list[Proposal]:
    units = snapshot["units"]
    proposals: list[Proposal] = []

    def status(universe, n_a):
        if universe < SUPPORT_THRESHOLD:
            return "rejected", f"universe {universe} < {SUPPORT_THRESHOLD}"
        if n_a == 0:
            return "rejected", "source absent from universe"
        return "eligible", "supported"

    # View 1 - contexts: fragments x (observed features, accessed Wi).
    wi_hits = np.zeros((len(units), n_wi), dtype=np.int64)
    for i, unit in enumerate(units):
        for mention in unit["mentions"]:
            wi_hits[i, mention["wi"]] = 1
    for feature in feature_vocab:
        dim = _dimension(feature)
        universe = np.array([dim in u["dims"] for u in units])
        has = np.array([feature in u["features"] for u in units], dtype=np.int64)[universe]
        hits = wi_hits[universe]
        n, n_a = int(universe.sum()), int(has.sum())
        for j in range(n_wi):
            n_b, n_ab = int(hits[:, j].sum()), int((has * hits[:, j]).sum())
            if n_b == 0:
                continue
            state, reason = status(n, n_a)
            proposals.append(Proposal("route", f"feature:{feature}", f"wi:{j}",
                                      implicative_intensity(n, n_a, n_b, n_ab), n_ab, n_a - n_ab, n,
                                      step, state, reason))

    # View 2 - correspondences: fragments x occupied field slots.
    occupied = np.zeros((len(units), n_fields), dtype=np.int64)
    for i, unit in enumerate(units):
        for mention in unit["mentions"]:
            occupied[i, mention["field"]] = 1
    n = len(units)
    used = np.flatnonzero(occupied.sum(0))
    co = occupied.T @ occupied
    for k in used:
        for l in used:
            if k == l or co[k, l] == 0:
                continue
            n_a, n_b, n_ab = int(occupied[:, k].sum()), int(occupied[:, l].sum()), int(co[k, l])
            score = implicative_intensity(n, n_a, n_b, n_ab)
            state = "proposed" if n >= SUPPORT_THRESHOLD else "rejected"
            proposals.append(Proposal("projection", f"field:{k}", f"field:{l}", score, n_ab, n_a - n_ab, n,
                                      step, state, "reciprocal pairs are equivalence candidates only"))

    # View 3 - discrimination: subjects routed to Wi j x their observed coordinates.
    by_wi = defaultdict(list)
    for unit in units:
        for mention in unit["mentions"]:
            by_wi[mention["wi"]].append(mention)
    for j, mentions in sorted(by_wi.items()):
        classes = sorted({c for m in mentions for c in m["queried"]})
        for cls in classes:
            pool = [m for m in mentions if cls in m["queried"]]
            universe, positives = len(pool), sum(cls in m["true"] for m in pool)
            state = "proposed" if universe >= SUPPORT_THRESHOLD else "rejected"
            fraction = positives / universe
            if fraction in (0.0, 1.0):
                proposals.append(Proposal("gate", f"class:{cls}", f"wi:{j}", 1.0, positives,
                                          universe - positives, universe, step, state,
                                          "coordinate constant in this local world: does not discriminate"))
            else:
                proposals.append(Proposal("discriminant", f"class:{cls}", f"wi:{j}", 1 - abs(2 * fraction - 1),
                                          positives, universe - positives, universe, step, state,
                                          "coordinate splits the subjects of this local world"))
        by_field = defaultdict(lambda: defaultdict(int))
        for m in mentions:
            by_field[m["field"]][m["anchor"]] += 1
        for field, anchors in by_field.items():
            if len(anchors) > 1:
                total = sum(anchors.values())
                minority = total - max(anchors.values())
                proposals.append(Proposal("gate", f"field:{field}", f"wi:{j}", minority / total, minority,
                                          total - minority, total, step,
                                          "proposed" if total >= SUPPORT_THRESHOLD else "rejected",
                                          f"collision of {len(anchors)} reference anchors"))
    return proposals


def ranking_pairs(proposals: list[Proposal], feature_vocab: dict[str, int]) -> list[tuple[int, int, int]]:
    """(feature, better wi, worse wi) whenever eligible intensities from one source differ >= 0.1."""
    by_source = defaultdict(list)
    for p in proposals:
        if p.kind == "route" and p.status == "eligible":
            by_source[p.source].append(p)
    pairs = []
    for source, group in by_source.items():
        feature = feature_vocab[source.removeprefix("feature:")]
        for a in group:
            for b in group:
                if a.score - b.score >= MIN_GAP and a.universe_size == b.universe_size:
                    pairs.append((feature, int(a.target[3:]), int(b.target[3:])))
    return pairs


def asi_loss(model, pairs: torch.Tensor | None, ctx: torch.Tensor):
    """L_ASI: hinge with margin 0.2 on sigmoid route scores, normalised by comparisons."""
    if pairs is None or len(pairs) == 0:
        return ctx.new_zeros(()), 0
    better = model.feature_route_scores(pairs[:, 0], pairs[:, 1], ctx).sigmoid()
    worse = model.feature_route_scores(pairs[:, 0], pairs[:, 2], ctx).sigmoid()
    return torch.relu(MARGIN - (better - worse)).mean(), len(pairs)


def summarize(proposals: list[Proposal]) -> dict:
    counts = defaultdict(int)
    for p in proposals:
        counts[f"{p.kind}:{p.status}"] += 1
    return dict(counts)


def serialize(proposals: list[Proposal]) -> list[dict]:
    return [asdict(p) for p in proposals]
