"""Turns a Corpus plus SIA statistics into canonical Matrix S-expressions."""

from __future__ import annotations

from collections import Counter
import json
import re
import unicodedata
from typing import Any, TYPE_CHECKING

import numpy as np

from populator import Corpus
from populator.extract import Document
from sia.cohesion import cohesion_pair
from sia.contingency import contingency
from sia.hierarchy import build_hierarchy, significant_levels
from sia.intensity import confidence, phi_classical, phi_entropic
from sia.report import rules

if TYPE_CHECKING:
    from src.operational_model import LogicalSystem


def surface_forms(corpus: Corpus, documents: list[Document]) -> dict[str, str]:
    """Returns the most frequent surface form of every concept."""

    by_id = {document.document_id: document for document in documents}
    counts: dict[str, Counter[str]] = {concept: Counter() for concept in corpus.concepts}
    for occurrence in corpus.occurrences:
        concept = corpus.concepts[occurrence.col]
        document = by_id[corpus.individuals[occurrence.row].document_id]
        start, end = occurrence.char_span
        counts[concept][document.text[start:end]] += 1
    forms: dict[str, str] = {}
    for concept in corpus.concepts:
        counters = counts[concept]
        forms[concept] = counters.most_common(1)[0][0] if counters else corpus.vocab_source.get(concept, [concept])[0]
    return forms


def corpus_to_sexprs(
    corpus: Corpus,
    wigame_id: str,
    relation_id: str = "implies",
    alpha: float = 2.0,
    phi_min: float = 0.85,
    n_min: int = 20,
    auto_confirm_phi: float = 0.99,
    extractor: str = "populator@0.1",
    documents: list[Document] | None = None,
    max_fact_candidates: int | None = None,
    max_nonsense: int | None = None,
    max_class_candidates: int | None = None,
    hierarchy_max_concepts: int | None = 120,
) -> list[str]:
    """Builds the create plus candidate S-expressions for one corpus.

    Candidates flagged ``auto_confirm`` in their evidence are the ``fact``
    candidates with ``phi_entropic >= auto_confirm_phi`` and ``n_a >= n_min``;
    use :func:`auto_confirm_candidates` after evaluating them to get the
    runtime-generated ``candidate_id`` list.
    """

    concepts = list(corpus.concepts)
    forms = surface_forms(corpus, documents) if documents else {c: c for c in concepts}
    c = contingency(corpus.X)
    entropic = phi_entropic(c, alpha)
    classical = phi_classical(c)
    conf = confidence(c)
    cohesion = cohesion_pair(entropic)

    sexprs: list[str] = [f"(create relation {relation_id} {relation_id} transitive:true)"]
    for concept in concepts:
        sexprs.append(f"(create symbol {concept} {_atom(forms[concept])})")
    axis = " ".join(concepts)
    sexprs.append(f"(create li li:{wigame_id} {relation_id} (axis-a {axis}) (axis-b {axis}))")
    sexprs.append(f"(create wigame wigame:{wigame_id} li:{wigame_id})")

    index = {concept: position for position, concept in enumerate(concepts)}
    cooccurring = _concept_rows(corpus)
    records = rules(concepts, c, alpha=alpha, threshold=phi_min)
    if max_fact_candidates is not None:
        records = records[:max_fact_candidates]
    for record in records:
        a, b = record["a"], record["b"]
        evidence: dict[str, Any] = {
            "tier": "statistical",
            "curation": "proposed",
            "stats": {
                "phi": record["phi"],
                "phi_entropic": record["phi_entropic"],
                "confidence": record["confidence"],
                "n": c.n,
                "n_a": record["n_a"],
                "n_b": record["n_b"],
                "n_anb": record["n_anb"],
                "cohesion": record["cohesion"],
            },
            "prov": _provenance(
                corpus,
                cooccurring,
                index[a],
                index[b],
                extractor,
                record["phi_entropic"],
            ),
        }
        if record["phi_entropic"] >= auto_confirm_phi and record["n_a"] >= n_min:
            evidence["auto_confirm"] = True
        sexprs.append(
            f"(candidate fact wigame:{wigame_id} ({relation_id} {a} {b}) evidence:{_compact(evidence)})"
        )

    class_entries = _class_entries(corpus, concepts, cohesion, c, alpha, hierarchy_max_concepts)
    if max_class_candidates is not None:
        class_entries = class_entries[:max_class_candidates]
    if max_class_candidates is not None:
        class_entries = class_entries[:max_class_candidates]
    for cohesion_value, class_id, names in class_entries:
        evidence = {
            "tier": "statistical",
            "curation": "proposed",
            "stats": {"cohesion": cohesion_value},
        }
        sexprs.append(
            f"(candidate class wigame:{wigame_id} ({class_id} {' '.join(names)}) evidence:{_compact(evidence)})"
        )

    nonsense_pairs: list[tuple[float, int, int]] = []
    for a in range(len(concepts)):
        for b in range(len(concepts)):
            if a == b or c.n_a[a] < n_min or c.n_a[b] < n_min or c.n_ab[a, b] != 0:
                continue
            nonsense_pairs.append((float(c.n_a[a] * c.n_a[b]), a, b))
    nonsense_pairs.sort(key=lambda entry: (-entry[0], entry[1], entry[2]))
    if max_nonsense is not None:
        nonsense_pairs = nonsense_pairs[:max_nonsense]
    for _, a, b in nonsense_pairs:
        evidence = {
            "tier": "statistical",
            "curation": "proposed",
            "stats": {"n": c.n, "n_a": int(c.n_a[a]), "n_b": int(c.n_a[b]), "n_anb": 0},
        }
        sexprs.append(
            f"(candidate nonsense wigame:{wigame_id} ({relation_id} {concepts[a]} {concepts[b]}) "
            f"evidence:{_compact(evidence)})"
        )
    return sexprs


def auto_confirm_candidates(system: "LogicalSystem") -> list[str]:
    """Returns the candidate ids flagged for automatic confirmation."""

    return [
        candidate_id
        for candidate_id, candidate in system.candidates.items()
        if candidate.evidence.get("auto_confirm")
    ]


def _concept_rows(corpus: Corpus) -> Any:
    return corpus.X.tocsc()


def _provenance(
    corpus: Corpus,
    columns: Any,
    a: int,
    b: int,
    extractor: str,
    intensity: float,
    limit: int = 3,
) -> list[dict[str, Any]]:
    rows_a = set(columns.indices[columns.indptr[a] : columns.indptr[a + 1]].tolist())
    rows_b = set(columns.indices[columns.indptr[b] : columns.indptr[b + 1]].tolist())
    provenance: list[dict[str, Any]] = []
    for row in sorted(rows_a & rows_b)[:limit]:
        individual = corpus.individuals[row]
        provenance.append(
            {
                "document_id": individual.document_id,
                "span": [individual.char_span[0], individual.char_span[1]],
                "extractor": extractor,
                "confidence": round(float(intensity), 6),
            }
        )
    return provenance


def _class_entries(
    corpus: Corpus,
    concepts: list[str],
    cohesion: Any,
    counts: Any,
    alpha: float,
    hierarchy_max_concepts: int | None,
) -> list[tuple[float, str, list[str]]]:
    """Computes significant class candidates, subsampling the hierarchy if needed."""

    if hierarchy_max_concepts is not None and len(concepts) > hierarchy_max_concepts:
        columns = list(np.argsort(-counts.n_a)[:hierarchy_max_concepts])
        sub_corpus = corpus.X[:, columns]
        sub_concepts = [concepts[position] for position in columns]
        sub_counts = contingency(sub_corpus)
        sub_cohesion = cohesion_pair(phi_entropic(sub_counts, alpha))
        levels = build_hierarchy(sub_cohesion)
        significant = significant_levels(levels, sub_cohesion)
    else:
        sub_concepts = concepts
        levels = build_hierarchy(cohesion)
        significant = significant_levels(levels, cohesion)
    entries: list[tuple[float, str, list[str]]] = []
    for index in significant:
        if len(levels[index].cls) < 2:
            continue
        names = [sub_concepts[position] for position in levels[index].cls]
        entries.append((float(levels[index].cohesion), "_".join(names), names))
    return entries


def _compact(payload: dict[str, Any]) -> str:
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False)


def _atom(surface: str) -> str:
    """Collapses a surface form into one safe accent-folded s-expression atom."""

    collapsed = "_".join(surface.split())
    folded = "".join(
        char for char in unicodedata.normalize("NFKD", collapsed) if not unicodedata.combining(char)
    )
    return _ATOM_RE.sub("_", folded).strip("_") or "concept"


_ATOM_RE = re.compile(r"[^0-9A-Za-z_-]+")
