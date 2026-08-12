# Flash browser setup

The Dream World is a Flash game. Ruffle does not work with it yet, so you need a
real Flash Player. Pick one of these.

## Option A: Basilisk browser with the Flash plugin

Basilisk still supports old NPAPI plugins.

1. Install Basilisk: https://www.basilisk-browser.org/
2. Install archived Flash Player 32.0.0.371:
   - Windows: https://web.archive.org/web/20200609220527/https://fpdownload.macromedia.com/pub/flashplayer/installers/archive/fp_32.0.0.371_archive.zip
   - Linux: https://web.archive.org/web/20200530062840if_/https://fpdownload.adobe.com/get/flashplayer/pdc/32.0.0.371/flash_player_npapi_linux.x86_64.tar.gz
     Put `libflashplayer.so` in `/usr/lib64/mozilla/plugins` and run Basilisk with
     `MOZ_PLUGIN_PATH=/usr/lib64/mozilla/plugins ./basilisk`
3. Open http://127.0.0.1:8080/ in Basilisk.

## Option B: Standalone Flash Player

Download the standalone Adobe Flash Player 32.0.0.465 and open this URL with it:

```
http://127.0.0.1:8080/DreamWorld_data/src/swf/theme/assets/common/main.swf
```

Downloads:
- Windows: https://archive.org/download/standaloneflashplayers/fp/fp_32/32.0.0.465/flashplayer32_0r0_465_win_sa.exe
- Mac: https://archive.org/download/standaloneflashplayers/fp/fp_32/32.0.0.465/flashplayer32_0r0_465_mac_sa.dmg
- Linux: https://archive.org/download/standaloneflashplayers/fp/fp_32/32.0.0.465/flashplayer32_0r0_465_linux_sa.x86_64.tar.gz

These download links and instructions come from the upstream project readme.
