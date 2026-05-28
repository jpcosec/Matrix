#!/usr/bin/env bash
# Test 1: Basic prompt — can pi/gemma understand the Matrix repo?
echo "=== Test 01: Basic prompt to pi with gemma4 ==="
echo "What is the purpose of the src/operational_model/ package?" | \
  pi --provider ollama --model gemma4 2>&1
echo "=== End Test 01 ==="
