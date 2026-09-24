"""Interactive Spanish REPL over a Matrix logical system."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
import sys

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.append(str(_REPO_ROOT))

from src.operational_model import LogicalSystem, OperationResult, SExpressionRuntime, TruthValue

from .text_norm import normalize

from .dialog_state import DialogState
from .spanish import Clarification, _symbols_for, fold, parse_es

_SALIR = {"salir", "exit", "quit"}

# Simple English questions answered by routed queries (no LLM involved).
_QUESTIONS: tuple[tuple[re.Pattern[str], str, bool], ...] = (
    (re.compile(r"^was\s+(.+?)\s+born\s+in\s+(.+?)$"), "born_in", True),
    (re.compile(r"^did\s+(.+?)\s+win\s+(.+?)$"), "award", True),
    (re.compile(r"^what\s+did\s+(.+?)\s+discover$"), "discovered", False),
)


@dataclass
class Repl:
    """Verbalizes runtime results in Spanish for one focused conversation."""

    system: LogicalSystem
    runtime: SExpressionRuntime
    dialog: DialogState = field(default_factory=DialogState)
    backend: object | None = None
    documents: list = field(default_factory=list)
    last_question: tuple[str, str, str] | None = None

    def step(self, line: str) -> str:
        """Processes one user line and returns the answer text."""

        text = line.strip()
        if not text:
            return ""
        norm = fold(text)
        if self.dialog.pending is not None and re.fullmatch(r"\d+", norm):
            return self._run(self.dialog.answer(norm))
        if norm in _SALIR:
            return "Hasta luego."
        if norm.startswith("sugiere "):
            return self._suggest(norm.split(None, 1)[1])
        if norm in {"why", "por que", "porque"} and self.last_question is not None:
            return self._why_last()
        answer = self._answer_question(norm)
        if answer is not None:
            return answer
        try:
            parsed = parse_es(text, self.dialog)
        except ValueError:
            return f"No entiendo «{text}»."
        if isinstance(parsed, Clarification):
            self.dialog.pending = parsed
            return parsed.question
        return self._run(parsed)

    def run(self, prompt: str = "> ") -> None:
        """Reads lines until ``salir`` and prints each answer."""

        while True:
            try:
                line = input(prompt)
            except EOFError:
                break
            if fold(line) in _SALIR:
                break
            print(self.step(line))

    def _run(self, sexpr: str) -> str:
        if sexpr.startswith("(ask "):
            return self._run_ask(sexpr)
        return self._verbalize(sexpr, self.runtime.evaluate(sexpr))

    def _run_ask(self, sexpr: str) -> str:
        """Answers a Spanish question through `pipeline.query.ask`."""

        from pipeline.query import ask

        parts = sexpr.strip("()").split()
        if len(parts) != 4:
            return "No entiendo la pregunta."
        relation, subject, obj = parts[1], parts[2], parts[3]
        answer = ask(self.system, relation, subject, obj)
        return self._render_answer(answer, obj)

    def _answer_question(self, norm: str) -> str | None:
        """Answers simple English questions with `ask`, without any LLM."""

        from pipeline.query import ask

        for pattern, relation, has_object in _QUESTIONS:
            match = pattern.fullmatch(norm)
            if match is None:
                continue
            subjects = _symbols_for(match.group(1), self.dialog)
            if not subjects:
                return f"No conozco «{match.group(1)}»."
            object_norm = match.group(2) if has_object else None
            # A sign maps to many symbols (one per context): prefer the one that
            # actually answers the question, then the first by name.
            subject = subjects[0]
            answer = ask(self.system, relation, subject, object_norm)
            for candidate in subjects[1:]:
                attempt = ask(self.system, relation, candidate, object_norm)
                if attempt.objects:
                    subject, answer = candidate, attempt
                    break
            if object_norm:
                context = subject.split("@", 1)[-1]
                obj = answer.objects[0][0] if answer.objects else f"{_as_symbol(object_norm)}@{context}"
                self.last_question = (relation, subject, obj)
                if answer.objects:
                    # Enables the Spanish bare ``¿por qué?`` over the last turn.
                    self.dialog.remember_turn("why", subject, obj, relation)
            return self._render_answer(answer, object_norm)

    def _why_last(self) -> str:
        """Explains the last answered question (SHRDLU's ``WHY``)."""

        relation, subject, obj = self.last_question  # type: ignore[misc]
        context = subject.split("@", 1)[-1]
        return self._run(f"(why wigame:{context}:{relation} ({relation} {subject} {obj}))")
        return None

    def _render_answer(self, answer, object_norm: str | None) -> str:
        outcome = answer.truth_for(object_norm)
        if outcome == "true" and answer.objects:
            symbol, ctx, _, prov = answer.objects[0]
            citation = ""
            if prov:
                citation = f" [{prov[0]['document_id']}:{prov[0]['span'][0]}-{prov[0]['span'][1]}]"
            route = " -> ".join(answer.path[:3])
            return f"Sí: ({answer.relation} {answer.subject} {symbol}){citation} · ruta: {route}"
        if outcome == "false":
            return "No."
        return "No lo sé (nadie lo ha confirmado)."

    def _suggest(self, candidate_id: str) -> str:
        """Asks the LLM backend for a draft proposal without confirming anything."""

        from pipeline.curate import PiBackend, propose

        backend = self.backend or PiBackend()
        try:
            proposal = propose(self.system, candidate_id, backend, self.documents)
        except Exception as error:  # noqa: BLE001 - the REPL reports backend failures as text
            return f"No pude consultar al backend: {error}"
        return (
            f"Propuesta: {proposal.sexpr or '(vacía)'} "
            f"[prov {proposal.prov_index}; keep={proposal.keep}] {proposal.comment}"
        )

    def _verbalize(self, sexpr: str, result: OperationResult) -> str:
        payload = result.payload or {}
        if sexpr.startswith("(why"):
            return self._describe_why(payload)
        if sexpr.startswith("(return candidates"):
            return self._describe_candidates(payload)
        if sexpr.startswith("(return facts"):
            return self._describe_facts(payload)
        if sexpr.startswith("(define"):
            derived = ", ".join(payload.get("derived", [])) or "ninguno"
            return f"Regla añadida. Derivados: {derived}."
        if sexpr.startswith("(retract"):
            return (
                f"Retirado: {payload.get('proposition')} = {payload.get('truth')}. "
                f"Dependientes: {len(payload.get('dependents', []))}."
            )
        if sexpr.startswith("(promote") and result.status == "accept":
            return f"Confirmado: {payload.get('kind', 'candidato')}."
        if sexpr.startswith("(reject") and result.status == "accept":
            return f"Rechazado: {payload.get('candidate_id', '')}."
        if result.status == "ambiguous":
            options = payload.get("candidates", [])
            return "Ambiguo: " + " | ".join(options) + ". Repite con wigame:<id>."
        if "truth" in payload:
            truth = payload["truth"]
            if truth == TruthValue.TRUE.value:
                return "Sí."
            if truth == TruthValue.FALSE.value:
                return "No."
            return "No lo sé (nadie lo ha confirmado)."
        if result.status == "reject":
            return f"No: {result.reason}."
        return "Hecho."

    def _describe_why(self, payload: dict) -> str:
        lines: list[str] = []
        for node in payload.get("chain", []):
            citations = _citations(node.get("prov") or [])
            lines.append(f"porque {node.get('proposition')} [{node.get('tier')}; {citations}]")
        return "\n".join(lines) or "No tengo una justificación."

    def _describe_candidates(self, payload: dict) -> str:
        records = payload.get("candidates", [])
        if not records:
            return "No hay candidatos pendientes."
        return "\n".join(
            f"{index + 1}) {record['candidate_id']} {record['kind']} {record['payload']}"
            for index, record in enumerate(records)
        )

    def _describe_facts(self, payload: dict) -> str:
        lines: list[str] = []
        for group in payload.get("groups", []):
            lines.append(f"{group['wigame_id']}:")
            for fact in group.get("facts", []):
                lines.append(f"  {fact['proposition']} = {fact['truth']}")
        return "\n".join(lines) or "Sin hechos."


def _as_symbol(sign: str) -> str:
    """Normalizes a surface sign into a symbol name (without its context)."""

    return normalize(sign.split("@", 1)[0]).replace(" ", "_")


def _citations(prov: list[dict]) -> str:
    if not prov:
        return "sin cita"
    return ", ".join(f"{entry['document_id']}:{entry['span'][0]}-{entry['span'][1]}" for entry in prov)


def build_repl(
    corpus_dir: str | Path = "corpus/vegetales",
    wigame_id: str = "vegetales",
    *,
    unit: str = "document",
    lang: str | None = None,
    limit: int | None = None,
) -> Repl:
    """Builds a REPL over the WiGame produced by the pipeline."""

    from pipeline.run import build_system

    location = Path(corpus_dir)
    if not location.exists() and (_REPO_ROOT / location).exists():
        location = _REPO_ROOT / location
    from populator import read_documents

    documents = read_documents(location)
    system, runtime, _ = build_system(location, wigame_id, unit=unit, lang=lang, limit=limit)
    dialog = DialogState(focus_wigame=f"wigame:{wigame_id}", system=system)
    return Repl(system=system, runtime=runtime, dialog=dialog, documents=documents)


def main(argv: list[str] | None = None) -> int:
    """Runs the Spanish REPL from the command line."""

    import argparse

    parser = argparse.ArgumentParser(description="Conversational REPL over a corpus world.")
    parser.add_argument("corpus_dir", nargs="?", default="corpus/vegetales")
    parser.add_argument("--wigame", default=None, help="world id (default: corpus directory name)")
    parser.add_argument("--unit", choices=["document", "section"], default="document")
    parser.add_argument("--lang", choices=["es", "en"], default=None)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args(argv)

    wigame_id = args.wigame or Path(args.corpus_dir).resolve().name
    repl = build_repl(
        args.corpus_dir, wigame_id, unit=args.unit, lang=args.lang, limit=args.limit
    )
    print("REPL SHRDLU (escribe `salir` para terminar)")
    repl.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
