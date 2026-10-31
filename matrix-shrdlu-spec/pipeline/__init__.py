"""Pipeline package: SIA statistics to Matrix WiGames, plus the SHRDLU REPL glue."""

from __future__ import annotations

from pathlib import Path
import sys

_MATRIX_ROOT = Path(__file__).resolve().parents[2]
if str(_MATRIX_ROOT) not in sys.path:
    sys.path.append(str(_MATRIX_ROOT))


def build_system(corpus_dir, wigame_id: str = "vegetales", **kwargs):
    """Builds the logical system, runtime and results for a corpus."""

    from .run import build_system as _build_system

    return _build_system(corpus_dir, wigame_id, **kwargs)


def main(argv: list[str] | None = None) -> int:
    """Runs the corpus to WiGame pipeline CLI."""

    from .run import main as _main

    return _main(argv)


__all__ = [
    "build_system",
    "main",
]
