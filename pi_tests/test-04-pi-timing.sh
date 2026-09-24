echo "=== Test 04: pi timing analysis ==="
echo "Test a: pi with --no-tools 'hi' (30s timeout)"
timeout 30 pi --no-tools --no-session --provider ollama --model gemma4 "hi" 2>&1
echo "EXIT: $?"
echo ""
echo "Test b: curl Ollama 'hi' (direct)"
time curl -s -X POST http://localhost:11434/api/generate -d '{"model":"gemma4","prompt":"hi","stream":false}' | python3 -c "import sys,json; d=json.load(sys.stdin); print('Response:', d.get('response','?')[:100]); print('Duration:', d.get('total_duration',0)//1000000,'ms')"
echo "=== End Test 04 ==="
