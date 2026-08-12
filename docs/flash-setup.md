# Flash projector setup

Dream World requires the standalone Adobe Flash projector. Modern browsers and
Ruffle do not run it correctly.

> [!IMPORTANT]
> This setup has only been tested with the macOS projector while using a DSi
> and Pokemon White 2.

Flash is obsolete and receives no security fixes. Use it only with this local
server. Do not open untrusted SWF files or browse arbitrary sites with it.

## Download

Use the standalone Flash Player 32.0.0.465 for your platform:

- [Windows projector](https://archive.org/download/standaloneflashplayers/fp/fp_32/32.0.0.465/flashplayer32_0r0_465_win_sa.exe)
- [macOS projector](https://archive.org/download/standaloneflashplayers/fp/fp_32/32.0.0.465/flashplayer32_0r0_465_mac_sa.dmg)
- [Linux projector](https://archive.org/download/standaloneflashplayers/fp/fp_32/32.0.0.465/flashplayer32_0r0_465_linux_sa.x86_64.tar.gz)

On Apple Silicon, install Rosetta 2 if macOS requests it. Use
**Control-click > Open** for the first launch if Gatekeeper blocks the app.

## Run Dream World

Complete Game Sync first and wait until the desktop app reports that the player
upload was found. In Flash Player, choose **File > Open**, paste this URL, and
select **Open**:

```text
http://127.0.0.1:8080/src/swf/theme/assets/common/dream-world-projector-v25.swf
```

Do not paste the URL into Chrome, Safari, Edge, or Firefox. If it stays at 0%,
select **Pull / Update image** in the desktop app, restart the container, and
copy the URL again.
