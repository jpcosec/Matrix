"""Tests for one-call-per-chunk LLM decomposition and its cache."""

from __future__ import annotations

import json

from pipeline.decompose import build_chunk_prompt, decompose_llm_chunk
from pipeline.llm_cache import cache_key, cached_decompose, read_cache
from populator import build_context, chunk_documents
from populator.extract import Document

TEXT = (
    "# Marie Curie\n\n"
    "Marie Curie was born in Warsaw. She studied at the Sorbonne.\n"
)


class CountingBackend:
    """Backend that returns canned replies and counts the calls."""

    name = "counting"

    def __init__(self, replies: list[str]) -> None:
        self.replies = list(replies)
        self.calls = 0

    def __call__(self, prompt: str) -> str:
        self.calls += 1
        return self.replies.pop(0) if len(self.replies) > 1 else self.replies[0]


def build_chunk():
    return build_context(chunk_documents([Document("Q7186.md", TEXT)])[0], lang="en")


VALID = [
    {"s": 0, "r": "born_in", "a_sign": "Marie Curie", "b_sign": "Warsaw"},
    {"s": 1, "r": "rel:study", "a_sign": "she", "b_sign": "Sorbonne"},
]
INVALID = [
    {"s": 0, "r": "invented", "a_sign": "Marie Curie", "b_sign": "Warsaw"},
    {"s": 0, "r": "born_in", "a_sign": "Marie Curie", "b_sign": "Mars"},
    {"s": 0, "r": "born_in", "a_sign": 42, "b_sign": "Warsaw"},
]


def test_prompt_lists_sentences_signs_and_relations():
    prompt = build_chunk_prompt(build_chunk())

    assert "Marie Curie" in prompt
    assert "symbol_id=marie_curie@Q7186" in prompt
    assert "she@Q7186" in prompt
    assert "born_in" in prompt and "rel:<verbo en infinitivo>" in prompt
    assert "[0]" in prompt and "[1]" in prompt


def test_valid_triples_survive_and_invalid_are_dropped():
    backend = CountingBackend([json.dumps(VALID + INVALID)])

    declarations = decompose_llm_chunk(build_chunk(), backend)

    assert backend.calls == 1
    assert [(d.relation, d.a, d.b) for d in declarations] == [
        ("born_in", "marie_curie@Q7186", "warsaw@Q7186"),
        ("rel:study", "she@Q7186", "sorbonne@Q7186"),
    ]
    assert all(d.source == "llm" for d in declarations)
    # The span is the cited sentence: 0 is the title line, 1 the birth sentence.
    assert declarations[0].sentence_index == 0
    assert declarations[0].span == (0, 13)
    assert declarations[1].sentence_index == 1
    assert declarations[1].span == (15, 46)


def test_json_wrapped_in_prose_is_accepted():
    backend = CountingBackend(["Claro, aquí va:\n```json\n" + json.dumps(VALID) + "\n```\nFin."])

    declarations = decompose_llm_chunk(build_chunk(), backend)

    assert len(declarations) == 2


def test_bad_json_is_retried_once():
    backend = CountingBackend(["no soy json", json.dumps(VALID)])

    declarations = decompose_llm_chunk(build_chunk(), backend)

    assert backend.calls == 2
    assert len(declarations) == 2


def test_cache_writes_and_reads_without_calling_again(tmp_path):
    cache = tmp_path / "declarations_llm.jsonl"
    backend = CountingBackend([json.dumps(VALID)])
    chunk = build_chunk()

    first = cached_decompose(chunk, backend, path=cache)
    second = cached_decompose(chunk, backend, path=cache)

    assert backend.calls == 1
    assert [(d.relation, d.a, d.b) for d in second] == [(d.relation, d.a, d.b) for d in first]
    entry = json.loads(cache.read_text(encoding="utf-8").splitlines()[0])
    assert entry["key"] == cache_key(chunk)
    assert entry["ctx_id"] == "Q7186"
    assert len(entry["declarations"]) == 2
    assert set(read_cache(cache)) == {cache_key(chunk)}


def test_cache_miss_without_backend_is_empty(tmp_path):
    cache = tmp_path / "declarations_llm.jsonl"

    assert cached_decompose(build_chunk(), None, path=cache) == []
    assert not cache.exists()
