"""LLM-assisted curation: a backend drafts proposals, a human still promotes."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import re
import subprocess
from typing import Any, Callable, TYPE_CHECKING

from populator import read_documents

if TYPE_CHECKING:
    from src.operational_model import LogicalSystem

Backend = Callable[[str], str]

DEFAULT_MODEL = "deepseek/deepseek-flash"
DEFAULT_TIMEOUT = 90
_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


class PiBackend:
    """Calls the `pi` CLI in non-interactive, tool-less mode."""

    def __init__(self, model: str = DEFAULT_MODEL, timeout: int = DEFAULT_TIMEOUT) -> None:
        self.model = model
        self.timeout = timeout
        self.name = f"pi:{model}"

    def __call__(self, prompt: str) -> str:
        command = [
            "pi",
            "-p",
            "--no-tools",
            "--no-session",
            "--no-extensions",
            "--no-skills",
            "--model",
            self.model,
            prompt,
        ]
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=self.timeout,
            check=True,
        )
        return completed.stdout


class FakeBackend:
    """Returns a canned reply, for tests and dry runs."""

    def __init__(self, reply: str) -> None:
        self.reply = reply
        self.name = "fake"

    def __call__(self, prompt: str) -> str:
        return self.reply


@dataclass
class Proposal:
    """One LLM draft for a queued candidate."""

    sexpr: str
    prov_index: int
    keep: bool
    comment: str
    candidate_id: str = ""


def build_prompt(candidate: Any, sentences: list[str], vocabulary: list[str]) -> str:
    """Builds the curation prompt asking for a single JSON object."""

    quotes = "\n".join(f"[{index}] {sentence.strip()}" for index, sentence in enumerate(sentences))
    vocab = ", ".join(vocabulary[:200])
    return (
        "Eres un curador de una base de conocimiento lógica. Recibes un candidato "
        "estadístico y las oraciones que lo respaldan.\n"
        f"Candidato: kind={candidate.kind} wigame={candidate.wigame_id} payload={json.dumps(candidate.payload, ensure_ascii=False)}\n"
        f"Oraciones citadas:\n{quotes or '(sin oraciones)'}\n"
        f"Vocabulario del mundo: {vocab}\n\n"
        "Responde SOLO un objeto JSON con las claves "
        '{"sexpr": "<S-expression canónica>", "prov_index": <índice de la oración citada>, '
        '"keep": <true|false>, "comment": "<motivo breve>"}. '
        "No añadas texto fuera del JSON."
    )


def propose(
    system: "LogicalSystem",
    candidate_id: str,
    backend: Backend,
    documents: list,
) -> Proposal:
    """Asks the backend to draft a proposal and records it under `evidence.llm`."""

    candidate = system.candidates.get(candidate_id)
    if candidate is None:
        raise KeyError(candidate_id)
    sentences = _cited_sentences(candidate, documents)
    vocabulary = _vocabulary(system, candidate)
    prompt = build_prompt(candidate, sentences, vocabulary)
    reply = backend(prompt)
    proposal = _parse_reply(reply)
    proposal.candidate_id = candidate_id
    candidate.evidence["llm"] = {
        "sexpr": proposal.sexpr,
        "prov_index": proposal.prov_index,
        "keep": proposal.keep,
        "comment": proposal.comment,
        "backend": getattr(backend, "name", type(backend).__name__),
    }
    return proposal


def curate_queue(
    system: "LogicalSystem",
    backend: Backend,
    documents: list,
    limit: int = 20,
    only_kind: str = "fact",
) -> list[Proposal]:
    """Drafts proposals for the first `limit` queued candidates of one kind."""

    proposals: list[Proposal] = []
    for candidate in select_candidates(system, limit=limit, only_kind=only_kind):
        proposals.append(propose(system, candidate.candidate_id, backend, documents))
    return proposals


def select_candidates(system: "LogicalSystem", limit: int = 20, only_kind: str = "fact") -> list:
    """Returns the queued candidates of one kind, highest entropic phi first."""

    candidates = [
        candidate
        for candidate in system.candidates.values()
        if candidate.kind == only_kind and candidate.evidence.get("curation") == "proposed"
    ]
    candidates.sort(
        key=lambda candidate: -float(candidate.evidence.get("stats", {}).get("phi_entropic", 0.0))
    )
    return candidates[:limit]


def _cited_sentences(candidate: Any, documents: list) -> list[str]:
    by_id = {document.document_id: document for document in documents}
    sentences: list[str] = []
    for prov in candidate.evidence.get("prov", []):
        document = by_id.get(prov.get("document_id"))
        if document is None:
            continue
        start, end = prov.get("span", [0, 0])
        sentences.append(document.text[start:end])
    return sentences[:5]


def _vocabulary(system: "LogicalSystem", candidate: Any) -> list[str]:
    if candidate.wigame_id is not None and candidate.wigame_id in system.wigames:
        wigame = system.wigames[candidate.wigame_id]
        return sorted(set(wigame.axis_a) | set(wigame.axis_b))
    return sorted(system.symbols)


def _parse_reply(reply: str) -> Proposal:
    match = _JSON_RE.search(reply)
    if match is None:
        return Proposal(sexpr="", prov_index=0, keep=False, comment=reply.strip()[:200])
    try:
        payload = json.loads(match.group(0))
    except json.JSONDecodeError:
        return Proposal(sexpr="", prov_index=0, keep=False, comment=match.group(0)[:200])
    return Proposal(
        sexpr=str(payload.get("sexpr", "")),
        prov_index=int(payload.get("prov_index", 0)),
        keep=bool(payload.get("keep", False)),
        comment=str(payload.get("comment", "")),
    )


def main(argv: list[str] | None = None) -> int:
    """Runs the curation CLI over one corpus world."""

    from pipeline.run import build_system

    parser = argparse.ArgumentParser(description="Draft LLM proposals for queued candidates.")
    parser.add_argument("corpus_dir")
    parser.add_argument("--wigame", default="vegetales")
    parser.add_argument("--backend", choices=["pi", "fake"], default="fake")
    parser.add_argument("--lang", choices=["es", "en"], default=None)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--kind", default="fact")
    args = parser.parse_args(argv)

    from populator import build_corpus

    documents = read_documents(args.corpus_dir)
    corpus = build_corpus(documents, lang=args.lang)
    system, _, _ = build_system(
        args.corpus_dir, args.wigame, lang=args.lang, corpus=corpus, documents=documents
    )
    backend: Backend = PiBackend() if args.backend == "pi" else FakeBackend(
        json.dumps({"sexpr": "", "prov_index": 0, "keep": True, "comment": "fake backend"})
    )
    proposals = curate_queue(system, backend, documents, limit=args.limit, only_kind=args.kind)
    print(f"{'candidato':28} {'propuesta':44} keep  comentario")
    for proposal in proposals:
        print(
            f"{proposal.candidate_id:28} {proposal.sexpr[:44]:44} "
            f"{str(proposal.keep):5} {proposal.comment[:60]}"
        )
    print(f"propuestas: {len(proposals)} (curation sin cambios; promueve con `aprueba <id>`)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
