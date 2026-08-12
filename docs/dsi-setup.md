# Connect your DS or DSi

You need a DS, DS Lite, DSi, DSi XL, or 3DS, and a copy of Pokemon Black,
White, Black 2, or White 2. Reach the point in the game where the C-Gear and
Game Sync are available.

1. Find your computer's LAN IP:

   ```
   scripts/find-lan-ip.sh
   ```

2. Start the container with that IP as `HOST_IP` (see the main README for the
   full command). Keep it running.

3. On the DS, open the game and go to the Nintendo WFC Settings on the save
   select screen (or System Settings > Internet on a DSi). Edit your connection
   and set the Primary DNS to your computer's LAN IP. Leave the Secondary DNS as
   zeros. Save.

   Make sure the DS and your computer are on the same Wi-Fi network. If the
   connection test fails, ignore it.

4. In the game, open the C-Gear, choose Game Sync, and tuck in a Pokemon. Save
   when asked.

5. If this is your first ever tuck-in, restart the container once so the Dream
   World site switches into game sync mode.

6. Open http://127.0.0.1:8080/ in a Flash-capable browser (see
   [flash-setup.md](flash-setup.md)) and play as that save.

Notes:
- The container runs both servers, so the Game Sync side is ready as soon as the
  container is up.
- Troubleshooting DNS and ports uses the same method as Entralinked, so its guide
  applies: https://github.com/kuroppoi/entralinked/wiki/Troubleshooting
