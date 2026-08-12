# Connect the console

You need a DS-family system and Pokemon Black, White, Black 2, or White 2 with
the C-Gear and Game Sync unlocked.

> [!IMPORTANT]
> This wrapper has only been tested on a Nintendo DSi with Pokemon White 2,
> hosted by macOS. Other combinations are unverified.

> [!WARNING]
> Your tucked-in Pokemon can wake and return, but use a disposable Pokemon
> while testing. Newly befriended Dream World Pokemon cannot yet transfer to
> the game's Entralink or Entree Forest.

## Prepare

1. Put the console and Docker host on the same LAN.
2. Use the host's physical LAN IPv4, not a VPN or virtual-adapter address.
3. Disable guest-network client isolation.
4. Allow inbound UDP 53 and TCP 80, 443, and 29900 on the host firewall.

Original DS and DS Lite systems normally require open or WEP 2.4 GHz Wi-Fi.
DSi and 3DS systems can use supported system Internet connections for these
DSi-enhanced games.

## Configure WFC

1. Start Dream World with the desktop app or Docker Compose.
2. Open Nintendo WFC Settings from the game's save-selection screen.
3. Edit the active connection and disable automatic DNS.
4. Set Primary DNS to the IP shown in the desktop app or `HOST_IP` in `.env`.
5. Set Secondary DNS to `0.0.0.0`, then save.

Do not mix this server with Kaeru or another Secondary DNS. A failed connection
test does not always prevent the game-specific Game Sync flow. Check the live
server logs for DNS and HTTP requests.

## Tuck in

1. In White 2, open the C-Gear.
2. Press **ONLINE** on the bottom screen.
3. Press **GAME SYNC** and tuck in a disposable Pokemon.
4. Wait for `Player upload found; Dream World site is starting` in the logs.
5. Open the URL from [flash-setup.md](flash-setup.md) in the standalone Flash
   projector.

Data persists in the `dream-world-data` Docker volume. No restart is required
after the first tuck-in.
