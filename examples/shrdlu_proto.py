"""Minimal proto-SHRDLU harness over the Matrix language layer."""

from __future__ import annotations

import argparse

from src.operational_model import ParseError, parse_controlled_english


def main() -> int:
    """Runs one-shot or interactive controlled-English parsing."""

    parser = argparse.ArgumentParser(description="Parse controlled English into Matrix semantic frames.")
    parser.add_argument("--once", help="Parse one sentence and exit.")
    args = parser.parse_args()

    if args.once:
        return _run_once(args.once)
    return _run_repl()


def _run_once(sentence: str) -> int:
    """Parses one sentence and prints the semantic frame."""

    try:
        print(parse_controlled_english(sentence).to_sexpr())
        return 0
    except ParseError as exc:
        print(f"error: {exc}")
        return 1


def _run_repl() -> int:
    """Runs a tiny interactive loop for proto-SHRDLU testing."""

    print("Proto-SHRDLU for Matrix. Type 'exit' to quit.")
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
        _run_once(sentence)


if __name__ == "__main__":
    raise SystemExit(main())
