# Connect your DS or DSi

You need a DS, DS Lite, DSi, DSi XL, or 3DS, and a copy of Pokemon Black,
White, Black 2, or White 2. Reach the point in the game where the C-Gear and
Game Sync are available.

1. Start the Game Sync server on your computer:

   ```
   scripts/run-gamesync.sh
   ```

   It prints a DNS address. Write it down.

2. On the DS, open the game and go to the Nintendo WFC Settings on the save
   select screen (or System Settings > Internet on a DSi). Edit your connection
   and set the Primary DNS to the address from step 1. Leave the Secondary DNS
   as zeros. Save.

   Make sure the DS and your computer are on the same Wi-Fi network. If the
   connection test fails, ignore it.

3. In the game, open the C-Gear, choose Game Sync, and tuck in a Pokemon. Save
   when asked.

4. Start the Dream World website (see the main README) and play as that save.

Notes:
- The Game Sync server must run before you tuck in.
- On Linux and macOS it needs to run with sudo because it uses port 53.
- Troubleshooting DNS and ports: this uses the same method as Entralinked, so
  its guide applies: https://github.com/kuroppoi/entralinked/wiki/Troubleshooting
