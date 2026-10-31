#!/usr/bin/env bash
# Runs a command inside its own memory-capped cgroup so that an out-of-memory
# condition kills only that command, never the terminal or the agents around it.
#
#   bash scripts/capped.sh <MEM_GB> -- <command...>
#
# Uses a transient systemd user scope (MemoryMax, no swap); falls back to a
# virtual-memory ulimit when systemd-run is unavailable.
set -euo pipefail
if [ "${1:-}" = "" ] || [ "${2:-}" != "--" ]; then
  echo "usage: $0 <MEM_GB> -- <command...>" >&2
  exit 2
fi
MEM_GB="$1"; shift 2
if command -v systemd-run >/dev/null 2>&1 \
   && systemd-run --user --scope --quiet -p MemoryMax=64M -- true 2>/dev/null; then
  exec systemd-run --user --scope --quiet --collect \
    -p "MemoryMax=${MEM_GB}G" -p MemorySwapMax=0 -- "$@"
fi
ulimit -v $(( MEM_GB * 1024 * 1024 ))
exec "$@"
