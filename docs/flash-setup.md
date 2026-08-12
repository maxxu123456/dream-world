# Flash client setup

The Dream World is a Flash game. Ruffle does not currently run it correctly, so
use a real Flash Player only after completing a Game Sync tuck-in.

Flash reached end of life and receives no security fixes. Use it only with the
local URL in this guide. Do not browse arbitrary websites or open untrusted SWF
files; a dedicated local user account or offline virtual machine is safer.

## Recommended: standalone Flash projector

Download the standalone Adobe Flash Player 32.0.0.465 for your platform:

- Windows: https://archive.org/download/standaloneflashplayers/fp/fp_32/32.0.0.465/flashplayer32_0r0_465_win_sa.exe
- macOS: https://archive.org/download/standaloneflashplayers/fp/fp_32/32.0.0.465/flashplayer32_0r0_465_mac_sa.dmg
- Linux: https://archive.org/download/standaloneflashplayers/fp/fp_32/32.0.0.465/flashplayer32_0r0_465_linux_sa.x86_64.tar.gz

On Apple Silicon, the archived Intel projector may require Rosetta 2. After
verifying the download, use Finder's **Control-click > Open** if macOS blocks
the first launch; do not disable Gatekeeper globally.

Open this URL in the projector:

```text
http://127.0.0.1:8080/DreamWorld_data/src/swf/theme/assets/common/main.swf
```

## Alternative: Basilisk and the NPAPI plug-in

This is mainly practical on Windows or Linux. Install Basilisk from
https://www.basilisk-browser.org/ and the archived NPAPI Flash Player
32.0.0.371:

- Windows: https://web.archive.org/web/20200609220527/https://fpdownload.macromedia.com/pub/flashplayer/installers/archive/fp_32.0.0.371_archive.zip
- Linux: https://web.archive.org/web/20200530062840if_/https://fpdownload.adobe.com/get/flashplayer/pdc/32.0.0.371/flash_player_npapi_linux.x86_64.tar.gz

For Linux, place `libflashplayer.so` in a private plug-in directory and launch
Basilisk with that directory in `MOZ_PLUGIN_PATH`; for example:

```sh
mkdir -p "$HOME/.local/lib/mozilla/plugins"
cp libflashplayer.so "$HOME/.local/lib/mozilla/plugins/"
MOZ_PLUGIN_PATH="$HOME/.local/lib/mozilla/plugins" ./basilisk
```

Then open http://127.0.0.1:8080/. Avoid installing the obsolete plug-in
system-wide.

These archived versions and URLs follow the upstream project's instructions;
they are not included in the Docker image.
