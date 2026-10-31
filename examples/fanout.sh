#!/usr/bin/env bash
# Fan-out KB extraction to free pi workers (default: deepseek-flash).
# Usage: bash examples/fanout.sh <kb-dir> [parallel] [provider] [model]
set -uo pipefail

KB="${1:?usage: fanout.sh <kb-dir> [parallel] [provider] [model]}"
PARALLEL="${2:-6}"
PROVIDER="${3:-deepseek}"
MODEL="${4:-deepseek-flash}"
export KB PROVIDER MODEL

run_one() {
  local prompt="$1" out="$2"
  [ -s "$prompt" ] || return 0
  timeout 300 pi -p --provider "$PROVIDER" --model "$MODEL" \
    --no-tools --no-session --no-skills --no-context-files \
    "$(cat "$prompt")

Return ONLY the JSONL lines. No markdown fences, no commentary." > "$out" 2> "$out.err"
  printf 'exit=%s lines=%s %s\n' "$?" "$(grep -c . "$out" 2>/dev/null || echo 0)" "$out"
}
export -f run_one

for src_dir in "$KB"/work/*/; do
  src="$(basename "$src_dir")"
  mkdir -p "$KB/candidates/$src"
  for prompt in "$src_dir"*.prompt.md; do
    [ -s "$prompt" ] || continue
    echo "$prompt|$KB/candidates/$src/$(basename "$prompt" .prompt.md).jsonl"
  done
done | xargs -P "$PARALLEL" -I{} bash -c 'IFS="|" read -r p o <<< "{}"; run_one "$p" "$o"'
