# Dream World

Run the Pokemon Dream World on your own computer and connect a real DS, DSi,
or 3DS to it. Tuck in a Pokemon from Black, White, Black 2, or White 2, then
play the Dream World in a Flash-capable browser as that save.

Everything needed at runtime is included in the image: the server, restored
site, and pre-patched game assets. The container does not clone repositories or
download JPEXS when it starts.

## Recommended: Dream World desktop app

The desktop app is the easiest way to run Dream World. It detects your network,
starts and updates the public Docker image, shows live health and logs, and
guides you through the first tuck-in. You do not need Git, this repository, or
Docker commands after downloading it.

The app is one executable, but it still requires Docker Desktop to provide the
container runtime. Install and open
[Docker Desktop](https://www.docker.com/products/docker-desktop/) first; wait
until its whale menu says Docker is running.

### Download the app

Open the [latest GitHub Release](https://github.com/maxxu123456/dream-world/releases/latest)
and download the single binary for your computer:

- Apple Silicon Mac (M1/M2/M3/M4 or newer):
  `dream-world-gui-macos-aarch64`
- Intel Mac: `dream-world-gui-macos-x86_64`
- Windows: `dream-world-gui-windows-x86_64.exe`
- 64-bit Linux: `dream-world-gui-linux-x86_64`

#### macOS

macOS does not keep the executable permission when a binary is downloaded from
the web. Open Terminal, type `chmod +x ` (including the trailing space), drag
the downloaded `dream-world-gui-macos-*` file into the Terminal window, and
press Return. This is a one-time step; Docker commands are not required.

In Finder, **Control-click the downloaded binary > Open**, then choose **Open**
in the Gatekeeper prompt. Double-clicking works on later launches. If the file
opens in a text editor instead, open Terminal, drag the file into it, and press
Return.

#### Windows

Double-click `dream-world-gui-windows-x86_64.exe`. If Microsoft Defender
SmartScreen appears, choose **More info > Run anyway**. Keep the executable in a
normal folder such as Documents or Downloads.

#### Linux

In a terminal, change to the download folder once and run:

```sh
chmod +x dream-world-gui-linux-x86_64
./dream-world-gui-linux-x86_64
```

You can launch the executable from your file manager afterward. Docker Desktop
must be running, and your user must have permission to access Docker without
`sudo`.

### Start Dream World

1. In the game, open **Bag > Key Items > Pal Pad**, choose your trainer's
   **Friend Code**, and enter all 12 digits in the app. Save it. The app uses
   the profile ID encoded in this code so a fresh self-host does not trigger
   Nintendo WFC error 60000. Use the code from the exact game and save that
   will connect.
2. Check the detected LAN IPv4. It must belong to the physical Wi-Fi or
   Ethernet network shared with the DS, not a VPN or virtual adapter. Correct it
   if necessary, then choose **Save DNS IP**.
3. Choose **Pull / Update image** if you want to download the newest server,
   then choose **Start**. Start also downloads the public image automatically
   when it is not already installed.
4. Set the DS Primary DNS to the large saved IP shown in the app. Leave the
   Secondary DNS blank or set it to `0.0.0.0`.
5. In White 2, open the C-Gear, press **ONLINE** on the bottom screen, then
   press **GAME SYNC** and tuck in a Pokemon. Black, White, and Black 2 use the
   same C-Gear Online/Game Sync path. The DS-facing service stays healthy while
   waiting. When the live log says
   `Player upload found; Dream World site is starting`, choose
   **Open Dream World**.

The restored site still requires a Flash-capable client; modern browsers and
Ruffle do not run it correctly. Read the [Flash setup guide](docs/flash-setup.md)
before playing.

The app continues polling health and logs while it is open. Closing the app
does not stop the server; use **Stop** first when you want to stop it. Progress
is stored in the named Docker volume `dream-world-data`, shared with the manual
methods below. Reserve the selected address in your router (look for "DHCP
reservation" or "static lease") so the DS DNS setting does not become stale.

If you already run the manual Compose setup, stop it before pressing Start in
the app because both methods use the same host ports.

## Manual Docker setup

The following methods remain available for people who prefer Docker commands.

### Install Docker

- Windows or macOS: download Docker Desktop from
  https://www.docker.com/products/docker-desktop/, install it, and open it once
  so it is running (look for the whale icon).
- Linux: install Docker Engine and the Compose plugin, see
  https://docs.docker.com/engine/install/.

### Get the project

You also need git. On Windows, install it from https://git-scm.com/download/win.
On macOS, `git --version` offers to install the Command Line Tools if needed;
on Linux, install git with your distribution's package manager. Then open a
terminal (PowerShell on Windows, Terminal on macOS or Linux) and run:

```
git clone https://github.com/maxxu123456/dream-world.git
cd dream-world
```

Run every command in this guide from inside that `dream-world` folder.

### Run with Docker Compose

1. Find the LAN IPv4 address of the physical Wi-Fi or Ethernet interface on the
   same home network as the DS. It often looks like `192.168.x.x` or `10.x.x.x`.

   - Windows: run `ipconfig` and read `IPv4 Address` under the active Wi-Fi or
     Ethernet adapter. Ignore VPN, `vEthernet`, WSL, and other virtual adapters.
   - macOS: run `route -n get default` and read its `interface`, then run
     `ipconfig getifaddr INTERFACE` (for example, `ipconfig getifaddr en0`).
   - Linux: run `ip -4 route get 1.1.1.1` and read the address after `src`.

   If the command selects a VPN, disconnect it temporarily or choose the
   physical interface that shares the DS's network.

2. In the game, open **Bag > Key Items > Pal Pad** and display your trainer's
   12-digit Friend Code. It must come from the exact game and save that will
   connect.

3. Create a file named `.env` in this folder with both values, using your IP
   and Friend Code (digits only):

   ```
   HOST_IP=192.168.1.50
   FRIEND_CODE=123456789012
   ```

   Quick ways to create it (replace both examples with your own values):

   - Windows PowerShell:
     `Set-Content -Path .env -Value "HOST_IP=192.168.1.50`nFRIEND_CODE=123456789012" -Encoding ascii`
   - macOS or Linux:
     `printf 'HOST_IP=192.168.1.50\nFRIEND_CODE=123456789012\n' > .env`

   Your LAN IP can change when your router hands out a new lease. So it keeps
   working, reserve a fixed IP for this computer in your router settings (look
   for "DHCP reservation" or "static lease"). If the IP ever does change,
   update `.env` and your DS's DNS setting to match, then run
   `docker compose up -d` again.

4. Start the container:

   ```
   docker compose up -d
   ```

5. Check it:

   ```
   docker compose ps
   docker compose logs -f
   ```

   On a brand-new install, Game Sync becomes healthy and stays available for
   the DS while the website waits for player data. Complete the first tuck-in;
   the website then starts automatically on port 8080. No container restart is
   needed.

To stop it, run `docker compose down`. To start it again, run
`docker compose up -d`.

#### Your progress is saved

Game Sync accounts, saves, berries, and items are stored in the named Docker
volume `dream-world-data`. Both Compose and the single-command method below use
that exact volume. `docker compose down` keeps it; `docker compose down -v`
deletes it permanently.

If you used an older Compose file, your data may be in the old project-scoped
volume `dream-world_dream-world-data`. With the Dream World container stopped,
copy it once before starting this version:

```
docker volume inspect dream-world_dream-world-data
docker volume create dream-world-data
docker run --rm --volume dream-world_dream-world-data:/from:ro --volume dream-world-data:/to alpine sh -c "cp -a /from/. /to/"
```

Skip that migration if `docker volume inspect` says the old volume does not
exist.

### Run with a single command

This path needs only Docker, not git or the project files. Replace the example
IP with the LAN IP shared with your DS.

macOS or Linux:

```sh
HOST_IP=192.168.1.50
FRIEND_CODE=123456789012
docker run --rm \
  --env "HOST_IP=${HOST_IP}" \
  --env "FRIEND_CODE=${FRIEND_CODE}" \
  --volume dream-world-data:/opt/server/save_data \
  --publish "${HOST_IP}:53:53/udp" \
  --publish "${HOST_IP}:80:80" \
  --publish "${HOST_IP}:443:443" \
  --publish "${HOST_IP}:29900:29900/tcp" \
  --publish 127.0.0.1:8080:8080 \
  ghcr.io/maxxu123456/dream-world:latest
```

Windows PowerShell:

```powershell
$HostIp = "192.168.1.50"
$FriendCode = "123456789012"
docker run --rm `
  --env "HOST_IP=$HostIp" `
  --env "FRIEND_CODE=$FriendCode" `
  --volume dream-world-data:/opt/server/save_data `
  --publish "${HostIp}:53:53/udp" `
  --publish "${HostIp}:80:80" `
  --publish "${HostIp}:443:443" `
  --publish "${HostIp}:29900:29900/tcp" `
  --publish "127.0.0.1:8080:8080" `
  ghcr.io/maxxu123456/dream-world:latest
```

`--rm` removes only the stopped container. The `dream-world-data` volume keeps
your progress. Press Ctrl+C to stop this foreground command.

## Network requirements

- The DS and Docker host must be on the same reachable LAN. Disable wireless
  client/AP isolation; guest networks commonly block devices from each other.
- Allow inbound UDP 53 and TCP 80, 443, and 29900 in the host firewall for the
  LAN/private network. Port 8080 remains bound to host localhost only.
- Original DS and DS Lite hardware require a compatible 2.4 GHz legacy network,
  normally open or WEP. DSi and 3DS systems running these DSi-enhanced games can
  use their system Internet settings with newer Wi-Fi security. If association
  fails, check that the router offers 2.4 GHz and legacy Nintendo DS support.
- The DNS IP saved in the app (or `HOST_IP` in `.env` for Compose), the
  published-port bindings, and the DS Primary DNS setting must all be the same
  address.

Docker Engine on Linux and current Docker Desktop releases publish ports bound
to the selected LAN address. VPNs, endpoint-security tools, and host firewalls
can still block traffic from a physical DS.

## Connect your DS

1. Start the container and confirm Game Sync is healthy.
2. Set the Primary DNS of the console's game connection to the same LAN IP used
   as `HOST_IP`. Leave Secondary DNS blank or `0.0.0.0`. A failed connection
   test does not necessarily prevent Game Sync; continue and check the logs.
3. In the game, open the C-Gear, press **ONLINE** on the bottom screen, then
   press **GAME SYNC** and tuck in a Pokemon.
4. Wait for `Player upload found; Dream World site is starting` in the logs.
5. Open http://127.0.0.1:8080/ in a Flash-capable client.

Step by step: [docs/dsi-setup.md](docs/dsi-setup.md).

## Troubleshooting

- Website unavailable before the first tuck-in: expected. The DS-facing Game
  Sync service starts first; the website starts after usable save data arrives.
- `bind: address already in use`: another service has one of the required host
  ports. For UDP 53, common causes are a local DNS resolver, VPN, WARP,
  Tailscale, or an ad blocker. Binding to the LAN IP avoids a resolver that uses
  only `127.0.0.1:53`, but not a process bound to all interfaces.
  - Windows PowerShell as administrator:
    `Get-Process -Id (Get-NetUDPEndpoint -LocalPort 53).OwningProcess`
  - macOS or Linux: `sudo lsof -nP -iUDP:53`
- Container is unhealthy: read the app's live logs, or run
  `docker compose logs -f` for a manual install. Health requires a DNS answer
  containing the selected host IP plus listeners on TCP 80, 443, and 29900.
- DS cannot connect: recheck the physical interface/IP, firewall, 2.4 GHz
  compatibility, and client isolation. Temporarily disconnect VPN software.
- Error 60000: stop the container, verify that `FRIEND_CODE` (or the code saved
  in the app) exactly matches **Pal Pad > your trainer's Friend Code** for this
  game/save, then start or restart it. The server repairs that save's GameSpy
  profile ID before replying to the next login.
- Platform warning on Apple Silicon: choose **Pull / Update image** in the app,
  or run `docker compose pull`. The published image supports amd64 and arm64.

## Flash

Ruffle does not run the Dream World correctly yet. Use Basilisk with the
archived Flash plug-in, or preferably the standalone Flash projector. Flash is
unsupported and unsafe for general browsing; use it only with this local
server. See [docs/flash-setup.md](docs/flash-setup.md).

## Status

The DS round trip—tuck in, play, and persist berries/items—works. Some upstream
features remain incomplete, including two minigames whose files are lost. See
[docs/whats-working.md](docs/whats-working.md).

## Credits

The server and restored site come from the Dream World Revival team and are
vendored here so the runtime image is self-contained:

- Server and assets: [minibug1021/dreamworld-reawakened](https://github.com/minibug1021/dreamworld-reawakened)
  and its submodules ([game-sync-python](https://github.com/minibug1021/game-sync-python),
  [dreamworld-assets](https://github.com/minibug1021/dreamworld-assets)), by the
  Dream World Revival Project ([@PDWRevival](https://x.com/PDWRevival))
- Game Sync method: [kuroppoi/entralinked](https://github.com/kuroppoi/entralinked) (MIT)

Fan project, not affiliated with Nintendo. See [docs/legal.md](docs/legal.md).
