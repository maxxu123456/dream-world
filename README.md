# Dream World

Run the Pokemon Dream World on your own computer and connect a real DS or DSi
to it. Tuck in a Pokemon from Black, White, Black 2, or White 2, then play the
Dream World in a Flash-capable browser as that save.

Everything needed to run is included in this repo (the server and all game
assets), so the image is fully self-contained.

## Run

You only need Docker.

```
docker run --rm \
  -e HOST_IP=<your LAN IP> \
  --mount type=volume,src=dream-world-data,dst=/opt/server/save_data \
  -p 53:53/udp -p 80:80 -p 443:443 -p 29900:29900/tcp \
  -p 127.0.0.1:8080:8080 \
  ghcr.io/maxxu123456/dream-world:latest
```

- `HOST_IP` must be your computer's address on your Wi-Fi network. Get it with
  `scripts/find-lan-ip.sh`, or from your system network settings.
- The named volume keeps your saves, berries, and items between runs.
- Port 29900 is the GameSpy login step the DS needs, so keep it.
- Port 8080 is only for your browser, so it stays on localhost.

For a DS to reach the container, Docker must be able to expose these ports on
your LAN. That works out of the box on Linux. On Docker Desktop for Mac or
Windows, published ports are reachable from your LAN in most setups; if the DS
cannot connect, run Docker on a Linux machine or use host networking.

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
