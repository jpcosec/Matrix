#!/usr/bin/env python3
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
from matrix_engine import MatrixEngine


def main():
    parser = argparse.ArgumentParser(description="Matrix Engine CLI")
    parser.add_argument("file", help="Path to YAML schema")
    parser.add_argument("--query", nargs="+", help="Properties to query")
    parser.add_argument("--status", nargs=2, metavar=("object", "property"), help="Get status of object property")
    parser.add_argument("--tautologies", action="store_true", help="Show tautological properties")
    parser.add_argument("--ambiguous", action="store_true", help="Show ambiguous objects")
    args = parser.parse_args()

    engine = MatrixEngine.load(args.file)

    if args.query:
        results = engine.query(args.query)
        print(f"Objects with {args.query}: {results}")

    if args.status:
        obj, prop = args.status
        result = engine.get_status(obj, prop)
        print(f"Status: {result}")

    if args.tautologies:
        print(f"Tautologies: {engine.detect_tautologies()}")

    if args.ambiguous:
        print(f"Ambiguous: {engine.detect_ambiguous()}")


if __name__ == "__main__":
    main()
