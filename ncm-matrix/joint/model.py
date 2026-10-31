"""Joint forward of SPEC §3-§4: fields F, Wi descriptors U/A, routing as propositions, NCM VQ.

All neural state that carries meaning is permutation-equivariant in its slots:
fields, Wi and profiles are only ever read through softmax mixtures or the
shared scorer, so permuting slots (with A's rows) leaves every output unchanged.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass

import torch
from omegaconf import OmegaConf
from torch import nn
from torch.nn import functional as F

from . import _paths  # noqa: F401
from .schema import MAX_TOKENS, Record, model_inputs, token_span, tokenize
from models.vqvae import VQVAE

PAD, UNK = 0, 1


@dataclass
class ModelConfig:
    dim: int = 64
    n_fields: int = 64
    n_wi: int = 32
    refinement_steps: int = 2
    vq_levels: tuple[int, ...] = (16, 32, 64)
    codebook_size: int = 32
    enc_layers: int = 2
    heads: int = 4
    use_context: bool = True
    freeze_routing: bool = False


class Vocabulary:
    """Train-only token, feature and constant vocabularies (SPEC §8)."""

    def __init__(self, train: list[Record], relations: list[str], profiles: list[dict], feature_of):
        words = sorted({w for r in train for w, _, _ in tokenize(r.text)})
        self.tokens = {w: i for i, w in enumerate(["<pad>", "<unk>", *words])}
        self.features = {f: i for i, f in enumerate(sorted({v for r in train for _, v in r.observed_context}))}
        self.constants = {c: i for i, c in enumerate(["<unk>", *sorted({q.object for r in train for q in r.queries
                                                                         if "://" in q.object})])}
        self.relations = {rel: i for i, rel in enumerate(relations)}
        self.profiles = profiles
        self.profile_features = [[self.features[feature_of(d, v)] for d, v in p.items()] for p in profiles]

    def state(self) -> dict:
        return {k: getattr(self, k) for k in ("tokens", "features", "constants", "relations", "profiles",
                                              "profile_features")}

    @classmethod
    def from_state(cls, state: dict) -> "Vocabulary":
        vocab = cls.__new__(cls)
        vocab.__dict__.update(state)
        return vocab


def collate(records: list[Record], vocab: Vocabulary, use_context: bool = True) -> dict:
    """Model inputs only: built exclusively from `schema.model_inputs` (no supervision)."""
    ids = torch.zeros(len(records), MAX_TOKENS, dtype=torch.long)
    features = torch.zeros(len(records), max(len(vocab.features), 1))
    cover, mention_batch, q_subject, q_relation, q_object, q_batch = [], [], [], [], [], []
    for b, record in enumerate(records):
        inputs = model_inputs(record)
        tokens = tokenize(inputs.text)
        ids[b, :len(tokens)] = torch.tensor([vocab.tokens.get(w, UNK) for w, _, _ in tokens])
        if use_context:
            for _, value in inputs.observed_context:
                if value in vocab.features:
                    features[b, vocab.features[value]] = 1.0
        offset = len(mention_batch)
        for start, end in inputs.mention_spans:
            a, z = token_span(tokens, start, end)
            row = torch.zeros(MAX_TOKENS)
            row[a:z] = 1.0
            cover.append(row)
            mention_batch.append(b)
        for subject, relation, obj in inputs.query_structure:
            if not isinstance(subject, int):
                raise ValueError("this experiment's queries have mention subjects")
            q_subject.append(offset + subject)
            q_relation.append(vocab.relations[relation])
            q_object.append(vocab.constants.get(obj, 0))
            q_batch.append(b)
    return {
        "ids": ids, "features": features, "cover": torch.stack(cover),
        "mention_batch": torch.tensor(mention_batch), "q_subject": torch.tensor(q_subject),
        "q_relation": torch.tensor(q_relation), "q_object": torch.tensor(q_object),
        "q_batch": torch.tensor(q_batch),
    }


def mlp(inp: int, hidden: int, out: int) -> nn.Sequential:
    return nn.Sequential(nn.Linear(inp, hidden), nn.GELU(), nn.Linear(hidden, out))


class JointModel(nn.Module):
    def __init__(self, cfg: ModelConfig, vocab: Vocabulary, routes_to: str):
        super().__init__()
        self.cfg = cfg
        d = cfg.dim
        self.vqvae = VQVAE(
            in_vocab_size=len(vocab.tokens), context_length=MAX_TOKENS, embed_dim=d,
            vqvae_vocab_size=[cfg.codebook_size] * len(cfg.vq_levels), n_layers=cfg.heads,
            compression_factor=1, dropout=0.0, enc_layers=cfg.enc_layers, dec_layers=1,
            vector_quantizer_config=OmegaConf.create({
                "clss": "multiscale_residual_vector_quantizer", "decay": .9, "commitment_cost": .25,
                "quant_resi": {"enabled": False},
                "levels": {"use_manual_levels": True, "manual_levels": list(cfg.vq_levels)},
            }),
        )
        n_profiles = len(vocab.profiles)
        self.routes_to = vocab.relations[routes_to]
        self.feature_emb = nn.Embedding(max(len(vocab.features), 1), d)
        self.absent_context = nn.Parameter(torch.zeros(d))
        self.context_in = nn.Linear(d, d)
        self.F = nn.Parameter(torch.randn(cfg.n_fields, d) / d ** .5)
        self.U = nn.Parameter(torch.randn(cfg.n_wi, d) / d ** .5)
        self.A = nn.Parameter(torch.zeros(cfg.n_wi, n_profiles).normal_(0, .1))
        self.profile_empty = nn.Parameter(torch.zeros(d))
        self.profile_proj = nn.Linear(d, d)
        membership = torch.zeros(n_profiles, max(len(vocab.features), 1))
        for c, features in enumerate(vocab.profile_features):
            membership[c, features] = 1.0
        self.register_buffer("profile_membership", membership)
        self.relations = nn.Embedding(len(vocab.relations), d)
        self.constants = nn.Embedding(len(vocab.constants), d)
        self.entry = nn.Parameter(torch.randn(d) / d ** .5)
        self.role = nn.ModuleDict({k: nn.Linear(d, d) for k in ("field", "constant", "wi", "entry", "feature")})
        self.scorer = mlp(4 * d, 2 * d, 2)  # shared: truth and sense logits of (rel s o) under ctx
        self.route_context = mlp(3 * d, 2 * d, d)
        self.mapper = mlp(2 * d, 2 * d, d)
        self.update = mlp(3 * d, 2 * d, d)
        if cfg.freeze_routing:
            self.route_scorer = copy.deepcopy(self.scorer)
            for module in (self.route_scorer, self.route_context, self.role["wi"], self.role["entry"]):
                module.requires_grad_(False)
            for parameter in (self.U, self.A, self.entry):
                parameter.requires_grad_(False)
        else:
            self.route_scorer = None

    # -- shared pieces -------------------------------------------------------------
    def score(self, subject, relation, obj, context, route: bool = False):
        scorer = self.route_scorer if (route and self.route_scorer is not None) else self.scorer
        subject, relation, obj, context = torch.broadcast_tensors(subject, relation, obj, context)
        return scorer(torch.cat([subject, relation, obj, context], -1))

    def descriptors(self):
        """D[j] = U[j] + sum_c softmax(A[j])[c] E[c], E[c] encoding the profile's constraints."""
        counts = self.profile_membership.sum(1, keepdim=True)
        mean = (self.profile_membership @ self.feature_emb.weight) / counts.clamp_min(1)
        E = self.profile_proj(torch.where(counts > 0, mean, self.profile_empty))
        return self.U + self.A.softmax(-1) @ E, E

    def observed_context(self, features):
        present = features.sum(1, keepdim=True)
        mean = features @ self.feature_emb.weight / present.clamp_min(1)
        return torch.where(present > 0, self.context_in(mean), self.absent_context)

    def fields(self, h, u):
        logits = self.mapper(torch.cat([h, u], -1)) @ self.F.T / self.cfg.dim ** .5
        return logits.softmax(-1)

    def route_matrix(self, D, ctx):
        """P[m, i, j] = softmax_j score(routes_to, wi_i, wi_j | ctx_m); self-routes always admissible."""
        wi = self.role["wi"](D)
        rel = self.relations.weight[self.routes_to]
        logits = self.score(wi[None, :, None], rel, wi[None, None, :], ctx[:, None, None], route=True)[..., 0]
        return logits.softmax(-1), logits

    def feature_route_scores(self, feature_ids, wi_ids, ctx):
        """Truth logits of (routes_to feature wi_j): the ASI ranking bridge (SPEC §6)."""
        D, _ = self.descriptors()
        rel = self.relations.weight[self.routes_to]
        return self.score(self.role["feature"](self.feature_emb(feature_ids)), rel,
                          self.role["wi"](D[wi_ids]), ctx, route=True)[..., 0]

    # -- forward -------------------------------------------------------------------
    def forward(self, batch: dict, refinement_steps: int | None = None, route_override=None) -> dict:
        steps = self.cfg.refinement_steps if refinement_steps is None else refinement_steps
        ids, cover, mb = batch["ids"], batch["cover"], batch["mention_batch"]
        B, T = ids.shape
        member = F.one_hot(mb, B).T.float()                                     # [B, M]
        tok_cover = member[:, None, :] * cover.T[None]                          # [B, T, M]
        frag_mean = member / member.sum(1, keepdim=True).clamp_min(1)          # [B, M]

        def spans(H):
            return (cover[:, :, None] * H[mb]).sum(1) / cover.sum(1, keepdim=True)

        def to_tokens(values):
            hits = tok_cover.sum(-1, keepdim=True)
            inside = tok_cover @ values / hits.clamp_min(1)
            return torch.where(hits > 0, inside, (frag_mean @ values)[:, None])

        c_obs = self.observed_context(batch["features"])                        # [B, d]
        c_m = c_obs[mb]
        H0 = self.vqvae._encode_pre_quant(ids) + c_obs[:, None]                 # 1. H0
        D, E = self.descriptors()
        m = self.fields(spans(H0), c_m)                                        # 2. m0
        ctx = self.route_context(torch.cat([spans(H0), m @ self.F, c_m], -1))
        entry_logits = self.score(self.role["entry"](self.entry), self.relations.weight[self.routes_to],
                                  self.role["wi"](D)[None], ctx[:, None], route=True)[..., 0]
        w = entry_logits.softmax(-1)                                            # 3. w0
        trace = {"w": [w], "P": [], "route_logits": [], "m": [m], "H": [H0], "ctx": [ctx]}
        H = H0
        for t in range(steps):                                                  # 4. refinements
            ctx = self.route_context(torch.cat([spans(H), m @ self.F, c_m], -1))
            P, logits = self.route_matrix(D, ctx)
            if route_override is not None:
                P = route_override(t, P)
            w = torch.einsum("mi,mij->mj", w, P)
            u = w @ D
            H = H0 + self.update(torch.cat([H0, to_tokens(u), to_tokens(m @ self.F)], -1))
            m = self.fields(spans(H), u)
            for key, value in (("w", w), ("P", P), ("route_logits", logits), ("m", m), ("H", H), ("ctx", ctx)):
                trace[key].append(value)
        u = w @ D
        zq, vq_loss, *_ = self.vqvae.vq(H)                                      # 5. VQ (EMA in train)
        reconstruction = self.vqvae.decoder(zq)                                 # 6. reconstruct
        m_final = self.fields(spans(zq), u)
        qs = batch["q_subject"]
        query_logits = self.score(                                              # 7. queries
            self.role["field"](m_final[qs] @ self.F), self.relations(batch["q_relation"]),
            self.role["constant"](self.constants(batch["q_object"])), u[qs])
        return {"reconstruction": reconstruction, "vq_loss": vq_loss, "query_logits": query_logits,
                "m": m_final, "w": w, "u": u, "D": D, "E": E, "zq": zq, "trace": trace,
                "profile_mass": w @ self.A.softmax(-1)}

    @torch.no_grad()
    def executed_paths(self, out: dict) -> list[list[int]]:
        """Greedy executed route per mention: argmax entry, then argmax of each P_t row."""
        trace = out["trace"]
        current = trace["w"][0].argmax(-1)
        paths = [current]
        for P in trace["P"]:
            current = P[torch.arange(len(current)), current].argmax(-1)
            paths.append(current)
        return torch.stack(paths, 1).tolist()
