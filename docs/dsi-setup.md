# Connect a DS, DSi, or 3DS

You need a DS-family console and Pokemon Black, White, Black 2, or White 2 with
the C-Gear and Game Sync unlocked.

## Prepare the network

1. Put the console and Docker host on the same LAN.
2. Find the LAN IPv4 of the host's physical adapter:

   - Windows: use `ipconfig`; choose the active Wi-Fi/Ethernet adapter, not a
     VPN, WSL, or `vEthernet` adapter.
   - macOS: use `route -n get default` to find the interface, then
     `ipconfig getifaddr INTERFACE`.
   - Linux: use `ip -4 route get 1.1.1.1` and read the address after `src`.

3. Disable guest-network/client isolation. Allow inbound UDP 53 and TCP 80,
   443, and 29900 through the host firewall on the private/LAN network.

Original DS and DS Lite hardware require a compatible 2.4 GHz legacy network,
normally open or WEP. DSi and 3DS systems can use the system Internet settings
supported by these DSi-enhanced games. If the console cannot even join Wi-Fi,
check the router's 2.4 GHz and legacy Nintendo DS settings first.

## Start Game Sync

Follow the Compose instructions in the main [README](../README.md), putting the
host LAN IP in `.env`, then run:

```
docker compose up -d
docker compose ps
docker compose logs -f
```

On a new volume, the container intentionally starts Game Sync before the Dream
World website. It remains running and healthy while waiting for the first save
upload; port 8080 becomes available automatically after tuck-in.

## Configure the console

1. Open Nintendo WFC Settings from the game's save-selection screen. On DSi or
   3DS, use the matching connection configured in System Settings when
   appropriate for the console.
2. Edit the connection and disable automatic DNS.
3. Set Primary DNS to the same LAN IP used for `HOST_IP`.
4. Leave Secondary DNS blank or set it to `0.0.0.0`, then save.

The connection test can fail even when the game-specific flow works. If it
does, continue once and watch `docker compose logs -f` for DNS/HTTP activity.

## Tuck in and play

1. In the game, open the C-Gear, choose Game Sync, and tuck in a Pokemon. Save
   when asked.
2. Wait for this container message:

   ```text
   Player upload found; Dream World site is starting on port 8080.
   ```

3. Open http://127.0.0.1:8080/ in a supported Flash client; see
   [flash-setup.md](flash-setup.md).

No container restart is required. Accounts, the selected Game Sync ID, saves,
berries, and items persist in the `dream-world-data` Docker volume.

For protocol-specific troubleshooting, the server uses the same DNS/WFC method
as Entralinked: https://github.com/kuroppoi/entralinked/wiki/Troubleshooting
