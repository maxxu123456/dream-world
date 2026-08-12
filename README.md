# Dream World

Run the Pokemon Dream World on your own computer and connect a real DS or DSi
to it. Tuck in a Pokemon from Black, White, Black 2, or White 2, then play the
Dream World in a Flash-capable browser as that save.

Everything needed to run is included in this repo (the server and all game
assets), so the image is fully self-contained.

## Run with Docker Compose (recommended)

You only need Docker.

1. Find your computer's LAN IP:

   ```
   scripts/find-lan-ip.sh
   ```

2. Put it in a `.env` file next to `docker-compose.yml` (copy `.env.example`):

   ```
   echo "HOST_IP=192.168.1.50" > .env   # use your own IP
   ```

3. Start it:

   ```
   docker compose up -d
   ```

That is it. To stop it: `docker compose down`. To watch logs: `docker compose logs -f`.

### Your progress is saved

Saves, berries, and items are stored in a named Docker volume
(`dream-world-data`) and persist across restarts and updates. `docker compose
down` keeps your progress. Only `docker compose down -v` deletes it.

## Run with a single command (alternative)

```
docker run --rm \
  -e HOST_IP=<your LAN IP> \
  -v dream-world-data:/opt/server/save_data \
  -p <your LAN IP>:53:53/udp \
  -p <your LAN IP>:80:80 \
  -p <your LAN IP>:443:443 \
  -p <your LAN IP>:29900:29900/tcp \
  -p 127.0.0.1:8080:8080 \
  ghcr.io/maxxu123456/dream-world:latest
```

The `-v dream-world-data:/opt/server/save_data` volume is what keeps your
progress. Without it, `--rm` deletes everything when the container stops. Port
29900 is the GameSpy login the DS needs. Port 8080 is only for your browser, so
it stays on localhost.

For a DS to reach the container, Docker must expose these ports on your LAN. That
works out of the box on Linux, and usually on Docker Desktop for Mac and Windows
too. If the DS cannot connect, run Docker on a Linux machine.

## Troubleshooting

- `bind: address already in use` on port 53: a local DNS resolver or VPN already
  holds it. Binding to your LAN IP (which Compose and the command above do)
  avoids most of these. To find and stop the process holding it:
  `sudo lsof -nP -iUDP:53`.
- The image is multi-arch (amd64 and arm64), so it runs natively on Apple
  Silicon. If Docker still warns about platform, run `docker compose pull` to get
  the current image.

## Connect your DS

1. Set the Primary DNS of your DS Wi-Fi connection to your computer's LAN IP
   (the same value you passed as `HOST_IP`). The connection test may fail, that
   is fine.
2. In game, open the C-Gear, pick Game Sync, and tuck in a Pokemon.
3. If this is your first ever tuck-in, restart the container once so the site
   picks up game sync mode.
4. Open http://127.0.0.1:8080/ in a Flash-capable browser and play.

Step by step: [docs/dsi-setup.md](docs/dsi-setup.md)

## Flash

Ruffle does not run the Dream World yet. Use the Basilisk browser with the
archived Flash plugin, or the standalone Flash Player.
See [docs/flash-setup.md](docs/flash-setup.md).

## Status

The DS round trip (tuck in, play, berries and items persist) works. Some parts
are still broken, including two minigames whose files are lost. See
[docs/whats-working.md](docs/whats-working.md).

## Credits

The server and the restored site come from the Dream World Revival team and are
vendored here so the image is self-contained:

- Server and assets: [minibug1021/dreamworld-reawakened](https://github.com/minibug1021/dreamworld-reawakened)
  and its submodules ([game-sync-python](https://github.com/minibug1021/game-sync-python),
  [dreamworld-assets](https://github.com/minibug1021/dreamworld-assets)), by the
  Dream World Revival Project ([@PDWRevival](https://x.com/PDWRevival))
- Game Sync method: [kuroppoi/entralinked](https://github.com/kuroppoi/entralinked) (MIT)

Fan project, not affiliated with Nintendo. See [docs/legal.md](docs/legal.md).
