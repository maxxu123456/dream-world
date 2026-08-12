# Dream World

Self-host the Pokemon Dream World and connect a physical DS-family system. The
Docker image includes the Game Sync server, restored website, and patched Flash
assets. It does not download source or tools at runtime.

> [!IMPORTANT]
> This wrapper has only been tested with a Nintendo DSi, macOS, and Pokemon
> White 2. Other supported systems, operating systems, and Generation 5 games
> are expected to work but have not been verified by this project.

> [!WARNING]
> This restoration is unfinished. Your tucked-in Pokemon can wake and return,
> but newly befriended Dream World Pokemon cannot yet transfer to the Entralink
> or Entree Forest. Use a disposable Pokemon while testing.

## Recommended: desktop app

The desktop app finds your LAN address, controls Docker, shows health and logs,
and keeps the command line optional. It is one executable, but
[Docker Desktop](https://www.docker.com/products/docker-desktop/) must be
installed, open, and running.

### Download

Open the [latest release](https://github.com/maxxu123456/dream-world/releases/latest)
and download one file:

- Apple Silicon Mac: `dream-world-gui-macos-aarch64`
- Intel Mac: `dream-world-gui-macos-x86_64`
- Windows x86-64: `dream-world-gui-windows-x86_64.exe`
- Linux x86-64: `dream-world-gui-linux-x86_64`

On macOS or Linux, make the download executable:

```sh
chmod +x dream-world-gui-*
```

On macOS, use **Control-click > Open**, then **Open** for the first launch. On
Windows, use **More info > Run anyway** if SmartScreen appears. Linux users
must be able to run Docker without `sudo`, then run
`./dream-world-gui-linux-x86_64`.

### Start and connect

1. Check **Bag > Key Items > Pal Pad** in the game.
   - No Friend Code: leave **This save already has a Friend Code** off.
   - Existing 12-digit code: enable the option and enter the code from this
     exact save. This prevents or repairs WFC error 60000.
2. Confirm the detected LAN IPv4 and select **Save DNS IP**. Ignore VPN and
   virtual-adapter addresses.
3. Select **Start**. The public image downloads automatically if needed.
4. On the console, set Primary DNS to the saved IP and Secondary DNS to
   `0.0.0.0`.
5. In White 2, open the C-Gear, press **ONLINE** on the bottom screen, press
   **GAME SYNC**, and tuck in a disposable Pokemon.
6. Wait for `Player upload found; Dream World site is starting` in the logs.
7. Copy the Flash URL shown by the app. In the standalone Flash projector,
   choose **File > Open**, paste the URL, and select **Open**.

Modern browsers and Ruffle do not run Dream World correctly. Follow the
[Flash projector guide](docs/flash-setup.md).

Closing the desktop app does not stop Docker. Select **Stop** first when you
want to stop the server. Progress is stored in the `dream-world-data` Docker
volume. Reserve the selected LAN address in your router using a DHCP
reservation or static lease.

## Manual Docker setup

The desktop app is recommended. These methods remain available for Docker
users.

### Install Docker

Install Docker Desktop on Windows or macOS. On Linux, install Docker Engine and
the Compose plugin.

### Docker Compose

Install Git, then run:

```sh
git clone https://github.com/maxxu123456/dream-world.git
cd dream-world
```

Find the LAN IPv4 of the physical adapter shared with the console:

- Windows: run `ipconfig` and use the active Wi-Fi or Ethernet IPv4 address.
- macOS: run `route -n get default`, note the interface, then run
  `ipconfig getifaddr INTERFACE`.
- Linux: run `ip -4 route get 1.1.1.1` and use the address after `src`.

Create `.env` with your address. Leave `FRIEND_CODE` empty if the Pal Pad does
not have one yet:

```text
HOST_IP=192.168.1.50
FRIEND_CODE=
```

Windows PowerShell can create the file with:

```powershell
Set-Content -Path .env -Value "HOST_IP=192.168.1.50`nFRIEND_CODE=" -Encoding ascii
```

Start and inspect the service:

```sh
docker compose up -d
docker compose ps
docker compose logs -f
```

Use `docker compose down` to stop it. Do not add `-v` unless you intend to
delete all progress. If the host address changes, update `.env`, update the
console DNS, and run `docker compose up -d` again. A router DHCP reservation
prevents this problem.

### Single Docker command

This method does not require Git or repository files. Replace the example IP.

macOS or Linux:

```sh
HOST_IP=192.168.1.50
FRIEND_CODE=
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
$FriendCode = ""
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

Press Ctrl+C to stop. `--rm` removes the container, not the named data volume.

## Network requirements

- The Docker host and console must be on the same reachable LAN.
- Do not use a guest network with client or AP isolation.
- Allow inbound UDP 53 and TCP 80, 443, and 29900 on the private LAN.
- Port 8080 is available only on the Docker host at `127.0.0.1`.
- Original DS and DS Lite systems need compatible 2.4 GHz legacy Wi-Fi. DSi
  and 3DS systems can use the system connections supported by Gen 5 games.
- The app or `.env` IP, Docker port bindings, and console Primary DNS must
  match. Leave Secondary DNS empty or set it to `0.0.0.0`.

## Troubleshooting

- Website not ready before tuck-in: expected. Game Sync starts first.
- Error 60000: enter the existing Friend Code from this exact save, restart the
  managed container, and try again.
- Error 52210: the WFC connection test failed before Friend Code login. Recheck
  DNS, firewall, LAN isolation, and VPN or DNS-filter software.
- Address already in use: another program owns UDP 53 or TCP 80, 443, or
  29900. DNS resolvers, VPNs, and ad blockers often use port 53.
- Unhealthy container: inspect the desktop app logs or run
  `docker compose logs -f`.

See [DS setup](docs/dsi-setup.md), [Flash setup](docs/flash-setup.md), and
[feature status](docs/whats-working.md).

## Credits and legal

The vendored server and assets come from
[dreamworld-reawakened](https://github.com/minibug1021/dreamworld-reawakened)
and its game-sync-python and dreamworld-assets submodules. The Game Sync method
comes from [Entralinked](https://github.com/kuroppoi/entralinked).

This is an unofficial fan project. See [docs/legal.md](docs/legal.md).
