#!/usr/bin/env bash
# Container entrypoint: start the Game Sync server, then the Dream World site.
# HOST_IP must be set to the LAN IP of the machine running Docker, because the
# DNS server hands that IP to the DS.
set -euo pipefail

cd /opt/server/game_sync_server
if [ -n "${HOST_IP:-}" ]; then
  # Tell the Game Sync DNS which IP to answer with (the Docker host's LAN IP).
  # config.json key is host_name: "local" means autodetect, an IP pins it.
  python3 - <<PY
import json, pathlib
p = pathlib.Path("config.json")
cfg = json.loads(p.read_text()) if p.exists() else {}
cfg["host_name"] = "${HOST_IP}"
p.write_text(json.dumps(cfg, indent=2))
print("Game Sync DNS will answer with:", "${HOST_IP}")
PY
else
  echo "WARNING: HOST_IP is not set. Set -e HOST_IP=<your LAN IP> or the DS will be handed the container's internal IP."
fi

python3 server.py &
GS=$!

cd /opt/server
python3 main.py &
DW=$!

echo "Game Sync server (DNS 53, HTTP 80/443) and Dream World site (8080) are up."
trap 'kill $GS $DW 2>/dev/null' TERM INT
wait -n
kill $GS $DW 2>/dev/null || true
