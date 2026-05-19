"""Minimal proto-SHRDLU harness over the separate prototype package."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from prototypes.shrdlu import ParseError
from prototypes.shrdlu.lowering import PrototypeHarness


def main() -> int:
    """Runs one-shot or interactive controlled-English parsing."""

    parser = argparse.ArgumentParser(
        description="Parse controlled English into SHRDLU prototype semantic frames."
    )
    parser.add_argument("--once", help="Parse one sentence and exit.")
    args = parser.parse_args()

    if args.once:
        return _run_once(args.once)
    return _run_repl()


def _run_once(sentence: str) -> int:
    harness = PrototypeHarness()
    try:
        print(harness.execute(sentence))
        return 0
    except ParseError as exc:
        print(f"error: {exc}")
        return 1


def _run_repl() -> int:
    print("Proto-SHRDLU for Matrix. Type 'exit' to quit.")
    harness = PrototypeHarness()
    while True:
        try:
            sentence = input("> ").strip()
        except EOFError:
            print()
            return 0
        if sentence.lower() in {"exit", "quit"}:
            return 0
        if not sentence:
            continue
        try:
            print(harness.execute(sentence))
        except ParseError as exc:
            print(f"error: {exc}")


if __name__ == "__main__":
    raise SystemExit(main())
