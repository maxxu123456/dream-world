#!/usr/bin/env bash
# One-time setup: download the Dream World server and install its Python packages.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

command -v git     >/dev/null || { echo "Install git first."; exit 1; }
command -v python3 >/dev/null || { echo "Install Python 3 first."; exit 1; }
command -v java    >/dev/null || echo "Note: Java was not found. The Dream World server needs a JRE to patch the Flash files. Install one (for example Temurin) before running scripts/run-dreamworld.sh."

if [ -d server/.git ]; then
  echo "Updating existing server checkout..."
  git -C server pull --recurse-submodules --ff-only || true
  git -C server submodule update --init --recursive
else
  echo "Cloning minibug1021/dreamworld-reawakened (with submodules)..."
  git clone --recursive https://github.com/minibug1021/dreamworld-reawakened.git server
fi

# Use a dedicated virtualenv so the packages are found whether we run as you or
# with sudo (the Game Sync server needs root for port 53), and so we do not fight
# a system-managed Python (PEP 668).
echo "Creating virtualenv at server/.venv and installing packages..."
python3 -m venv server/.venv
server/.venv/bin/python -m pip install --upgrade pip
server/.venv/bin/python -m pip install -r server/requirements.txt
server/.venv/bin/python -m pip install -r server/game_sync_server/requirements.txt

echo
echo "Setup done. Next steps:"
echo "  1. scripts/run-gamesync.sh     (start first; needs your password for port 53)"
echo "  2. scripts/find-lan-ip.sh      (get the DNS IP to type into your DS)"
echo "  3. scripts/run-dreamworld.sh   (the Dream World website on port 8080)"
echo "  See docs/dsi-setup.md and docs/flash-setup.md."
