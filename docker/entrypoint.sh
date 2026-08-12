#!/usr/bin/env bash
# Container entrypoint: start the Game Sync server, then the Dream World site.
# HOST_IP must be the LAN IP of the machine running Docker, because the DNS
# server hands that IP to the DS. It must be reachable by the DS.
set -euo pipefail

# Fail fast: without a valid LAN IPv4, the DNS server would hand the DS the
# container's internal address and the DS could never connect.
: "${HOST_IP:?Set -e HOST_IP to your LAN IPv4, see scripts/find-lan-ip.sh}"
if ! printf '%s' "$HOST_IP" | grep -Eq '^([0-9]{1,3}\.){3}[0-9]{1,3}$'; then
  echo "HOST_IP must be an IPv4 address like 192.168.1.50, got: $HOST_IP" >&2
  exit 1
fi

cd /opt/server/game_sync_server
# Pin the DNS to the host LAN IP. config.json key host_name: "local" autodetects
# (wrong inside a container), an IP pins it. Read from the environment rather
# than interpolating into source.
HOST_IP="$HOST_IP" python3 - <<'PY'
import json, os, pathlib, ipaddress
ip = os.environ["HOST_IP"]
ipaddress.IPv4Address(ip)  # raises if invalid
p = pathlib.Path("config.json")
cfg = json.loads(p.read_text()) if p.exists() else {}
cfg["host_name"] = ip
p.write_text(json.dumps(cfg, indent=2))
print("Game Sync DNS will answer with:", ip)
PY

python3 server.py &
GS=$!

cd /opt/server
python3 main.py &
DW=$!

echo "Up: Game Sync (DNS 53/udp, HTTP 80, TLS 443, GameSpy 29900/tcp) and Dream World site (8080)."
echo "Note: if this is your first ever tuck-in, restart the container afterwards so the site picks up game sync mode."
trap 'kill $GS $DW 2>/dev/null' TERM INT
wait -n
kill $GS $DW 2>/dev/null || true
