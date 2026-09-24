#!/usr/bin/env bash
# Test 2: Can pi read local files?
echo "=== Test 02: Can pi read local files? ==="
echo "Read src/external_formats/unl/unl_converter.py and tell me the first 5 lines." | \
  pi --provider ollama --model gemma4 2>&1
echo "=== End Test 02 ==="
