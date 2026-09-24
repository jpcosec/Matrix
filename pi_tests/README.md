# pi + Gemma4 capability tests

## Setup
- **pi**: `@mariozechner/pi-coding-agent` (Node.js CLI)
- **Model**: `gemma4:latest` (8B, Q4_K_M, 9.6GB) via local Ollama

## Test Results

| # | Test | Result | Notes |
|---|------|--------|-------|
| 01 | Basic prompt | ✅ Works | Needs model pre-warmed (first cold start ~28s) |
| 02 | Read local file | ✅ Works | pi reads files and summarizes code accurately |
| 03 | Run bash command (`ls`) | ❌ Timeout | Tool execution hangs with Gemma4 |
| 04 | Run pytest | ❌ Timeout | Multi-step tool use times out |
| 05 | Read + analyze code | ✅ Works | Correctly described UNLConverter class |
| 06 | `--no-tools` mode | ❌ Timeout | Even without tools, simple prompts hang |

## Conclusions
1. **pi + Gemma4 is viable for read-only tasks** — file reading and code summarization works well
2. **Tool execution is unreliable** — bash/edit/write tools time out with Gemma4 on Ollama
3. **Cold start is slow** (~28s for first prompt; subsequent prompts faster if kept warm)
4. **Pre-warming is essential** — without it, pi almost always times out at default limits

## Recommended usage
- Use for code review and analysis only
- Pre-warm Ollama before each interaction
- Set generous timeouts (≥120s)
- For tool execution, use direct Ollama API or another backend
