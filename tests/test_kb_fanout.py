"""Contract tests: proposals are context-scoped and reviewed before compiling."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.kb.compile import compile_kb
from tools.kb.ingest import ingest
from tools.kb.review import decide, status_of, load_decisions
from tools.kb.runtime import load_system, query, route, verify
from tools.kb.store import KB, dump_yaml, write_json, write_jsonl

SENTENCE_A = "Marie Curie was a Polish and naturalised-French physicist and chemist."
SENTENCE_B = "She was the first woman to win a Nobel Prize."


def _row(relation: str, subject: str, obj: str, sentence: str, source: str, chunk: str, **extra: object) -> dict:
    return {
        "relation": relation,
        "subject": subject,
        "object": obj,
        "truth": True,
        "sentence": sentence,
        "source": source,
        "chunk_id": chunk,
        "revid": 1,
        "confidence": 0.9,
        **extra,
    }


def _seed(kb: KB, slug: str, text: str, rows: list[dict]) -> None:
    kb.ensure()
    write_json(
        kb.sources_dir / f"{slug}.json",
        {
            "slug": slug,
            "title": slug.title(),
            "lang": "en",
            "url": f"https://example.test/{slug}",
            "revid": 1,
            "chars": len(text),
            "sha256": "0" * 64,
        },
    )
    (kb.sources_dir / f"{slug}.txt").write_text(text + "\n", encoding="utf-8")
    (kb.work_dir / slug).mkdir(parents=True, exist_ok=True)
    (kb.work_dir / slug / "000.txt").write_text(text + "\n", encoding="utf-8")
    write_jsonl(kb.candidates_dir / slug / "000.jsonl", rows)


def test_proposals_are_context_scoped_and_pending(tmp_path: Path) -> None:
    kb = KB(tmp_path / "kb")
    _seed(
        kb,
        "marie_curie",
        f"{SENTENCE_A} {SENTENCE_B}",
        [
            _row("es", "Marie Curie", "physicist", SENTENCE_A, "marie_curie", "marie_curie/000"),
            _row("es", "She", "woman", SENTENCE_B, "marie_curie", "marie_curie/000"),
            _row("sucks", "Marie Curie", "physics", SENTENCE_A, "marie_curie", "marie_curie/000"),
        ],
    )

    report = ingest(kb)
    assert report["contexts"] == ["marie_curie"]
    assert report["rejected"] == 1
    assert report["proposals"] == 2

    proposals = kb.proposals()
    assert {p["context"] for p in proposals} == {"marie_curie"}
    assert {p["context_id"] for p in proposals} == {"ctx:marie_curie"}
    assert {p["wigame_id"] for p in proposals} == {"wigame:marie_curie:es"}
    assert all(p["status"] == "pending" for p in kb.proposals())

    # nothing is compiled while pending
    manifest = compile_kb(kb)
    assert manifest["totals"]["facts"] == 0
    assert manifest["excluded"]["pending"] == 2
    assert manifest["totals"]["wigames"] == 0


def test_compile_is_context_scoped_and_sets_context_id(tmp_path: Path) -> None:
    kb = KB(tmp_path / "kb")
    _seed(
        kb,
        "marie_curie",
        SENTENCE_A,
        [_row("es", "Marie Curie", "physicist", SENTENCE_A, "marie_curie", "marie_curie/000")],
    )
    ingest(kb)
    proposal_id_value = kb.proposals()[0]["proposal_id"]
    decide(kb, [proposal_id_value], "approved", "tester")

    manifest = compile_kb(kb)
    assert manifest["totals"]["facts"] == 1
    assert list(manifest["wigames"]) == ["wigame:marie_curie:es"]
    assert manifest["wigames"]["wigame:marie_curie:es"]["context_id"] == "ctx:marie_curie"

    contexts = manifest["contexts"]["contexts"]
    assert contexts["ctx:kb"]["subcontexts"] == ["ctx:marie_curie"]
    assert contexts["ctx:marie_curie"]["wigames"] == ["wigame:marie_curie:es"]

    facts = kb.facts()
    assert facts[0]["context"] == "marie_curie"
    assert facts[0]["review"]["decision"] == "approved"
    assert verify(kb)["ok"] is True
    assert query(kb, ["(check wigame:marie_curie:es (es marie_curie physicist))"])["results"][0]["status"] == "accept"


def test_aliases_canonicalize_occurrences_and_link_contexts(tmp_path: Path) -> None:
    kb = KB(tmp_path / "kb")
    _seed(
        kb,
        "marie_curie",
        f"{SENTENCE_A} {SENTENCE_B}",
        [
            _row("es", "She", "woman", SENTENCE_B, "marie_curie", "marie_curie/000"),
            _row("es", "Marie Curie", "chemist", SENTENCE_A, "marie_curie", "marie_curie/000"),
        ],
    )
    _seed(
        kb,
        "rosalind_franklin",
        f"Rosalind Franklin was a chemist. {SENTENCE_A}",
        [
            _row(
                "es",
                "Rosalind Franklin",
                "crystallographer",
                "Rosalind Franklin was a chemist.",
                "rosalind_franklin",
                "rosalind_franklin/000",
            ),
            _row("es", "Marie Curie", "chemist", SENTENCE_A, "rosalind_franklin", "rosalind_franklin/000"),
        ],
    )
    ingest(kb)
    decide(kb, [p["proposal_id"] for p in kb.proposals()], "approved", "tester")

    dump_yaml(
        kb.aliases_path,
        {"aliases": [{"context": "marie_curie", "symbol": "she", "canonical": "marie_curie"}]},
    )
    manifest = compile_kb(kb)

    assert manifest["aliases_applied"] == 1
    assert manifest["totals"]["contexts"] == 2
    subjects = {row["subject"] for row in kb.facts() if row["context"] == "marie_curie"}
    assert subjects == {"marie_curie"}
    assert manifest["projections"], "shared canonical referent must produce cross-context projections"

    system = load_system(kb)
    assert "ctx:kb" in system.contexts and "ctx:marie_curie" in system.contexts
    assert system.projections

    # route_search: both contexts share the referent `marie_curie` after aliasing
    payload = route(
        kb,
        source_wigame_id="wigame:marie_curie:es",
        source_terms=["woman"],
        path=[sorted(system.projections)[0]],
    )
    assert payload["source_hits"] == ["marie_curie"]


def test_review_gate_blocks_pending(tmp_path: Path) -> None:
    kb = KB(tmp_path / "kb")
    _seed(
        kb,
        "marie_curie",
        f"{SENTENCE_A} {SENTENCE_B}",
        [
            _row("es", "Marie Curie", "physicist", SENTENCE_A, "marie_curie", "marie_curie/000"),
            _row("es", "She", "woman", SENTENCE_B, "marie_curie", "marie_curie/000"),
        ],
    )
    ingest(kb)
    proposals = kb.proposals()
    decide(kb, [proposals[0]["proposal_id"]], "approved", "tester")
    decide(kb, [proposals[1]["proposal_id"]], "rejected", "tester", note="pronombre")

    ledger = load_decisions(kb)
    assert status_of(proposals[0], ledger) == "approved"
    assert status_of(proposals[1], ledger) == "rejected"

    manifest = compile_kb(kb)
    assert manifest["totals"]["facts"] == 1
    assert manifest["excluded"] == {"pending": 0, "rejected": 1}
    assert kb.proposals()[1]["subject"] == "she"
    assert json.loads(json.dumps(manifest["review"]["by_status"])) == {"pending": 0, "approved": 1, "rejected": 1}
