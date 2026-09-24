#!/usr/bin/env bash
# Test 6: Can pi read local files using its built-in tools?
echo "=== Test 06: pi reading local file ==="
echo "Read the file /home/dios/Matrix/Matrix/src/external_formats/unl/unl_converter.py 
Then explain what class it defines and what the unl_to_sexprs method does." | \
  timeout 300 pi --provider ollama --model gemma4 2>&1
echo "EXIT: $?"
echo "=== End Test 06 ==="
