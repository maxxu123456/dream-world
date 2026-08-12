#!/usr/bin/env bash
# Container entrypoint: keep Game Sync available for the first tuck-in, then
# start the Dream World website once uploaded player data is ready.
set -euo pipefail

: "${HOST_IP:?Set -e HOST_IP to the LAN IPv4 address shared with your DS; see README.md}"
: "${FRIEND_CODE:?Set -e FRIEND_CODE to the 12-digit code shown in the game Pal Pad; see README.md}"

# A Nintendo DS Friend Code contains the GameSpy profile ID already stored in
# the cartridge save. Reusing that ID prevents error 60000 on a fresh server.
profile_id_file="/tmp/dream-world-profile-id"
FRIEND_CODE="$FRIEND_CODE" python3 - <<'PY' > "$profile_id_file"
import os

raw = os.environ["FRIEND_CODE"]
digits = "".join(character for character in raw if character.isascii() and character.isdigit())
separators = "".join(character for character in raw if not character.isdigit())

if any(not (character == "-" or character.isspace()) for character in separators):
    raise SystemExit("FRIEND_CODE may contain only digits, spaces, and hyphens")
if len(digits) != 12:
    raise SystemExit("FRIEND_CODE must contain the 12 digits shown in the game's Pal Pad")

encoded = int(digits)
checksum = encoded >> 32
profile_id = encoded & 0x7FFFFFFF
if checksum > 0x7F or profile_id == 0:
    raise SystemExit("FRIEND_CODE is not a valid Nintendo DS Friend Code; double-check the Pal Pad")

print(profile_id)
PY
IFS= read -r WFC_PROFILE_ID < "$profile_id_file"
rm -f "$profile_id_file"
export WFC_PROFILE_ID
echo "Friend Code accepted; GameSpy profile ID $WFC_PROFILE_ID will be preserved."

# Validate HOST_IP and pin the DNS answer to it. "local" auto-detection would
# return the container's private address, which a physical DS cannot reach.
cd /opt/server/game_sync_server
HOST_IP="$HOST_IP" python3 - <<'PY'
import ipaddress
import json
import os
from pathlib import Path

raw_ip = os.environ["HOST_IP"]
try:
    address = ipaddress.IPv4Address(raw_ip)
except ipaddress.AddressValueError as exc:
    raise SystemExit(f"HOST_IP must be an IPv4 address like 192.168.1.50, got: {raw_ip}") from exc

if (
    address.is_loopback
    or address.is_unspecified
    or address.is_multicast
    or address.is_link_local
    or address.is_reserved
    or address == ipaddress.IPv4Address("255.255.255.255")
):
    raise SystemExit(f"HOST_IP must be a usable LAN unicast address, got: {address}")

config_path = Path("config.json")
config = json.loads(config_path.read_text()) if config_path.exists() else {}
config["host_name"] = str(address)
config_path.write_text(json.dumps(config, indent=2) + "\n")
print("Game Sync DNS will answer with:", address, flush=True)
PY

GS=""
DW=""

cleanup() {
  local exit_status=$?
  trap - EXIT TERM INT
  set +e

  for pid in "$DW" "$GS"; do
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null
    fi
  done

  for pid in "$DW" "$GS"; do
    if [ -n "$pid" ]; then
      wait "$pid" 2>/dev/null
    fi
  done

  exit "$exit_status"
}

# Docker signals PID 1. A signal exits this shell; the EXIT trap then
# terminates and reaps every child before the container stops.
trap cleanup EXIT
trap 'exit 0' TERM INT

python3 server.py &
GS=$!

echo "Starting Game Sync (DNS 53/udp, HTTP 80, TLS 443, GameSpy 29900/tcp)."
echo "On a new install, it stays available while you complete the first tuck-in."

player_data_ready() {
  python3 - <<'PY'
import json
import sqlite3
from pathlib import Path

save_dir = Path("/opt/server/save_data")
gscd_path = save_dir / "gscd.txt"
db_path = save_dir / "pokemon_saves.db"

if not gscd_path.is_file() or not db_path.is_file():
    raise SystemExit(1)

gscd = gscd_path.read_text().strip()
if not gscd:
    raise SystemExit(1)

try:
    with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=2) as connection:
        row = connection.execute(
            "SELECT player_data, crop_data, chest_data FROM player_saves WHERE gscd = ?",
            (gscd,),
        ).fetchone()
except (OSError, sqlite3.Error):
    raise SystemExit(1)

if not row or not all(row):
    raise SystemExit(1)

try:
    player_data = json.loads(row[0])
    json.loads(row[1])
    json.loads(row[2])
    member = player_data["member"]
except (KeyError, TypeError, json.JSONDecodeError):
    raise SystemExit(1)

# These are populated by savedata.upload, not merely account registration.
if member.get("langcode") not in {1, 2, 3, 4, 5, 7, 8} or not member.get("player_name"):
    raise SystemExit(1)
PY
}

while ! player_data_ready; do
  if ! kill -0 "$GS" 2>/dev/null; then
    set +e
    wait "$GS"
    child_status=$?
    set -e
    echo "Game Sync exited before player data became ready (status $child_status)." >&2
    exit "$child_status"
  fi
  sleep 2
done

cd /opt/server
python3 main.py &
DW=$!

echo "Player upload found; Dream World site is starting on port 8080."

# wait -n can legitimately return nonzero when a child crashes. Capture that
# status without errexit bypassing the EXIT cleanup trap.
set +e
wait -n "$GS" "$DW"
child_status=$?
set -e

echo "A server process exited (status $child_status); stopping the container." >&2
exit "$child_status"
