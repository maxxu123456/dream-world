#!/usr/bin/env bash
# Start the Dream World website (the Flash game) on port 8080.
# Needs Java on your PATH so it can patch the Flash files on startup.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="$ROOT/server/.venv/bin/python"
[ -x "$PY" ] || { echo "Run scripts/setup.sh first."; exit 1; }
cd "$ROOT/server"
exec "$PY" main.py
