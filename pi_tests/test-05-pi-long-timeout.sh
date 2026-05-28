#!/usr/bin/env bash
# Test 5: pi with longer timeout
echo "=== Test 05: pi with 5min timeout ==="
echo "Hi" | timeout 300 pi --no-tools --no-session --provider ollama --model gemma4 2>&1
echo "EXIT: $?"
echo "=== End Test 05 ==="
