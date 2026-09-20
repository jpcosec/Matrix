#!/usr/bin/env bash
# Regenerates the deterministic part of the gold examples (no LLM, no network).
set -euo pipefail

cd "$(dirname "$0")/.."
KB="${1:-/tmp/kb_examples_machine}"
rm -rf "$KB"

echo "== machine/recipes KB =="
python -m tools.kb --kb "$KB" machine >/dev/null
python -m tools.kb --kb "$KB" ingest >/dev/null
python -m tools.kb --kb "$KB" review all --decision approved --reviewer operatoria >/dev/null
python -m tools.kb --kb "$KB" compile >/dev/null
python -m tools.kb --kb "$KB" verify --fail-on-problems >/dev/null
python -m tools.kb --kb "$KB" reachability >/dev/null
python -m tools.kb --kb "$KB" capabilities >/dev/null
echo "   built at $KB"

echo "== ragout demo =="
python examples/ragout_demonstration.py >/dev/null

echo "== digests =="
python examples/collect_digests.py "$KB=machine_recipes"

echo "== tests =="
python -m pytest tests/test_kb_machine.py tests/test_kb_fanout.py tests/test_ragout_demonstration.py -q
