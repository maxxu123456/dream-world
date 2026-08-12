# Dream World

Run the Pokemon Dream World on your own computer and connect a real DS or DSi
to it. Tuck in a Pokemon from Black, White, Black 2, or White 2, then play the
Dream World in a Flash-capable browser as that save.

This repo is a setup wrapper and Docker image around the community revival
server, [minibug1021/dreamworld-reawakened](https://github.com/minibug1021/dreamworld-reawakened),
which is where all the server code and restored site files come from.

## Run with Docker

The image is published to a private package. The simplest fix is to make it
public once: open https://github.com/users/maxxu123456/packages/container/dream-world/settings
and set the package to public. After that anyone (including you) can pull it with
no login.

To keep it private instead, sign in with a token that has `read:packages`:

```
gh auth refresh -s read:packages
gh auth token | docker login ghcr.io -u maxxu123456 --password-stdin
```

Then run it. Replace `<your LAN IP>` with your computer's address on your Wi-Fi
network (`scripts/find-lan-ip.sh` prints it on a Mac):

```
docker run --rm \
  -e HOST_IP=<your LAN IP> \
  --mount type=volume,src=dream-world-data,dst=/opt/server/save_data \
  -p 53:53/udp -p 80:80 -p 443:443 -p 29900:29900/tcp \
  -p 127.0.0.1:8080:8080 \
  ghcr.io/maxxu123456/dream-world:latest
```

The named volume keeps your saves, berries, and items between runs. Port 29900 is
the GameSpy login step the DS needs, so do not drop it. Port 8080 is only for your
own browser, so it stays on localhost.

Docker on a Mac cannot always let a DS on the Wi-Fi reach these ports. If Game Sync
will not connect, run without Docker instead (below), which is the reliable path
for a real DS.

## Run without Docker

Needs git, Python 3, and Java.

```
scripts/setup.sh            # clone the server and install packages
scripts/run-gamesync.sh     # start this first, it prints the DNS for your DS
scripts/run-dreamworld.sh   # the Dream World site on http://127.0.0.1:8080/
```

## Connect your DS

1. On the DS, set the Primary DNS of your Wi-Fi connection to your computer's
   LAN IP. The connection test may fail, that is fine.
2. In game, open the C-Gear, pick Game Sync, and tuck in a Pokemon.
3. Open http://127.0.0.1:8080/ in a Flash-capable browser and play.

Step-by-step: [docs/dsi-setup.md](docs/dsi-setup.md)

## Flash

Ruffle does not run the Dream World yet. Use the Basilisk browser with the
archived Flash plugin, or the standalone Flash Player.
See [docs/flash-setup.md](docs/flash-setup.md).

## Status

The DS round trip (tuck in, play, berries and items persist) works. Some parts
are still broken upstream, including two minigames whose files are lost. See
[docs/whats-working.md](docs/whats-working.md).

## Credits

- Server and restored site: [minibug1021/dreamworld-reawakened](https://github.com/minibug1021/dreamworld-reawakened)
  and submodules ([game-sync-python](https://github.com/minibug1021/game-sync-python),
  [dreamworld-assets](https://github.com/minibug1021/dreamworld-assets)) by the
  Dream World Revival team ([@PDWRevival](https://x.com/PDWRevival))
- Game Sync method: [kuroppoi/entralinked](https://github.com/kuroppoi/entralinked) (MIT)
- Asset research: [magical/pdw](https://github.com/magical/pdw) and the
  archive.org uploaders who preserved the original files

Fan project, not affiliated with Nintendo. Personal use only, see
[docs/legal.md](docs/legal.md).
