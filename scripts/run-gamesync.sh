#!/usr/bin/env bash
# Start the Game Sync server (the part your physical DS connects to).
# Run this BEFORE the Dream World server. It needs root because it uses port 53.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="$ROOT/server/.venv/bin/python"
[ -x "$PY" ] || { echo "Run scripts/setup.sh first."; exit 1; }
cd "$ROOT/server/game_sync_server"
echo "Starting Game Sync server. It will print the DNS IP to type into your DS."
exec sudo -- "$PY" server.py
