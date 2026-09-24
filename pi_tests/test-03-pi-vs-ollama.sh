#!/usr/bin/env bash
# Test 3: Compare pi vs direct Ollama API
echo "=== Test 03: pi vs direct Ollama ==="

echo "--- Direct Ollama API ---"
time curl -s -X POST http://localhost:11434/api/generate \
  -d '{"model":"gemma4","prompt":"What does the UNLConverter class do? Answer in 10 words.","stream":false}' | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('response','?')[:200])"

echo ""
echo "--- pi (with --quiet maybe?) ---"
timeout 30 pi --provider ollama --model gemma4 "Hello" 2>&1 || echo "pi timed out"

echo "=== End Test 03 ==="
