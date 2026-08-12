#!/usr/bin/env bash
# Print this machine's LAN IP — the address you type as the Primary DNS on your DS.
set -euo pipefail

ip=""
for iface in en0 en1 en2 en3; do
  if candidate=$(ipconfig getifaddr "$iface" 2>/dev/null); then
    ip="$candidate"; iface_used="$iface"; break
  fi
done

if [ -z "$ip" ]; then
  echo "Could not determine a LAN IP via ipconfig. Try: ifconfig | grep 'inet '" >&2
  exit 1
fi

echo "LAN IP : $ip   (interface $iface_used)"
echo
echo "On your DS/DSi Wi-Fi connection settings, set:"
echo "  Primary DNS   = $ip"
echo "  Secondary DNS = 0.0.0.0   (leave blank / zeros)"
echo
echo "Make sure this machine and the DS are on the SAME Wi-Fi network,"
echo "and that the Game Sync server is running so its DNS answers."
