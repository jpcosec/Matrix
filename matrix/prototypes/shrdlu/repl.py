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

from .dialog_state import DialogState
from .spanish import Clarification, fold, parse_es

_SALIR = {"salir", "exit", "quit"}


@dataclass
class Repl:
    """Verbalizes runtime results in Spanish for one focused conversation."""

    system: LogicalSystem
    runtime: SExpressionRuntime
    dialog: DialogState = field(default_factory=DialogState)

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
        parsed = parse_es(text, self.dialog)
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
        return self._verbalize(sexpr, self.runtime.evaluate(sexpr))

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


def _citations(prov: list[dict]) -> str:
    if not prov:
        return "sin cita"
    return ", ".join(f"{entry['document_id']}:{entry['span'][0]}-{entry['span'][1]}" for entry in prov)


def build_repl(corpus_dir: str | Path = "corpus/vegetales", wigame_id: str = "vegetales") -> Repl:
    """Builds a REPL over the WiGame produced by the pipeline."""

    from pipeline.run import build_system

    location = Path(corpus_dir)
    if not location.exists() and (_REPO_ROOT / location).exists():
        location = _REPO_ROOT / location
    system, runtime, _ = build_system(location, wigame_id)
    dialog = DialogState(focus_wigame=f"wigame:{wigame_id}", system=system)
    return Repl(system=system, runtime=runtime, dialog=dialog)


def main(argv: list[str] | None = None) -> int:
    """Runs the Spanish REPL from the command line."""

    args = list(sys.argv[1:] if argv is None else argv)
    corpus_dir = args[0] if args else "corpus/vegetales"
    repl = build_repl(corpus_dir)
    print("REPL SHRDLU (escribe `salir` para terminar)")
    repl.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
